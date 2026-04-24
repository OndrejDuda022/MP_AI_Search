# AI Search Engine

An intelligent search system that combines Google Custom Search API with advanced AI processing to deliver precise, context-aware answers to user queries. The system automatically generates optimized search queries, scrapes relevant content, and synthesizes comprehensive responses with source citations.

## Possible Future Improvements

- [ ] Implement search retry mechanism for irrelevant results
- [ ] Add caching layer for frequently accessed pages
- [ ] Support for more document formats (DOCX, XLSX, etc.)
- [x] Add web interface (Database Manager available at `/db-manager`)

## Features

### **Web-Based Search Interface**
- **User-friendly search UI** - Search directly from your browser
- **Full configuration options** - Search mode, language, local DB toggle
- **Results display** - AI summary, key points, and source cards

### **Web-Based Database Manager**
- **Web interface** for managing local ChromaDB knowledge base
- **Real-time statistics** - View document count and collection info
- **Bulk document upload** - Upload multiple text files (.txt, .md, .json)
- **Document browser** - View, expand, and delete documents
- **No installation required** - Pure JavaScript, access at `/db-manager` endpoint

### **Local Vector Database (ChromaDB)**
- **Multilingual semantic search** using `paraphrase-multilingual-mpnet-base-v2` embedding model
- **Optimized for various languages** - High-quality embeddings for 50+ languages
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
- **AI API access** (OpenAI API or compatible endpoint)
- **Docker** (optional, recommended for Selenium)
- **Chrome/Chromium browser** (for local Selenium fallback)

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/OndrejDuda022/MP_AI_Search.git
cd MP_AI_Search
```

2. **Run the FIRSTSETUP script:**

**Standard installation (recommended for users)**
```powershell
.\FIRSTSETUP.ps1
```

3. **Configure environment variables:**

Use `.env.example` to create an `.env` file in the project root:
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
# If set, Selenium will try to use RemoteWebDriver (e.g., Docker container)
# Example: http://localhost:4444/wd/hub
# Leave empty to use local ChromeDriver directly
SELENIUM_REMOTE_URL=

# Selenium Fallback (optional - default: True)
# If remote Selenium is unavailable, allow fallback to local ChromeDriver
ALLOW_LOCAL_SELENIUM=True

# Python Path (if needed)
PYTHONPATH=./src
```

## 📖 Usage

### Command Line Interface

Run the interactive search:
```bash
python src/main.py
```

### Web API & Database Manager

Start the REST API server:

**Windows:**
```powershell
.\start_api.ps1
```

**Linux/Mac:**
```bash
chmod +x start_api.sh
./start_api.sh
```

Then access:
- **Search Interface**: http://localhost:8000/search
- **API Documentation**: http://localhost:8000/docs
- **Database Manager**: http://localhost:8000/db-manager

## Local Database Setup

### Initial Setup

1. **Load documents into the database. For example through this:**
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
