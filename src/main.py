"""Main entry point for the AI Search application. Handles user input, executes search, and displays results."""
#load necessary libraries
import os
import sys
from dotenv import load_dotenv

#prepare environment
load_dotenv()
sys.path.insert(0, os.getenv("PYTHONPATH"))
from src.search_engine import execute_search, SearchConfig

#main function
def main():
    query = input("[*] Enter your search query: ").strip()
    
    #basic input validation
    if not query:
        print("[!] Empty query. Process terminated.")
        return
    
    if len(query) > int(os.getenv("MAX_USER_QUERY_LENGTH", 300)):
        print(f"[!] Query too long (max {os.getenv('MAX_USER_QUERY_LENGTH', 300)} characters). Process terminated.")
        return

    #load configuration from .env
    config = SearchConfig(
        use_local_db=os.getenv("USE_LOCAL_DB", "True").lower() == "true",
        search_mode=os.getenv("SEARCH_MODE", "hybrid").lower(),
        internal_mode=os.getenv("INTERNAL_MODE", "True").lower() == "true",
        language=os.getenv("LANGUAGE", "auto"),
        minimal_sources=int(os.getenv("MINIMAL_SOURCES", "3")),
        maximal_sources=int(os.getenv("MAXIMAL_SOURCES", "5")),
        min_relevance=float(os.getenv("MIN_RELEVANCE", "0.6"))
    )
    
    print(f"[*] Executing search (mode: {config.search_mode})...")
    
    #execute search
    result = execute_search(query, config)
    
    #display results
    if not result['success']:
        print(f"[!] {result['message']}")
        return
    
    contents = result['contents']
    
    #display source preview
    print(f"\n[*] Total sources found: {len(contents)}")
    for i, source in enumerate(result['sources'], 1):
        print(f"  {i}. [{source.get('type', 'N/A')}] {source.get('title', 'N/A')}")
    
    #process results
    if config.internal_mode:
        #internal mode - display raw results without AI processing
        print("\n[*] Internal mode - displaying raw results (no AI processing)")
        display_raw_results(contents, query)
    else:
        #normal mode - AI processing
        ai_response = result.get('ai_response')
        if ai_response:
            pretty_output(ai_response)
        else:
            print("\n[!] AI processing was not available")
            display_raw_results(contents, query)

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

#function to display raw results (internal mode)
def display_raw_results(contents, query):
    print("\n" + "="*60)
    print(f"RAW SEARCH RESULTS FOR: {query}")
    print("="*60)
    
    for i, source in enumerate(contents, 1):
        print(f"\n--- Result {i} ---")
        print(f"Source: {source.get('url', 'N/A')}")
        print(f"Type: {source.get('type', 'N/A')}")
        print(f"Title: {source.get('title', 'N/A')}")
        print(f"\nContent ({source.get('length', 0)} chars):")
        print("-" * 60)
        print(source.get('content', 'N/A')[:500])
        if source.get('length', 0) > 500:
            print(f"\n... (truncated, {source.get('length', 0) - 500} more chars)")
        print("-" * 60)
    
    print("\n" + "="*60)
    print(f"Total Results: {len(contents)}")
    print("="*60)

#execute main function
if __name__ == "__main__":
    main()