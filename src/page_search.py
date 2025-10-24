import os
from googleapiclient.discovery import build
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import time
from typing import Optional
import io
import pdfplumber



load_dotenv()

#function to search google using Custom Search API
def search_google(queries, max=5):
    api_key = os.getenv("GOOGLE_API_KEY")
    search_engine_id = os.getenv("SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        raise ValueError("Missing Google API key or Search Engine ID in environment variables.")

    service = build("customsearch", "v1", developerKey=api_key)
    all_urls = []

    for query in queries:
        result = service.cse().list(q=query, cx=search_engine_id).execute()
        items = result.get("items", [])
        
        urls = []
        for item in items:
            url = item["link"]
            url_lower = url.lower()
            
            """
            #skip those weird pdfs that pop up from who knows where
            if 'file.php' in url_lower or '.pdf' in url_lower:
                continue
            """
            urls.append(url)
            if len(urls) >= 3:
                break
        
        all_urls.extend(urls)

    return all_urls[:max]

def is_pdf_content(response: requests.Response) -> bool:
    content_type = response.headers.get('Content-Type', '').lower()
    
    if 'application/pdf' in content_type:
        return True
    
    if response.content[:4] == b'%PDF':
        return True
    
    return False

def extract_text_from_pdf(pdf_content: bytes) -> Optional[str]:
    try:
        text_parts = []
        
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        full_text = '\n'.join(text_parts)
        full_text = ' '.join(full_text.split())
        
        return full_text
    
    except Exception as e:
        print(f"[!] Error while extracting text from PDF: {e}")
        return None

#1st attempt: fetch page using requests
def fetch_with_requests(url: str, timeout: int = 10) -> Optional[tuple[str, bool]]:
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

        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        #check if PDF
        if is_pdf_content(response):
            print(f"PDF detected: {url}")
            text = extract_text_from_pdf(response.content)
            return (text, True)

        #HTML content
        response.encoding = response.apparent_encoding or 'utf-8'
        return (response.text, False)
        
    except requests.RequestException as e:
        print(f"[!] Requests failed for {url}: {e}")
        return (None, False)

#2nd attempt: fallback to fetch page using Selenium
def fetch_with_selenium(url: str, timeout: int = 15) -> Optional[str]:
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        print(f"[*] Trying Selenium for {url} (this may take a moment)...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(timeout)
        
        try:
            driver.get(url)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            #javascript execution delay
            time.sleep(2)
            
            html = driver.page_source
            print(f"[+] Selenium successfully fetched {url}")
            
            return html
        finally:
            driver.quit()
            
    except ImportError:
        print(f"[!] Selenium not installed.")
        print(f"[!] Skipping Selenium fallback for {url}")
        return None
    except Exception as e:
        print(f"[!] Selenium failed for {url}: {e}")
        return None

#get text content from HTML
def extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    
    for script in soup(["script", "style"]):
        script.decompose()
    text = soup.get_text(separator=' ', strip=True)
    text = ' '.join(text.split())
    return text

#main function to fetch page text with fallback
def fetch_page_text(url: str, use_selenium: bool = False) -> Optional[str]:
    result = None
    is_pdf = False
    
    if not use_selenium:
        print(f"[1/2] Trying requests for {url}...")
        result, is_pdf = fetch_with_requests(url)
    
    if result is None and not is_pdf:
        print(f"[2/2] Falling back to Selenium for {url}...")
        html = fetch_with_selenium(url)
        if html:
            result = html
    
    if result:
        if is_pdf:
            print(f"[+] Successfully extracted {len(result)} characters from PDF: {url}")
            return f"{url} — {result}"
        else:
            try:
                text = extract_text_from_html(result)
                print(f"[+] Successfully extracted {len(text)} characters from {url}")
                return f"{url} — {text}"
            except Exception as e:
                print(f"[!] Failed to parse HTML from {url}: {e}")
                return None
    
    print(f"[-] All methods failed for {url}")
    return None