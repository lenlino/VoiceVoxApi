FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
ENV USAGE_DB=/data/usage.db PYTHONUNBUFFERED=1
RUN useradd -r -u 10001 app && mkdir /data && chown app:app /data
USER app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
