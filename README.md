# AI Search Engine

An intelligent search system that combines Google Custom Search API with advanced AI processing to deliver precise, context-aware answers to user queries. The system automatically generates optimized search queries, scrapes relevant content, and synthesizes comprehensive responses with source citations.

## Possible Future Improvements

- [ ] Implement search retry mechanism for irrelevant results
- [ ] Add caching layer for frequently accessed pages
- [ ] Support for more document formats (DOCX, XLSX, etc.)
- [ ] Add web interface

## Features

### **AI-Powered Query Generation**
- Transforms natural language questions into optimized Google search queries
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
[1] AI Query Generator
    ↓ (2-4 optimized search queries)
[2] Google Custom Search API
    ↓ (relevant URLs)
[3] Web Content Scraper
    ↓ (extracted text + metadata)
[4] AI Response Generator
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
# Test AI processing
python tests/test_ai_processing.py

# Test Google search and scraping
python tests/test_google_search.py
```
