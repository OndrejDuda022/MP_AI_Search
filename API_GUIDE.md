# AI Search API - Quick Start Guide

## Installation

### Windows
```powershell
# Install dependencies
pip install -r requirements.txt

# Start the API server
.\start_api.ps1
```

### Linux / WSL
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies  
pip install -r requirements.txt

# Make startup script executable
chmod +x start_api.sh

# Start the API server
./start_api.sh
```

## API Endpoints

Base URL: `http://localhost:8000`

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

#### 1. Search
`POST /api/search`

Search with optional base64-encoded documents.

**Request Body:**
```json
{
  "query": "What is machine learning?",
  "documents": [
    {
      "filename": "document.txt",
      "content": "base64encodedcontent..."
    }
  ],
  "use_local_db": true,
  "search_mode": "hybrid",
  "internal_mode": false,
  "language": "auto"
}
```

**Response:**
```json
{
  "success": true,
  "query": "What is machine learning?",
  "summary": "AI-generated summary...",
  "key_points": ["Point 1", "Point 2"],
  "sources": [
    {
      "url": "https://example.com",
      "title": "Document Title",
      "type": "web",
      "length": 1500
    }
  ],
  "confidence": "high"
}
```

#### 2. Health Check
`GET /api/health`

Check API and service health.

**Response:**
```json
{
  "status": "healthy",
  "database_status": {
    "count": 42,
    "collection": "knowledge_base"
  },
  "selenium_status": "running"
}
```

#### 3. Database Statistics
`GET /api/db/stats`

Get local database statistics.

**Response:**
```json
{
  "document_count": 42,
  "collection_name": "knowledge_base",
  "embedding_model": "paraphrase-multilingual-mpnet-base-v2"
}
```

#### 4. Upload Documents
`POST /api/db/upload`

Add base64-encoded documents to the local database.

**Request Body:**
```json
{
  "documents": [
    {
      "filename": "mydoc.txt",
      "content": "base64encodedcontent..."
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "added_count": 1,
  "message": "Successfully added 1/1 documents"
}
```

## Example Usage

### Using curl

```bash
# Health check
curl http://localhost:8000/api/health

# Simple search
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Python?",
    "search_mode": "web",
    "internal_mode": false
  }'

# Search with base64 document
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Summarize this document",
    "documents": [
      {
        "filename": "test.txt",
        "content": "'$(echo "This is my test document content" | base64)'"
      }
    ]
  }'
```

### Using Python

```python
import requests
import base64

# Search with document
with open("mydocument.txt", "rb") as f:
    content = base64.b64encode(f.read()).decode()

response = requests.post(
    "http://localhost:8000/api/search",
    json={
        "query": "Analyze this document",
        "documents": [
            {
                "filename": "mydocument.txt",
                "content": content
            }
        ],
        "search_mode": "hybrid"
    }
)

result = response.json()
print(result["summary"])
```

## Configuration

Set these environment variables in your `.env` file:

```bash
# AI Configuration
AI_API_KEY=your_api_key
AI_URL=https://api.your-ai-service.com

# Google Search
GOOGLE_API_KEY=your_google_api_key
SEARCH_ENGINE_ID=your_search_engine_id

# Search Settings
USE_LOCAL_DB=True
SEARCH_MODE=hybrid  # hybrid/local/web
INTERNAL_MODE=False
LANGUAGE=auto  # auto/en/cs/sk
MINIMAL_SOURCES=3
MAXIMAL_SOURCES=5
MIN_RELEVANCE=0.6
MAX_USER_QUERY_LENGTH=300

# Selenium Settings
CONTAIN_SELENIUM=False
ALLOW_LOCAL_SELENIUM=True
FORCE_SELENIUM=False
```

## Docker Support

The API works with Docker on both Windows and Linux for Selenium:

```bash
# API will automatically start Selenium container when needed
# Or start manually:
docker run -d --name selenium-chrome \
  -p 4444:4444 \
  --shm-size="2g" \
  selenium/standalone-chrome:latest
```

## CLI Mode

The original CLI interface still works:

```bash
python src/main.py
```
