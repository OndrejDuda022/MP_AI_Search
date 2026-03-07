# AI Search Engine

An intelligent search system that combines ChromaDB and Google Custom Search API with advanced AI processing to deliver precise, context-aware answers to user queries. The system automatically generates optimized search queries, gets relevant content, and synthesizes comprehensive responses with source citations.

## Possible Future Improvements

- [ ] Implement search retry mechanism for irrelevant results
- [ ] Add caching layer for frequently accessed pages
- [ ] Support for more document formats (DOCX, XLSX, etc.)
- [ ] Add web interface

## Features

### **Local Vector Database (ChromaDB)**
- **Multilingual semantic search** using `paraphrase-multilingual-mpnet-base-v2` embedding model
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
- **AI API access** (ChettyAI or other OpenAI API compatible endpoint)
- **Docker** (optional, recommended for Selenium)
- **Chrome/Chromium browser** (for local Selenium fallback)

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/OndrejDuda022/MP_AI_Search.git
cd MP_AI_Search
```

2. **Run the FIRSTSETUP.ps1 script**

**Standard installation (recommended for users)**
```bash
.\FIRSTSETUP.ps1
```

This prepares everything necessary for running, including:
- **Checks Python version present.**
- **Creates a virtual environment and downloads all the dependencies based on the file `requirements.txt`.**
- **Sets up the environment file `.env`.**
- **Downloads the embedding model.**
- **Prepares the Selenium container** (Only if Docker is running).


3. **Fill in the environment variables:**

Open the `.env` file in the project root and fill in:
```env
# Google Custom Search API
GOOGLE_API_KEY=your_google_api_key
SEARCH_ENGINE_ID=your_search_engine_id

# AI API Configuration
AI_API_KEY=your_ai_api_key

# Target Domain (optional - for domain-specific searches)
TARGET_DOMAIN=your-company.com
```
Other variables can be edited for further customization.

## 📖 Usage

Start the virtual environment:
```bash
.venv\Scripts\Activate.ps1
```

Run the interactive search:
```bash
python src/main.py
```

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
