# AI Search Engine

An intelligent search system that combines Google Custom Search API with advanced AI processing to deliver precise, context-aware answers to user queries. The system automatically generates optimized search queries, scrapes relevant content, and synthesizes comprehensive responses with source citations.

## Future Improvements

- [ ] Sanitize user input
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
  - Selenium WebDriver fallback for anti-bot sites
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
- Python 3.8 or higher
- Google Custom Search API credentials
- AI API access (ChettyAI or compatible endpoint)
- Chrome/Chromium browser (for Selenium)

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/OndrejDuda022/AI_Search.git
cd AI_Search
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

Or install in development mode:
```bash
pip install -e .
```

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

# Python Path (if needed)
PYTHONPATH=./src
```

## 📖 Usage

Run the interactive search:
```bash
python src/main.py
```

## 🔧 Configuration

### Search Query Generation

Customize query generation in `ai_processing.py`:
```python
queries = generate_search_queries(
    user_input="your question",
    language="auto"  # Options: "auto", "cs", "en", "sk"
)
```

### Web Scraping Options

```python
# Use only HTTP requests (faster)
content = fetch_page_text(url, use_selenium=False)

# Use Selenium for JavaScript-heavy sites (slower but more reliable)
content = fetch_page_text(url, use_selenium=True)

# Control number of results per query
urls = search_google(queries, max=5, disregard_files=True)
```

### AI Response Language

```python
response = process_with_ai(
    data=contents,
    user_query="your question",
    language="auto"  # Options: "auto", "cs", "en", "sk"
)
```
## Testing

Run tests:
```bash
# Test AI processing
python tests/test_ai_processing.py

# Test Google search and scraping
python tests/test_google_search.py
```
