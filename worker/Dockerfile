FROM python:3.10-slim
FROM ghcr.io/sokrypton/colabfold:1.5.5-cuda12.2.2
WORKDIR /app
COPY ./tasks.py /app
COPY ./predict.py /app
RUN pip install celery redis
CMD ["celery", "-A", "predict", "worker", "--loglevel=info"]
