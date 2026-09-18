FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY ingesta-ms2/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common.py .
COPY ingesta-ms2/src/ ./ingesta-ms2/src/
ENTRYPOINT ["python", "ingesta-ms2/src/main.py"]
