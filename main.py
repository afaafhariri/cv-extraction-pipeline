from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import os

app = FastAPI()

# @app.on_event("startup")
# async def list_routes():
#     print("Available routes:")
#     for route in app.router.routes:
#         print(route.path, route.methods)

@app.get("/")
async def root():
    return {"status": "ok"}

# app.post("/upload")
# async def upload_cv(file: UploadFile = File(...)):
#      return JSONResponse({
#         "filename": file.filename,
#         "content_type": file.content_type
#     })

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