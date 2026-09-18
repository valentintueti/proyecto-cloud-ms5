FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY ingesta-ms1/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common.py .
COPY ingesta-ms1/src/ ./ingesta-ms1/src/

ENTRYPOINT ["python", "ingesta-ms1/src/main.py"]
