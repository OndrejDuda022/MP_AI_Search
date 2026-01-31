# AI Search Engine

An intelligent search system that combines Google Custom Search API with advanced AI processing to deliver precise, context-aware answers to user queries. The system automatically generates optimized search queries, scrapes relevant content, and synthesizes comprehensive responses with source citations.

## Possible Future Improvements

- [ ] Implement search retry mechanism for irrelevant results
- [ ] Add caching layer for frequently accessed pages
- [ ] Support for more document formats (DOCX, XLSX, etc.)
- [ ] Add web interface

## Features

### **Local Vector Database (ChromaDB)**
- **Multilingual semantic search** using `paraphrase-multilingual-mpnet-base-v2` embedding model
- **Optimized for Czech language** - High-quality embeddings for 50+ languages
- **Smart query generation** - AI transforms questions into semantic keywords for better retrieval
- **Relevance filtering** - Configurable distance threshold to filter irrelevant results
- **Hybrid search mode** - Combines local knowledge base with web search
- **Fast retrieval** - Vector similarity search with persistent storage

### **AI-Powered Query Generation**
- **Dual-mode query generation:**
  - Local DB queries: Semantic keywords optimized for vector search
  - Web queries: Domain-specific search terms optimized for Google
- Generates 2-4 diverse queries targeting different information angles
- Multi-language support (Czech, English, Slovak, auto-detection)
- Input validation to filter inappropriate or harmful queries

### **Intelligent Web Scraping**
- **Dual-mode content extraction:**
  - Fast HTTP requests for standard pages
  - Selenium WebDriver fallback for anti-bot or dynamic sites
- **Multi-format support:**
  - HTML pages with smart content extraction (text or structured HTML)
  - PDF documents with text extraction
- **Configurable extraction modes:**
  - `text`: Plain text extraction (faster, smaller token usage)
  - `html`: Cleaned HTML structure (better context, semantic hierarchy)

### **AI-Powered Summarization**
- Analyzes scraped content and generates structured responses
- **Response includes:**
  - Concise summary answering the user's question
  - 3-5 key points with relevant details
  - Source citations with URLs
  - Confidence level (high/medium/low)

## System Architecture

```
User Query
    ↓
[1] AI Query Generator (Local DB optimized)
    ↓ (semantic keywords)
[2] Local Vector Database (ChromaDB)
    ↓ (relevant documents with distance scores)
[3] Relevance Filter
    ↓
    ├─ Sufficient results? → [5]
    └─ Need more context ↓
[4] AI Query Generator (Web optimized)
    ↓ (domain-specific search queries)
[5] Google Custom Search API
    ↓ (relevant URLs)
[6] Web Content Scraper
    ↓ (extracted text + metadata)
[7] AI Response Generator
    ↓
Structured Answer with Citations
```

## 🛠️ Installation

### Prerequisites
- **Python 3.8 or higher**
- **Google Custom Search API credentials**
  - API Key from Google Cloud Console
  - Search Engine ID from Programmable Search Engine
- **AI API access** (ChettyAI or compatible endpoint)
- **Docker** (optional, recommended for Selenium)
- **Chrome/Chromium browser** (for local Selenium fallback)

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/OndrejDuda022/MP_AI_Search.git
cd MP_AI_Search
```

2. **Install dependencies:**

**Standard installation (recommended for users)**
```bash
pip install -r requirements.txt
```

This installs all dependencies from [setup.py](setup.py) including:
- `google-api-python-client` - Google Custom Search API
- `python-dotenv` - Environment variable management
- `pydantic` - Data validation
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `selenium` - Web automation
- `webdriver-manager` - ChromeDriver management
- `pdfplumber` - PDF text extraction
- `chromadb` - Vector database for semantic search
- `sentence-transformers` - Multilingual embedding models

3. **Configure environment variables:**

Create a `.env` file in the project root:
```env
# Google Custom Search API
GOOGLE_API_KEY=your_google_api_key
SEARCH_ENGINE_ID=your_search_engine_id

# AI API Configuration
AI_API_KEY=your_ai_api_key

# Target Domain (optional - for domain-specific searches)
TARGET_DOMAIN=your-company.com

# Content Extraction Mode (optional - default: text)
# Options: 'text' (plain text) or 'html' (structured HTML)
EXTRACT_MODE=text

# Local Database Configuration (optional)
USE_LOCAL_DB=True
SEARCH_MODE=hybrid  # Options: 'local', 'web', 'hybrid'
MINIMAL_SOURCES=3
MAXIMAL_SOURCES=5
MIN_RELEVANCE=0.7  # Distance threshold (lower = more similar)

# Selenium Remote URL (optional)
# If set, Selenium will use RemoteWebDriver (e.g., Docker container)
# Example: http://localhost:4444/wd/hub
# Leave empty to use local ChromeDriver
SELENIUM_REMOTE_URL=

# Python Path (if needed)
PYTHONPATH=./src
```

4. **Setup Selenium (optional but recommended):**

**Option A: Automated Docker setup (Windows - recommended)**
```powershell
# Start Selenium container (automatically pulls image if needed)
.\src\scripts\start_selenium.ps1

# Stop the container when done
.\src\scripts\stop_selenium.ps1
```

The script automatically:
- Checks if Docker is running
- Pulls `selenium/standalone-chrome:latest` if not present
- Creates and starts the container with security constraints
- Configures resource limits (1.5 CPU cores, 1GB RAM)

**Option B: Manual Docker setup (Linux/Mac)**
```bash
# Pull and run Selenium container
docker pull selenium/standalone-chrome:latest

docker run \
  --name selenium-chrome \
  --detach \
  --rm \
  --publish 4444:4444 \
  --shm-size=1g \
  --cpus="1.5" \
  --memory="1g" \
  --security-opt no-new-privileges \
  --pids-limit 512 \
  selenium/standalone-chrome:latest
```

**Then update your .env file:**
```env
SELENIUM_REMOTE_URL=http://localhost:4444/wd/hub
```

**Option C: Local ChromeDriver (no Docker)**

If you don't use Docker, `webdriver-manager` will automatically download and manage ChromeDriver. No additional setup required, but leave `SELENIUM_REMOTE_URL` empty in `.env`.

## 📖 Usage

Run the interactive search:
```bash
python src/main.py
```

## Testing

Run tests:
```bash
# Test local database search
python tests/test_local_search.py

# Load documents into local database
python tests/document_loader.py

# Test AI processing
python tests/test_ai_processing.py

# Test Google search and scraping
python tests/test_google_search.py
```

## Local Database Setup

### Initial Setup

1. **Load documents into the database:**
```bash
python tests/document_loader.py
```

This populates the vector database with sample documents using the multilingual embedding model.

2. **Test the search:**
```bash
python tests/test_local_search.py
```

### Understanding the Embedding Model

The system uses **`paraphrase-multilingual-mpnet-base-v2`**:
- **278M parameters** - High-quality embeddings
- **50+ languages** - Excellent Czech language support
- **First run**: Downloads ~470MB model (cached for future use)
- **Distance metric**: Cosine distance (lower = more similar)
  - 0.0 - 0.3: Highly relevant
  - 0.3 - 0.7: Moderately relevant
  - 0.7+: Less relevant

### Search Modes

**`local`** - Search only local database
```env
SEARCH_MODE=local
```
Fast, uses only pre-indexed knowledge.

**`web`** - Search only the web
```env
SEARCH_MODE=web
```
Always uses Google search, ignores local database.

**`hybrid`** (recommended) - Smart combination
```env
SEARCH_MODE=hybrid
```
1. Searches local database first
2. If enough relevant results found → use them
3. Otherwise → supplement with web search
