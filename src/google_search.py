import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

def search_google(query):
    api_key = os.getenv("GOOGLE_API_KEY")
    search_engine_id = os.getenv("SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        raise ValueError("Missing Google API key or Search Engine ID in environment variables.")

    service = build("customsearch", "v1", developerKey=api_key)
    result = service.cse().list(q=query, cx=search_engine_id).execute()
    return result.get("items", [])