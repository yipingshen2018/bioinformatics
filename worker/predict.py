from celery import Celery
import subprocess, os
from tasks import celery  # 引入 tasks.py 中已注册的 Celery 实例

celery = Celery('predict', broker=os.getenv("CELERY_BROKER_URL"), backend=os.getenv("CELERY_RESULT_BACKEND"))
@celery.task
def predict_structure(job_id: str, fasta_path: str):
    output_dir = f"storage/outputs/{job_id}_out"
    os.makedirs(output_dir, exist_ok=True)
    subprocess.run(["colabfold_batch", fasta_path, output_dir], check=True)
    return f"{job_id}_out"
