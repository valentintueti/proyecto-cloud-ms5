FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY ingesta-ms3/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common.py .
COPY ingesta-ms3/src/ ./ingesta-ms3/src/
ENTRYPOINT ["python", "ingesta-ms3/src/main.py"]
