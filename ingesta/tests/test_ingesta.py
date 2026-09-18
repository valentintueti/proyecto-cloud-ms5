import argparse
import csv
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import common


def load(name, source):
    spec = importlib.util.spec_from_file_location(name, ROOT / source / "src" / "extractor.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ms2 = load("ms2_extractor", "ingesta-ms2")
ms3 = load("ms3_extractor", "ingesta-ms3")


class CsvTests(unittest.TestCase):
    def test_full_stream_preserves_precision_and_csv_escaping(self):
        with tempfile.TemporaryDirectory() as directory:
            export = common.write_csv(directory, "tarjetas", ["id", "saldo", "texto"],
                                      ((i, Decimal("123456789.12"), 'Lima, "Perú"\nCentro') for i in range(20001)))
            with export.path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(export.rows, 20001)
            self.assertEqual(rows[-1]["id"], "20000")
            self.assertEqual(rows[0]["saldo"], "123456789.12")
            self.assertEqual(rows[0]["texto"], 'Lima, "Perú"\nCentro')

    def test_empty_table_has_header(self):
        with tempfile.TemporaryDirectory() as directory:
            export = common.write_csv(directory, "viajes", ["id", "estado"], [])
            self.assertEqual(export.rows, 0)
            self.assertEqual(export.path.read_text(), "id,estado\n")

    def test_mongo_keeps_empty_services_repeated_stops_and_orphans(self):
        services = [{"_id": "s1", "ruta_id": "r1", "fecha": "2026-09-16", "paraderos": [
            {"paradero_id": "p1", "orden": 2}, {"paradero_id": "p1", "orden": 3},
            {"paradero_id": "missing", "orden": 4}]},
            {"_id": "s2", "ruta_id": "missing", "paraderos": []}]
        with tempfile.TemporaryDirectory() as directory:
            warnings = []
            exports = ms2.flatten_services(Path(directory), iter(services),
                {"r1": {"nombre": "Ruta, Norte", "sentido": "IDA"}}, {"p1": {"nombre": "Central"}}, warnings)
            self.assertEqual([e.rows for e in exports], [2, 3])
            with exports[0].path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(list(rows[0]), ms2.SERVICIOS_COLUMNS)
            self.assertEqual(rows[0]["ruta_nombre"], "Ruta, Norte")
            self.assertEqual(rows[1]["ruta_nombre"], "")
            with exports[1].path.open(encoding="utf-8", newline="") as stream:
                stops = list(csv.DictReader(stream))
            self.assertEqual(list(stops[0]), ms2.PARADEROS_COLUMNS)
            self.assertEqual([p["orden"] for p in stops], ["2", "3", "4"])
            self.assertEqual(stops[-1]["paradero_nombre"], "")
            self.assertEqual(len(warnings), 2)

    def test_missing_pago_is_distinct_from_database_failure(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        self.assertIsNone(ms3.find_table(cursor, "pago"))
        cursor.execute.side_effect = ConnectionError("db down")
        with self.assertRaises(ConnectionError):
            ms3.find_table(cursor, "pago")


class PipelineTests(unittest.TestCase):
    def args(self, directory, local=True):
        return argparse.Namespace(run_id="test", output_dir=directory, local_only=local)

    def test_failed_preflight_never_extracts(self):
        extractor = MagicMock()
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()), \
             patch.object(common, "aws_preflight", side_effect=common.ConfigurationError("Sin token")):
            self.assertEqual(common.execute("ms1", extractor, self.args(directory, False)), 1)
            extractor.assert_not_called()
            report = json.loads((Path(directory) / "ms1/test/manifest.json").read_text())
            self.assertEqual(report["status"], "failed")

    def test_local_only_never_contacts_aws_and_warns_empty(self):
        def extract(directory, warnings):
            return [common.write_csv(directory, "viajes", ["id"], [])]
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()), patch.object(common, "aws_preflight") as aws:
            self.assertEqual(common.execute("ms3", extract, self.args(directory)), 0)
            aws.assert_not_called()
            report = json.loads((Path(directory) / "ms3/test/manifest.json").read_text())
            self.assertIsNone(report["exports"][0]["s3_uri"])
            self.assertEqual(report["exports"][0]["rows"], 0)
            self.assertTrue(report["warnings"])

    def test_partial_upload_is_failed_with_no_completion_marker(self):
        def extract(directory, warnings):
            return [common.write_csv(directory, name, ["id"], [(1,)]) for name in ("pasajeros", "tarjetas")]
        s3 = MagicMock()
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()), \
             patch.object(common, "aws_preflight", return_value=(s3, "test-bucket", "123456789012")), \
             patch.object(common, "upload", side_effect=["s3://test-bucket/raw/pasajeros/test.csv", ConnectionError("secret")]):
            self.assertEqual(common.execute("ms1", extract, self.args(directory, False)), 1)
            report = json.loads((Path(directory) / "ms1/test/manifest.json").read_text())
            self.assertEqual(report["status"], "failed")
            self.assertIsNotNone(report["exports"][0]["s3_uri"])
            self.assertIsNone(report["exports"][1]["s3_uri"])
            self.assertNotIn("secret", report["error"])
            s3.put_object.assert_not_called()

    def test_upload_uses_owner_guard_and_checks_size(self):
        with tempfile.TemporaryDirectory() as directory:
            export = common.write_csv(directory, "viajes", ["id"], [(1,)])
            s3 = MagicMock()
            s3.head_object.return_value = {"ContentLength": export.path.stat().st_size}
            uri = common.upload(s3, "personal-test", "123456789012", export, "run1")
            self.assertEqual(uri, "s3://personal-test/raw/viajes/run_id=run1/viajes.csv")
            self.assertEqual(s3.upload_file.call_args.kwargs["ExtraArgs"]["ExpectedBucketOwner"], "123456789012")
            s3.head_object.return_value = {"ContentLength": 0}
            with self.assertRaises(RuntimeError):
                common.upload(s3, "personal-test", "123456789012", export, "run1")


class AwsTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"S3_BUCKET": "personal-test", "AWS_EXPECTED_ACCOUNT_ID": "123456789012", "AWS_REGION": "us-east-1"}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.session = MagicMock()
        self.session.get_credentials.return_value.get_frozen_credentials.return_value = argparse.Namespace(access_key="test", secret_key="test", token="token")
        self.sts, self.s3 = MagicMock(), MagicMock()
        self.sts.get_caller_identity.return_value = {"Account": "123456789012"}
        self.session.client.side_effect = lambda service, **kwargs: self.sts if service == "sts" else self.s3

    def test_correct_account_and_bucket(self):
        with patch("boto3.Session", return_value=self.session):
            self.assertEqual(common.aws_preflight()[1:], ("personal-test", "123456789012"))
        self.s3.head_bucket.assert_called_once_with(Bucket="personal-test", ExpectedBucketOwner="123456789012")

    def test_other_account_is_rejected_before_s3(self):
        self.sts.get_caller_identity.return_value = {"Account": "999999999999"}
        with patch("boto3.Session", return_value=self.session), self.assertRaises(common.ConfigurationError):
            common.aws_preflight()
        self.s3.head_bucket.assert_not_called()

    def test_missing_session_token_is_rejected_before_sts(self):
        self.session.get_credentials.return_value.get_frozen_credentials.return_value.token = None
        with patch("boto3.Session", return_value=self.session), self.assertRaises(common.ConfigurationError):
            common.aws_preflight()
        self.sts.get_caller_identity.assert_not_called()

    def test_403_does_not_claim_bucket_absent(self):
        from botocore.exceptions import ClientError
        self.s3.head_bucket.side_effect = ClientError({"Error": {"Code": "403"}}, "HeadBucket")
        with patch("boto3.Session", return_value=self.session), self.assertRaisesRegex(common.ConfigurationError, "no confirma"):
            common.aws_preflight()


if __name__ == "__main__":
    unittest.main()
