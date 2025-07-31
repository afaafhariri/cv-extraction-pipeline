import os
import json
import base64
import tempfile
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from google.cloud import storage
from motor.motor_asyncio import AsyncIOMotorClient
import pdfplumber
import docx
import phonenumbers
from dotenv import load_dotenv

load_dotenv()

gcs = storage.Client()
mongo = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = mongo.get_default_database()

ses = boto3.client(
    "ses",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

def extract_contact_info(path: str):
    import re
    EMAIL = re.compile(r"[A-Za-z0-9.+_-]+@[A-Za-z0-9._-]+\.[A-Za-z]+")
    NAME  = re.compile(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)")
    text = ""
    if path.lower().endswith(".pdf"):
        with pdfplumber.open(path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    else:
        doc = docx.Document(path)
        text = "\n".join(p.text for p in doc.paragraphs)
    email = (EMAIL.search(text).group(0) if EMAIL.search(text) else None)
    phone = None
    for m in phonenumbers.PhoneNumberMatcher(text, "US"):
        phone = phonenumbers.format_number(m.number, phonenumbers.PhoneNumberFormat.E164)
        break
    name = (NAME.search(text).group(0) if NAME.search(text) else None)
    return {"name": name, "email": email, "phone": phone}


def send_confirmation(email: str, name: str, app_id: str):
    message = Mail(
        from_email=os.getenv("FROM_EMAIL"),
        to_emails=email,
        subject="Your Application Received",
        html_content=f"Hi {name},<br>Your application ID is <strong>{app_id}</strong>."
    )
    sg.send(message)

def process_cv(event, context):
    payload = json.loads(base64.b64decode(event['data']).decode("utf-8"))
    bucket_name = payload["bucket"]
    filename = payload["filename"]
    if not bucket_name or not filename:
        print("Invalid event data:", payload)
        return
    bucket = gcs.bucket(bucket_name)
    blob = bucket.blob(filename)
    with tempfile.NamedTemporaryFile(suffix=filename, delete=False) as tmp:
        blob.download_to_filename(tmp.name)
        local_path = tmp.name

    info = extract_contact_info(local_path)

    app_id = "APP-" + uuid.uuid4().hex[:8].upper()
    record = {
        "applicationId": app_id,
        **info,
        "cvUrl": f"https://storage.googleapis.com/{bucket_name}/{filename}",
        "submittedAt": datetime.utcnow()
    }
    db.applications.insert_one(record)
    print(f"Processed CV: {filename}, Application ID: {app_id}")    
    if info.get("email"):
        send_confirmation(info["email"], info.get("name", "Applicant"), app_id)


# # processor/main.py

# import os
# import json
# import base64
# import tempfile
# import uuid
# from datetime import datetime

# import boto3
# from botocore.exceptions import ClientError
# from google.cloud import storage
# from motor.motor_asyncio import AsyncIOMotorClient
# import pdfplumber
# import docx
# import phonenumbers
# from dotenv import load_dotenv

# load_dotenv()

# # ─── Clients ──────────────────────────────────────────────────────────────────

# # Google Cloud Storage
# gcs = storage.Client()

# # MongoDB Atlas
# mongo = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
# db = mongo.get_default_database()

# # AWS SES
# ses = boto3.client(
#     "ses",
#     aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
#     aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
#     region_name=os.getenv("AWS_REGION")
# )


# def send_confirmation(email: str, name: str, app_id: str):
#     """
#     Send a confirmation email via AWS SES.
#     """
#     SENDER = os.getenv("FROM_EMAIL")
#     RECEIVER = email
#     SUBJECT = "Your Application Received"
#     CHARSET = "UTF-8"

#     # Plain-text and HTML bodies
#     BODY_TEXT = f"Hi {name},\nYour application ID is {app_id}."
#     BODY_HTML = f"""
#     <html>
#       <body>
#         <p>Hi {name},</p>
#         <p>Your application ID is <strong>{app_id}</strong>.</p>
#       </body>
#     </html>
#     """

#     try:
#         response = ses.send_email(
#             Source=SENDER,
#             Destination={"ToAddresses": [RECEIVER]},
#             Message={
#                 "Subject": {"Data": SUBJECT, "Charset": CHARSET},
#                 "Body": {
#                     "Text": {"Data": BODY_TEXT, "Charset": CHARSET},
#                     "Html": {"Data": BODY_HTML, "Charset": CHARSET},
#                 },
#             },
#         )
#     except ClientError as e:
#         # Log the error but don’t fail the whole function
#         print(f"SES send_email error: {e.response['Error']['Message']}")
#     else:
#         print(f"SES email sent, Message ID: {response['MessageId']}")


# # ─── Cloud Function Entry Point ──────────────────────────────────────────────

# def process_cv(event, context):
#     """
#     Triggered by Pub/Sub on CV upload.
#     Downloads the file, parses it, stores to MongoDB, and emails via SES.
#     """
#     # decode Pub/Sub message
#     payload = json.loads(base64.b64decode(event["data"]).decode("utf-8"))
#     bucket_name = payload.get("bucket")
#     filename = payload.get("filename")
#     if not bucket_name or not filename:
#         print("Invalid Pub/Sub payload:", payload)
#         return

#     # download from GCS
#     bucket = gcs.bucket(bucket_name)
#     blob = bucket.blob(filename)
#     with tempfile.NamedTemporaryFile(suffix=filename, delete=False) as tmp:
#         blob.download_to_filename(tmp.name)
#         local_path = tmp.name

#     # parse contact info
#     info = extract_contact_info(local_path)

#     # generate application ID
#     app_id = "APP-" + uuid.uuid4().hex[:8].upper()
#     record = {
#         "applicationId": app_id,
#         **info,
#         "cvUrl": f"https://storage.googleapis.com/{bucket_name}/{filename}",
#         "submittedAt": datetime.utcnow(),
#     }

#     # store in MongoDB
#     db.applications.insert_one(record)
#     print(f"Stored record for {filename} with ID {app_id}")

#     # send confirmation email if we have one
#     if info.get("email"):
#         send_confirmation(info["email"], info.get("name", "Applicant"), app_id)
#     else:
#         print("No email found in CV; skipping confirmation.")