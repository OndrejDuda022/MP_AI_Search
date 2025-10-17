import os
from googleapiclient.discovery import build
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
from typing import Optional

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
        urls = [item["link"] for item in items[:3]]
        all_urls.extend(urls)

    return all_urls

#1st attempt: fetch page using requests
def fetch_with_requests(url: str, timeout: int = 10) -> Optional[str]:
    try:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,cs;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        response = session.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or 'utf-8'

        return response.text
        
    except requests.RequestException as e:
        print(f"[!] Requests failed for {url}: {e}")
        return None

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
    html = None
    
    if not use_selenium:
        print(f"[1/2] Trying requests for {url}...")
        html = fetch_with_requests(url)
    
    if html is None:
        print(f"[2/2] Falling back to Selenium for {url}...")
        html = fetch_with_selenium(url)
    
    if html:
        try:
            text = extract_text_from_html(html)
            print(f"[+] Successfully extracted {len(text)} characters from {url}")
            return text
        except Exception as e:
            print(f"[!] Failed to parse HTML from {url}: {e}")
            return None
    
    print(f"[-] All methods failed for {url}")
    return None