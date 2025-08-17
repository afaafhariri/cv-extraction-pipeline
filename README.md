# CV Extraction Pipeline

An **event-driven** system built on AWS for extracting applicant information from CVs, authenticating uploads via Google OAuth, storing files in **AWS S3**, processing asynchronously via **AWS SNS & Lambda**, persisting parsed data in **MongoDB Atlas**, and sending confirmation emails through **AWS SES**.

---

## Architecture Overview

```text
Client Browser
    ↓ (HTTPS + OAuth)
API Gateway → Uploader Lambda
    ↓ (stores file)
    → AWS S3 (CV Bucket)
    ↓ (S3 Put Event or SNS)
SNS Topic → Processor Lambda
    → parses CV → MongoDB Atlas
    → sends email via AWS SES
```

- **Uploader Lambda** (FastAPI + Mangum) handles Google OAuth login, receives CV uploads, writes to S3, and publishes a message to an SNS topic.
- **Processor Lambda** triggers on SNS events (or S3 notifications), downloads the CV from S3, extracts name/email/phone, stores a document in MongoDB Atlas, and sends a confirmation email via SES.

---

## Technologies

- **Uploader**: Python, FastAPI, Mangum, Authlib (Google OAuth), AWS S3, AWS SNS, AWS Lambda, API Gateway
- **Processor**: Python, AWS Lambda, pdfplumber, python-docx, phonenumbers, Motor (MongoDB), Boto3 (AWS SES & S3)
- **Storage**: AWS S3
- **Messaging**: AWS SNS
- **Compute**: AWS Lambda behind API Gateway
- **Database**: MongoDB Atlas
- **Email**: AWS Simple Email Service (SES)

---

## Repository Structure

```text
cv-pipeline/
├── uploader/          # HTTP API service
│   ├── main.py        # FastAPI app (Google OAuth, S3 upload, SNS publish)
│   ├── requirements.txt
│   └── .env           # GOOGLE_OAUTH_CLIENT_ID, SECRET_KEY, AWS creds + config
└── processor/         # Event-driven processor
    ├── main.py        # Lambda handler: parse CV, store, email
    ├── requirements.txt
    └── .env           # MONGODB_URI, AWS creds + SES config
```

---

## Prerequisites

- **AWS Account** with:
  - **IAM User/Role** granting permissions to S3, SNS, Lambda, and SES (`AmazonS3FullAccess`, `AmazonSNSFullAccess`, `AWSLambda_FullAccess`, `AmazonSESFullAccess`).
  - **S3 Bucket** to store uploaded CVs.
  - **SNS Topic** for CV processing events.
  - **SES**: Verified sending identity (email or domain).
  - **API Gateway** and **Lambda** permissions.
- **MongoDB Atlas** cluster URI.
- **Google OAuth credentials**: Client ID & Client Secret for OAuth login.
- **Python 3.9+**, `pip`, and **Git**.

---

## Getting Started

### 1. Clone the Repository

### 2. Create & Activate Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Configure Environment Variables

Copy the example files into each service folder and fill in your values:

- **uploader/.env**:

  ```dotenv
  GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
  GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
  GOOGLE_OAUTH_REDIRECT_URI=https://your-api-gateway-domain/auth
  SECRET_KEY=random-32-byte-string

  AWS_ACCESS_KEY_ID=...
  AWS_SECRET_ACCESS_KEY=...
  AWS_REGION=us-east-1
  S3_BUCKET_NAME=your-cv-bucket
  SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:cv-uploads
  ```

- **processor/.env**:

  ```dotenv
  MONGODB_URI=mongodb+srv://<user>:<pass>@cluster0.mongodb.net/dbname?retryWrites=true&w=majority

  AWS_ACCESS_KEY_ID=...
  AWS_SECRET_ACCESS_KEY=...
  AWS_REGION=us-east-1
  FROM_EMAIL=verified@your-domain.com
  ```

### 4. Install Dependencies

```bash
pip install -r uploader/requirements.txt
pip install -r processor/requirements.txt
```

---

## Running Locally

### Uploader Service

```bash
cd uploader
uvicorn main:app --reload
```

- Visit `http://localhost:8000/login` to authenticate via Google.
- After login, use Swagger UI at `http://localhost:8000/docs` to POST CVs to `/upload`.

### Processor Service

- You can simulate SNS events locally by invoking the `process_cv` handler with a test JSON payload.

---

## Deployment

### Deploying with AWS SAM or Serverless Framework

Configure your `template.yaml` or `serverless.yml` for two Lambda functions:

1. **Uploader Lambda**:

   - Handler: `uploader.main.app` via Mangum adapter.
   - Trigger: API Gateway (HTTP).
   - Environment: `uploader/.env`.

2. **Processor Lambda**:

   - Handler: `processor.main.process_cv`.
   - Trigger: SNS Topic ARN.
   - Environment: `processor/.env`.

**Example (Serverless Framework)**:

```yaml
service: cv-pipeline
provider:
  name: aws
  runtime: python3.9
  region: ${env:AWS_REGION}
functions:
  uploader:
    handler: uploader.main.app
    events:
      - httpApi: '*'
    environment:
      GOOGLE_OAUTH_CLIENT_ID: ${env:GOOGLE_OAUTH_CLIENT_ID}
      ...
  processor:
    handler: processor.main.process_cv
    events:
      - sns: ${env:SNS_TOPIC_ARN}
    environment:
      MONGODB_URI: ${env:MONGODB_URI}
      ...
```

Deploy with:

```bash
serverless deploy
```

---

## Contributing

Contributions are welcome! Please open issues or pull requests for feature requests, bug fixes, or documentation improvements.
