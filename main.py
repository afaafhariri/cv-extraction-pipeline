from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI()

@app.on_event("startup")
async def list_routes():
    print("Available routes:")
    for route in app.router.routes:
        print(route.path, route.methods)

@app.get("/")
async def root():
    return {"status": "ok"}

app.post("/upload")
async def upload_cv(file: UploadFile = File(...)):
     return JSONResponse({
        "filename": file.filename,
        "content_type": file.content_type
    })