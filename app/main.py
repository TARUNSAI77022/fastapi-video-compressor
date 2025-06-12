from fastapi import FastAPI, UploadFile, File, HTTPException
from app.tasks import compress_and_upload
from app.utils import get_temp_path
import uuid
import shutil
import os

app = FastAPI()

# Max allowed file size: 500 MB
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB

@app.post("/compress")
async def compress_file(file: UploadFile = File(...)):
    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    ext = file.filename.split('.')[-1].lower()
    uid = str(uuid.uuid4())

    supported_video = ['mp4', 'mov', 'avi', 'mkv']
    supported_image = ['jpg', 'jpeg', 'png']

    if ext in supported_video:
        output_ext = "mkv"
    elif ext in supported_image:
        output_ext = "webp"
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    input_path = get_temp_path(f"{uid}_input.{ext}")
    output_path = get_temp_path(f"{uid}_compressed.{output_ext}")

    os.makedirs(os.path.dirname(input_path), exist_ok=True)

    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    original_filename = file.filename
    clean_filename = original_filename.rsplit(".", 1)[0]
    s3_key = f"compressed/{uid}_{clean_filename}.{output_ext}"

    task = compress_and_upload.delay(input_path, output_path, s3_key, original_filename)

    return {
        "message": "Compression started",
        "s3_key": s3_key,
        "original_filename": original_filename,
        "task_id": task.id
    }