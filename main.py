from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI()

app = FastAPI(
    title="CV Extraction Pipeline",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.post("/upload/")
async def upload_cv(file: UploadFile = File(...)):
     return JSONResponse({
        "filename": file.filename,
        "content_type": file.content_type
    })