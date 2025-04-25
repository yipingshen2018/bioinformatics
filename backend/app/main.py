from fastapi import FastAPI, UploadFile, File
from celery.result import AsyncResult
from tasks import send_to_runpod
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
    pdb_path = send_to_runpod(input_path)
    return {"pdb_path": pdb_path}

@app.get("/status/{task_id}")
def get_status(task_id: str):
    result = AsyncResult(task_id)
    return {"status": result.status}

@app.get("/result/{task_id}")
def get_result(task_id: str):
    result = AsyncResult(task_id)
    if result.status == 'SUCCESS':
        return {"pdb_path": f"/storage/outputs/{result.result}/ranked_0.pdb"}
    return {"status": result.status}

@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    filepath = f"storage/inputs/{file.filename}"
    with open(filepath, "wb") as f:
        f.write(await file.read())

    result = send_to_runpod(filepath)
    return {"result": result}