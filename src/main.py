#load necessary libraries
import os
import sys
from dotenv import load_dotenv

#prepare environment
load_dotenv()
sys.path.insert(0, os.getenv("PYTHONPATH"))
from page_search import search_google, fetch_page_text
from src.ai_processing import process_with_ai, generate_search_queries

#main function
def main():
    query = input("[*] Enter your search query: ")

    #generate search queries using AI
    search_queries = generate_search_queries(query)
    if not search_queries:
        print("[!] The input query was deemed inappropriate. Process terminated.")
        return
    print("[*] Generated search queries:", search_queries)

    #search google
    urls = search_google(search_queries, disregard_files=True)
    if not urls:
        print("[!] No results found. Process terminated.")
        return
    
    #remove duplicate URLs
    urls = list(dict.fromkeys(urls))
    print(f"[*] Fetched URLs: {len(urls)}")
    for url in urls:
        print(f" - {url}")

    #fetch page contents
    use_selenium = os.getenv("FORCE_SELENIUM", "False").lower() == "true"
    extract_mode = os.getenv("EXTRACT_MODE", "text")
    contents = []
    for url in urls:
        content = fetch_page_text(url, use_selenium, extract_mode)
        if content:
            contents.append(content)

    #display fetched content previews - TO BE REMOVED
    for i, source in enumerate(contents, 1):
        print(f"Source {i}:")
        print(f"  URL: {source.get('url', 'N/A')}")
        print(f"  Title: {source.get('title', 'N/A')}")
        print(f"  Type: {source.get('type', 'N/A')}")
        print(f"  Length: {source.get('length', 0)} chars")
        print(f"  Preview: {source.get('content', '')[:100]}...")

    #process contents with AI
    response = process_with_ai(contents, query)

    #display structured response
    pretty_output(response)

#function to pretty print AI response
def pretty_output(response):
    print("\n" + "="*60)
    print("AI RESPONSE")
    print("="*60)
    print(f"\n{response.summary}\n")
    
    if response.key_points:
        print("Key Points:")
        for i, point in enumerate(response.key_points, 1):
            print(f"  {i}. {point}")
    
    if response.sources_used:
        print("\nSources Used:")
        for source in response.sources_used:
            print(f"  - {source}")
    
    print(f"\n[Confidence: {response.confidence}]")
    print("="*60)

#execute main function
if __name__ == "__main__":
    main()