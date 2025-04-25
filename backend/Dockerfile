FROM python:3.10-slim
WORKDIR /app
COPY ./app /app
RUN pip install fastapi celery[redis] uvicorn python-multipart paramiko scp

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
