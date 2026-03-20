"""Module for searching web pages and extracting content, with support for both requests and Selenium as a fallback."""
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import time
from typing import Optional, Dict
import io
import pdfplumber

load_dotenv()

#function to search google using Custom Search API
#parameters: queries (List[str]) - list of search queries, max (int) - max results per query, disregard_files (bool) - whether to skip file links
#returns: List[str] - list of URLs
def search_google(queries, max=3, disregard_files=False):
    api_key = os.getenv("GOOGLE_API_KEY")
    search_engine_id = os.getenv("SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        raise ValueError("[!] Missing Google API key or Search Engine ID in environment variables.")

    service = build("customsearch", "v1", developerKey=api_key)
    all_urls = []

    for query in queries:
        result = service.cse().list(q=query, cx=search_engine_id).execute()
        items = result.get("items", [])
        
        urls = []
        for item in items:
            url = item["link"]
            
            if disregard_files:
                #skip those weird pdfs that pop up from who knows where
                url_lower = url.lower()
                if 'file.php' in url_lower or '.pdf' in url_lower or '.doc' in url_lower or '.docx' in url_lower:
                    print(f"[*] Skipping file URL: {url}")
                    continue
            
            urls.append(url)
            if len(urls) >= max:
                break
        
        all_urls.extend(urls)

    return all_urls

#main function to fetch page text with fallback
#parameters: url (str) - target URL, use_selenium (bool) - whether to force Selenium, extract_mode (str) - 'text' or 'html'
#returns: Optional[Dict] - dictionary with page info or None if failed
def fetch_page_text(url: str, use_selenium: bool = False, extract_mode: str = 'text') -> Optional[Dict]:
    result = None
    is_pdf = False
    
    if not use_selenium:
        print(f"[1/2] Trying requests for {url}...")
        result, is_pdf = fetch_with_requests(url)
    
    # Fallback to Selenium if we don't have any result
    if result is None or result == "":
        print(f"[2/2] Falling back to Selenium for {url}...")
        html = fetch_with_selenium(url)
        if html:
            result = html
            is_pdf = False  # Selenium returns HTML, not PDF
    
    if result:
        if is_pdf:
            print(f"[+] Successfully extracted {len(result)} characters from PDF: {url}")
            title = extract_title(text=result)
            return {
                "url": url,
                "type": "pdf",
                "title": title,
                "content": result,
                "length": len(result),
                "timestamp": time.time()
            }
        else:
            try:
                content, title = extract_text_from_html(result, mode=extract_mode)
                content_type = "html_structured" if extract_mode == 'html' else "html"
                print(f"[+] Successfully extracted {len(content)} characters from {url} (mode: {extract_mode})")
                return {
                    "url": url,
                    "type": content_type,
                    "title": title,
                    "content": content,
                    "length": len(content),
                    "timestamp": time.time()
                }
            except Exception as e:
                print(f"[!] Failed to parse HTML from {url}: {e}")
                return None
    
    print(f"[-] All methods failed for {url}")
    return None

#1st attempt: fetch page using requests
#parameters: url (str) - target URL, timeout (int) - request timeout, max_size_mb (int) - max content size in MB
#returns: Optional[tuple[str, bool]] - tuple of (content string, is_pdf flag) or (None, False) if failed
def fetch_with_requests(url: str, timeout: int = 10, max_size_mb: int = int(os.getenv("MAX_PAGE_SIZE", 10))) -> Optional[tuple[str, bool]]:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,cs;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        
        # Check content size before downloading
        content_length = response.headers.get('Content-Length')
        if content_length:
            size_mb = int(content_length) / (1024 * 1024)
            if size_mb > max_size_mb:
                print(f"[!] Content too large: {size_mb:.1f}MB (max {max_size_mb}MB)")
                return (None, False)
        
        response.raise_for_status()
        
        # Download content with size limit
        content = b''
        max_bytes = max_size_mb * 1024 * 1024
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > max_bytes:
                print(f"[!] Content exceeded {max_size_mb}MB, truncating")
                break
        
        #check if PDF
        if content[:4] == b'%PDF' or response.headers.get('Content-Type', '').lower().startswith('application/pdf'):
            print(f"[*] PDF detected: {url}")
            text = extract_text_from_pdf(content)
            if text:
                return (text, True)
            else:
                print(f"[!] PDF text extraction failed, will try Selenium fallback")
                return (None, False)

        #HTML content
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = content.decode('latin-1')
            except:
                print(f"[!] Failed to decode content from {url}")
                return (None, False)
        
        return (text, False)
        
    except requests.RequestException as e:
        print(f"[!] Requests failed for {url}: {e}")
        return (None, False)

#check if remote Selenium server is reachable
#parameters: remote_url (str) - remote Selenium URL
#returns: bool - True if reachable, False otherwise
def _is_remote_selenium_available(remote_url: str) -> bool:
    try:
        import requests
        # Check if Selenium server is responding.
        # Support both URL styles:
        # - http://host:4444/wd/hub
        # - http://host:4444
        base = remote_url.rstrip("/")
        status_url = base.replace('/wd/hub', '/status') if base.endswith('/wd/hub') else f"{base}/status"
        response = requests.get(status_url, timeout=2)
        return response.status_code == 200
    except:
        return False

#2nd attempt: fallback to fetch page using Selenium
#parameters: url (str) - target URL, timeout (int) - page load timeout, max_size_mb (int) - max HTML size in MB
#returns: Optional[str] - page HTML content or None if failed
def fetch_with_selenium(url: str, timeout: int = 15, max_size_mb: int = int(os.getenv("MAX_PAGE_SIZE", 10))) -> Optional[str]:
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        #check for PDF URLs before loading (save resources)
        url_lower = url.lower()
        if url_lower.endswith('.pdf') or '.pdf?' in url_lower or 'file.php' in url_lower:
            print(f"[!] Selenium cannot extract text from PDF files: {url}")
            print(f"[*] PDF files should be handled by requests with pdfplumber")
            return None
        
        print(f"[*] Trying Selenium for {url} (this may take a moment)...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Determine which WebDriver to use.
        # ensure_selenium_container() (called before fetch_with_selenium) sets
        # SELENIUM_REMOTE_URL=localhost:4444 when a local Docker container is found,
        # or it is pre-set to the Compose sidecar URL when running in a container.
        # If it is empty, there is no Selenium server and we go straight to
        # local ChromeDriver.
        from src.docker_manager import is_running_in_container
        in_container = is_running_in_container()
        remote_url = os.getenv("SELENIUM_REMOTE_URL", "").strip()

        # Local ChromeDriver is always allowed outside a container.
        # This guarantees local execution still works even if
        # SELENIUM_REMOTE_URL is configured but unreachable.
        allow_local_fallback = not in_container
        
        driver = None
        
        if remote_url:
            # Try remote Selenium first
            if _is_remote_selenium_available(remote_url):
                print(f"[*] Using remote Selenium at {remote_url}")
                try:
                    driver = webdriver.Remote(command_executor=remote_url, options=chrome_options)
                except Exception as e:
                    print(f"[!] Failed to connect to remote Selenium: {e}")
                    driver = None
            else:
                print(f"[!] Remote Selenium at {remote_url} is not available")
            
            # Fall back to local if remote failed and fallback is allowed
            if driver is None and allow_local_fallback:
                print(f"[*] Falling back to local ChromeDriver...")
                try:
                    driver = webdriver.Chrome(options=chrome_options)
                except Exception as e:
                    print(f"[!] Failed to start local ChromeDriver: {e}")
                    return None
            elif driver is None:
                print(f"[!] Remote Selenium unavailable and local fallback is disabled")
                return None
        else:
            # Use local ChromeDriver directly
            print(f"[*] Using local ChromeDriver")
            try:
                driver = webdriver.Chrome(options=chrome_options)
            except Exception as e:
                print(f"[!] Failed to start local ChromeDriver: {e}")
                return None
        
        driver.set_page_load_timeout(timeout)
        
        try:
            driver.get(url)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            #javascript execution delay
            time.sleep(2)
            
            html = driver.page_source
            
            #check HTML size after fetching (protection against huge pages)
            size_mb = len(html.encode('utf-8')) / (1024 * 1024)
            if size_mb > max_size_mb:
                print(f"[!] HTML too large: {size_mb:.1f}MB (max {max_size_mb}MB)")
                print(f"[!] Rejecting oversized content from {url}")
                return None
            
            print(f"[+] Selenium successfully fetched {url} ({size_mb:.1f}MB)")
            
            return html
        finally:
            driver.quit()

    #don't forget to install chromedriver      
    except ImportError:
        print(f"[!] Selenium not installed.")
        print(f"[!] Skipping Selenium fallback for {url}")
        return None
    except Exception as e:
        print(f"[!] Selenium failed for {url}: {e}")
        return None

#extract title from HTML or text
#parameters: soup (BeautifulSoup) - parsed HTML, text (str) - raw text content
#returns: str - extracted title or fallback title
def extract_title(soup: BeautifulSoup = None, text: str = None) -> str:
    if soup:
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        #try to get h1 as fallback
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
    
    #for PDF or if no title found, try to extract from first line
    if text:
        first_line = text.split('\n')[0].strip() if '\n' in text else text[:100].strip()
        return first_line if len(first_line) < 150 else first_line[:150] + "..."
    
    return "Untitled"

#get text content from HTML
#parameters: html (str) - raw HTML content, mode (str) - extraction mode ('text' or 'html'), max_size_mb (int) - max size in MB
#returns: tuple[str, str] - extracted content and title
def extract_text_from_html(html: str, mode: str = 'text', max_size_mb: int = 5) -> tuple[str, str]:
    try:
        # Check HTML size limit
        size_mb = len(html.encode('utf-8')) / (1024 * 1024)
        if size_mb > max_size_mb:
            print(f"[!] HTML too large: {size_mb:.1f}MB (max {max_size_mb}MB), truncating...")
            html = html[:max_size_mb * 1024 * 1024]
        
        soup = BeautifulSoup(html, 'html.parser')
        
        title = extract_title(soup=soup)
        
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
            tag.decompose()
    except Exception as e:
        print(f"[!] Error parsing HTML: {e}")
        return ("", "Error")
    
    main_content = soup.find('main') or soup.find('article') or soup.find('body')
    if not main_content:
        main_content = soup
    
    if mode == 'html':
        #clean HTML mode: preserve structure, remove attributes
        content = clean_html(main_content)
        return content, title
    else:
        #text mode: extract plain text
        text = main_content.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())
        return text, title

#clean HTML while preserving semantic structure
#parameters: element (Tag) - BeautifulSoup Tag element
#returns: str - cleaned HTML string
def clean_html(element) -> str:

    allowed_tags = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li', 
                   'table', 'tr', 'td', 'th', 'thead', 'tbody',
                   'a', 'strong', 'em', 'b', 'i', 'br', 'div', 'span', 'section'}
    
    clean = BeautifulSoup(str(element), 'html.parser')
    
    for tag in clean.find_all():
        if tag.name not in allowed_tags:
            tag.unwrap()  #keep content but remove tag
    
    #remove all attributes except href for links
    for tag in clean.find_all():
        if tag.name == 'a' and tag.get('href'):
            attrs = {'href': tag['href']}
            tag.attrs = attrs
        else:
            tag.attrs = {}
    
    html_str = str(clean)
    
    lines = html_str.split('\n')
    cleaned_lines = [line for line in lines if line.strip()]
    html_str = '\n'.join(cleaned_lines)
    html_str = ' '.join(html_str.split())
    
    return html_str.strip()

#check if response is PDF
#parameters: response (requests.Response) - HTTP response object
#returns: bool - True if PDF, False otherwise
def is_pdf_content(response: requests.Response) -> bool:
    content_type = response.headers.get('Content-Type', '').lower()
    
    if 'application/pdf' in content_type:
        return True
    
    if response.content[:4] == b'%PDF':
        return True
    
    return False

#extract text from PDF content
#parameters: pdf_content (bytes) - raw PDF content, max_pages (int) - max pages to extract, max_size_mb (int) - max size in MB
#returns: Optional[str] - extracted text or None if failed
def extract_text_from_pdf(pdf_content: bytes, max_pages: int = 50, max_size_mb: int = 10) -> Optional[str]:
    try:
        # Check file size limit
        size_mb = len(pdf_content) / (1024 * 1024)
        if size_mb > max_size_mb:
            print(f"[!] PDF too large: {size_mb:.1f}MB (max {max_size_mb}MB)")
            return None
        
        text_parts = []
        
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            page_count = len(pdf.pages)
            if page_count > max_pages:
                print(f"[*] PDF has {page_count} pages, limiting to first {max_pages}")
            
            for i, page in enumerate(pdf.pages):
                if i >= max_pages:
                    break
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        full_text = '\n'.join(text_parts)
        full_text = ' '.join(full_text.split())
        
        return full_text
    
    except Exception as e:
        print(f"[!] Error while extracting text from PDF: {e}")
        return None