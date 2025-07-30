from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
from google.cloud import storage, pubsub_v1


load_dotenv()
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "ok"}

@app.post("/upload")
async def upload_cv(file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)
    file_location = f"uploads/{file.filename}"
    contents = await file.read()
    with open(file_location, "wb") as f:
        f.write(contents)
        print("File uploaded successfully")
        print(f"File saved to {file_location}")
        print(f"File name: {file.filename}")
    return JSONResponse({
        "filename": file.filename,
        "content_type": file.content_type,
        "saved_to": file_location
    })