---
# 🖼️ Image Format Converter API

A production-ready Image Format Converter built with **FastAPI**.

This service allows you to upload an image and convert it to another supported format via a REST API.
---

## 🚀 Features

- Convert images between multiple formats
- File size validation
- File type validation
- Rate limiting
- Versioned API (`/api/v1`)
- Health check endpoint
- Environment-based configuration (`.env`)
- Structured logging
- Production-ready architecture

---

## 📦 Supported Formats

- jpeg
- jpg
- png
- webp
- bmp
- tiff
- gif

---

## 🛠 Installation

### 1️⃣ Clone the repository

```bash
git clone <your-repo-url>
cd image-processor
```

### 2️⃣ Create virtual environment

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙️ Environment Configuration

Create a `.env` file in the root directory:

```env
MAX_FILE_SIZE=5242880
RATE_LIMIT=10/minute
ENVIRONMENT=development
LOG_LEVEL=INFO
```

You can adjust:

- `MAX_FILE_SIZE` (in bytes)
- `RATE_LIMIT`
- `LOG_LEVEL`

---

## ▶️ Running the Application

### Development Mode

```bash
uvicorn app.main:app --reload
```

API will run at:

```
http://127.0.0.1:8000
```

Swagger documentation:

```
http://127.0.0.1:8000/docs
```

---

## 📡 API Endpoints

### 🔄 Convert Image

**POST** `/api/v1/convert`

#### Query Parameters:

- `target_format` (required)

#### Form Data:

- `file` (image file)

#### Example using curl:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/convert?target_format=png" \
  -F "file=@sample.jpg" \
  --output converted.png
```

---

### ❤️ Health Check

**GET** `/health`

Returns:

```json
{
  "status": "healthy",
  "service": "image-processor",
  "version": "1.0.0"
}
```

---

## 🛡 Validation & Protection

The API includes:

- File size limits (configured via `.env`)
- Allowed file type validation
- Pixel dimension validation
- Rate limiting per IP
- Streaming responses (no disk storage)
- Structured logging

---

## 📂 Project Structure

```
app/
 ├── api/v1/
 ├── controllers/
 ├── services/
 ├── utils/
 ├── core/
 └── exceptions/
```

This follows a modular, scalable architecture.

---

## 📊 Logging

Logs are written to:

```
app.log
```

Logs include:

- Incoming requests
- Conversion activity
- Validation failures
- Errors

---

## 🏭 Production Run

For production:

```bash
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4
```

---

## 📌 Notes

- Do not commit `.env`
- Do not commit `venv`
- Adjust file size limit carefully for memory safety
- For heavy workloads, consider adding Redis + background workers

---

## 📄 License

MIT License

---
