import os
import json
from fastapi import FastAPI, Request, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth, OAuthError
from google.cloud import storage, pubsub_v1
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user
bucket_name = os.getenv("GCS_BUCKET_NAME")
storage_client = storage.Client()
bucket = storage_client.bucket(bucket_name)

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(storage_client.project, os.getenv("PUBSUB_TOPIC"))

@app.get("/")
async def root(request: Request):
    return {"status": "ok", "logged_in_as": request.session.get("user")}

@app.get("/login")
async def login(request: Request):
    redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth")
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = await oauth.google.parse_id_token(request, token)
    except OAuthError:
        raise HTTPException(status_code=400, detail="OAuth authentication failed")
    request.session["user"] = {"email": user_info["email"], "name": user_info.get("name")}
    return RedirectResponse(url="/docs")

@app.post("/upload")
async def upload_cv(
    request: Request,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    # 1) Upload file to GCS
    contents = await file.read()
    blob = bucket.blob(file.filename)
    try:
        blob.upload_from_string(contents, content_type=file.content_type)
    except Exception as e:
        raise HTTPException(500, f"GCS upload error: {e}")

    # 2) Publish event
    msg = json.dumps({
        "bucket": bucket_name,
        "filename": file.filename,
        "content_type": file.content_type
    }).encode("utf-8")
    try:
        publisher.publish(topic_path, msg)
    except Exception as e:
        raise HTTPException(500, f"Pub/Sub publish error: {e}")

    return JSONResponse({"status": "uploaded", "filename": file.filename, "by": user})

@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return {"status": "logged out"}