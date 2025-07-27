from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI()

app = FastAPI(
    title="CV Extraction Pipeline",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

