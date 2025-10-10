import os
from googleapiclient.discovery import build
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

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
        urls = [item["link"] for item in items[:max]]
        all_urls.extend(urls)

    return all_urls[:max * len(queries)]

def fetch_page_content(url):
    try:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None