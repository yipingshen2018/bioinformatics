from fastapi import FastAPI, UploadFile, File
from celery.result import AsyncResult
from tasks import run_prediction  # 你在 tasks.py 里定义的 Celery 任务

import shutil, os
import uuid

app = FastAPI()

@app.post("/submit")
async def submit_fasta(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    input_path = f"storage/inputs/{job_id}.fasta"
    os.makedirs("storage/inputs", exist_ok=True)
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    task = run_prediction.delay(input_path, job_id)

    return {
        "task_id": task.id,
        "job_id": job_id
    }

@app.get("/status/{job_id}")
def get_status(job_id: str):
    done_file = os.path.join("storage/outputs", job_id, "ExampleProtein.done.txt")

    if os.path.exists(done_file):
        return {"status": "COMPLETED"}
    elif os.path.exists(output_dir):
        return {"status": "RUNNING"}
    else:
        return {"status": "PENDING"}


@app.get("/result/{job_id}")
def get_result(job_id: str):
    output_path = f"storage/outputs/{job_id}/ranked_0.pdb"
    if os.path.exists(output_path):
        return {"pdb_path": output_path}
    else:
        return {"error": "Result not ready yet."}


@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    return await submit_fasta(file)

@app.get("/status/{job_id}")
def get_status(job_id: str):
    output_dir = f"storage/outputs/{job_id}/"
    done_file = os.path.join(output_dir, "ExampleProtein.done.txt")
    if os.path.exists(done_file):
        return {"status": "COMPLETED"}
    if os.path.exists(output_dir):
        return {"status": "RUNNING"}
    return {"status": "PENDING"}