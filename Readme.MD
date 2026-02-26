# 🚀 Image Processor API

A production-grade, fully instrumented image processing API built with **FastAPI**, **Pillow**, and **PostgreSQL (Supabase)**.

This API provides advanced image transformation, optimization, analysis, and conversion tools with full usage tracking and analytics.

---

## 🏗 Tech Stack

- FastAPI
- SQLAlchemy (Async)
- PostgreSQL (Supabase)
- Alembic (Migrations)
- Pillow
- Scour (SVG Optimization)
- SlowAPI (Rate Limiting)

---

# 📦 Features

## ✅ Image Converter

Convert images between formats:

**Supported formats:**

- JPEG
- PNG
- WEBP
- BMP
- TIFF
- GIF
- ICO

### Endpoint

```
POST /api/v1/convert
```

### Query Params

- `target_format`

---

## 📊 Image Analyzer

Analyze image properties including:

- Width / Height
- Aspect Ratio
- Format
- File size
- Brightness score
- Contrast score
- Color palette
- Metadata
- Smart optimization recommendations

### Endpoint

```
POST /api/v1/analyze
```

---

## ✂️ Image Cropper

Crop image using coordinates.

### Endpoint

```
POST /api/v1/images/crop
```

### Query Params

- `left`
- `top`
- `right`
- `bottom`

---

## 📏 Image Resizer

Resize images with optional aspect ratio preservation.

### Endpoint

```
POST /api/v1/images/resize
```

### Query Params

- `width`
- `height`
- `keep_aspect` (default: true)

---

## 🔄 Image → Base64

Convert image file into Base64 string.

### Endpoint

```
POST /api/v1/images/to-base64
```

---

## 🔁 Base64 → Image

Convert Base64 string back to downloadable image.

### Endpoint

```
POST /api/v1/images/from-base64
```

---

## 🎯 Social Media Optimizers

### Twitter

```
POST /api/v1/optimize/twitter
```

### WhatsApp

```
POST /api/v1/optimize/whatsapp
```

### Instagram

```
POST /api/v1/optimize/instagram
```

### YouTube Thumbnail

```
POST /api/v1/optimize/youtube-thumbnail
```

### Web Optimization (WEBP output)

```
POST /api/v1/optimize/web
```

### SEO Responsive Package (ZIP output)

```
POST /api/v1/optimize/seo-responsive
```

### Custom Optimization

```
POST /api/v1/optimize/custom
```

Query Params:

- `target_kb`
- `quality`
- `resize_percent`

---

## 🖼 Favicon Generator

Generates a complete favicon package (ZIP):

- favicon.ico
- apple-touch-icon
- android icons
- manifest
- Multiple sizes

### Endpoint

```
POST /api/v1/images/favicon
```

Query Params:

- `extension`
- `background`
- `padding`

---

## 🧹 SVG Optimizer

Optimizes SVG files using Scour.

- Removes metadata
- Strips comments
- Shortens IDs
- Reduces precision

### Endpoint

```
POST /api/v1/optimize-svg
```

---

# 📈 Built-In Usage Tracking

Every endpoint logs:

- Action type
- Endpoint
- HTTP method
- IP address
- User agent
- File size
- Original format
- Target format
- Width / Height
- Success / Failure
- Status code
- Error type
- Error message
- Processing time (ms)
- Timestamp

Stored in PostgreSQL (`usage_logs` table).

---

# 🛡 Security Features

- File extension validation
- File size limits
- Image pixel limits
- Decompression bomb protection
- SVG safety validation
- Rate limiting
- EXIF auto-orientation
- Metadata stripping

---

# ⚙️ Environment Variables

Create `.env`:

```
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname?ssl=require
RATE_LIMIT=10/minute
MAX_FILE_SIZE=5242880
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

# 🗄 Database Setup

## Run Migrations

```
alembic upgrade head
```

## Add New Enum Values

When adding new tools:

```
alembic revision -m "add new action types"
```

Inside migration:

```
op.execute("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'new_value';")
```

Then:

```
alembic upgrade head
```

---

# 🚀 Running the Server

```
uvicorn app.main:app --reload
```

---

# 📊 Monitoring & Observability

Because all actions are logged, you can:

- Calculate tool popularity
- Track failure rates
- Monitor processing performance
- Detect abuse patterns
- Analyze user agents
- Track daily usage growth

---

# 🧠 Architecture Philosophy

- Thin routers
- Controllers handle logging + orchestration
- Services handle business logic
- Async SQLAlchemy
- Clean separation of concerns
- Production-ready logging

---

# 📌 Example Request

```
curl -X POST \
  -F "file=@image.jpg" \
  "http://localhost:8000/api/v1/convert?target_format=webp"
```

---

# 📦 Response Types

Depending on endpoint:

- StreamingResponse (image/jpeg, image/webp, etc.)
- JSON (analyzer, base64 tools)
- ZIP archive (favicon, SEO responsive)

---

# 🏁 Status

This API is:

- Production-ready
- Fully instrumented
- Extensible
- Secure
- Scalable

---

# 👨‍💻 Author

Built with ❤️ using FastAPI + Supabase.
