# S3 Service (MinIO) — Upload/Download Documents

This service provides a **single pair of APIs** for document upload and download, backed by **MinIO/S3**.

- **Upload:** `POST /s3/upload`
- **Download:** `GET  /s3/download`

It supports two functional types via headers:

- `type: user` → bucket: **uploads**
- `type: recruitment` → bucket: **recruitment** (with extra `post_id` header)

---

## 1) Requirements

- Python 3.12+
- MinIO (or any S3 compatible storage)
- MongoDB (audit logs) *(best-effort; upload/download will still work even if Mongo is down)*
- Redis *(optional; used only for health ping)*
- rsyslog *(optional; logs can be shipped to rsyslog)*

---

## 2) Environment variables

Create a `.env` file in the project root (same directory as `main.py`).

Example:

```env
SERVICE_NAME=s3-service
ENVIRONMENT=local

# rsyslog (optional)
RSYSLOG_DESTINATIONS=localhost:514

# Redis (optional)
REDIS_NODES=localhost:6379
REDIS_USERNAME=
REDIS_PASSWORD=
REDIS_SSL=false

# Mongo (audit)
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_USERNAME=
MONGO_PASSWORD=
MONGO_AUTH_DB=admin
MONGO_DB_NAME=audit_db
MONGO_AUDIT_COLLECTION=s3_audit_logs

# MinIO / S3
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_REGION=us-east-1
S3_SECURE=false
S3_ADDRESSING_STYLE=path

# Buckets
USER_BUCKET=uploads
RECRUITMENT_BUCKET=recruitment
```

> Important:
> - MinIO **requires** access key & secret (use `minioadmin/minioadmin` if you did not set custom ones).
> - Keep `.env` clean: any separator lines must start with `#` (comment), otherwise dotenv can fail to parse.

---

## 3) Install and Run

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn main:app --host 0.0.0.0 --port 9090 --reload
```

Swagger:
- http://localhost:9090/docs

Health:
- http://localhost:9090/health

---

## 4) API — Upload

### Endpoint
`POST /s3/upload`

### Headers (required)
For **user** uploads:
- `type: user`
- `applicant_id: <decrypted int>`
- `type_of_document: <string>` (example: `name_change`, `board_certificate`, `id_card`, etc.)

For **recruitment** uploads:
- `type: recruitment`
- `post_id: <string>` (required)
- `applicant_id: <decrypted int>`
- `type_of_document: <string>`

### Body (multipart/form-data)
- `file`: the uploaded file

### Key format (IMPORTANT)

Bucket selection:
- `type=user` → bucket **uploads**
- `type=recruitment` → bucket **recruitment**

Object key structure:

**User**
```
{applicant_id}/{rule.folder}/{filename}
```

**Recruitment**
```
recruitment/{post_id}/{applicant_id}/{rule.folder}/{filename}
```

> Bucket name is **NOT** part of the key.

### Versioning / overwrite behavior (no timestamp)

- The service stores the uploaded file using the **original filename** (no timestamp).
- If a file with the same name already exists at the same key:
  - the existing file is archived as `name_1.ext`, then `name_2.ext`, etc.
  - and the new file is uploaded as the original `name.ext`

Example (user):
- Upload `name_change.pdf` first time:
  - `uploads` bucket
  - key: `1111/name_change/name_change.pdf`
- Upload again:
  - old becomes: `1111/name_change/name_change_1.pdf`
  - new saved as: `1111/name_change/name_change.pdf`

---

## 5) API — Download

### Endpoint
`GET /s3/download`

### Headers (same as upload)

User download:
- `type: user`
- `applicant_id: <decrypted int>`
- `type_of_document: <string>`

Recruitment download:
- `type: recruitment`
- `post_id: <string>`
- `applicant_id: <decrypted int>`
- `type_of_document: <string>`

### Query param (optional)
- `filename=<exact_filename>`  
  If omitted, the service downloads the **latest** file under that folder (based on LastModified).

Examples:
- Download latest:
  - `GET /s3/download`
- Download a specific archived file:
  - `GET /s3/download?filename=name_change_1.pdf`

---

## 6) cURL examples

### Upload (user)
```bash
curl -X POST "http://localhost:9090/s3/upload" \
  -H "type: user" \
  -H "applicant_id: 1111" \
  -H "type_of_document: name_change" \
  -F "file=@name_change.pdf;type=application/pdf"
```

### Upload (recruitment)
```bash
curl -X POST "http://localhost:9090/s3/upload" \
  -H "type: recruitment" \
  -H "post_id: POST123" \
  -H "applicant_id: 1111" \
  -H "type_of_document: name_change" \
  -F "file=@name_change.pdf;type=application/pdf"
```

### Download latest (user)
```bash
curl -L "http://localhost:9090/s3/download" \
  -H "type: user" \
  -H "applicant_id: 1111" \
  -H "type_of_document: name_change" \
  -o name_change.pdf
```

### Download specific file (user)
```bash
curl -L "http://localhost:9090/s3/download?filename=name_change_1.pdf" \
  -H "type: user" \
  -H "applicant_id: 1111" \
  -H "type_of_document: name_change" \
  -o name_change_1.pdf
```

### Download latest (recruitment)
```bash
curl -L "http://localhost:9090/s3/download" \
  -H "type: recruitment" \
  -H "post_id: POST123" \
  -H "applicant_id: 1111" \
  -H "type_of_document: name_change" \
  -o name_change.pdf
```

---

## 7) Document rules (validation)

Rules are defined in `document_services/doc_rules.py`.

By default, the service validates:
- size range (KB)
- allowed extensions
- allowed content-types (MIME)

Example entries (typical):
- `name_change`: PDF only, 50–300 KB
- `board_certificate`: PDF only, 50–300 KB
- `id_card`: JPG/PNG/PDF, 20–500 KB

If a `type_of_document` is not found in rules, a default rule is used.

---

## 8) Notes

- **Do not trust `applicant_id` from a browser client** if exposed publicly.
  Recommended integration: Keycloak SPI or backend service calls this API.
- If you later want service-to-service authentication, add a shared secret header (recommended).
