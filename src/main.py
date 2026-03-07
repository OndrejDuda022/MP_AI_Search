# Load necessary libraries
import os
import sys
from dotenv import load_dotenv

# Prepare environment
load_dotenv()
sys.path.insert(0, os.getenv("PYTHONPATH"))
from page_search import search_google, fetch_page_text
from ai_processing import process_with_ai, generate_search_queries, generate_local_db_queries
from local_db import search_local_db, filter_relevant, get_db_stats
from docker_manager import ensure_selenium_container

# Main function
def main():
    query = input("[*] Enter your search query: ").strip()
    
    # Basic input validation
    max_query_length = int(os.getenv("MAX_USER_QUERY_LENGTH", 300))
    if not query:
        print("[!] Empty query. Process terminated.")
        return

    if len(query) > max_query_length:
        print(f"[!] Query too long (max {max_query_length} characters). Process terminated.")
        return

    # Load configuration from .env
    # Default settings:
        # Use local DB: True
        # Search mode: hybrid
        # Internal mode: True - for safety
        # Minimal sources: 3
        # Minimal relevance: 0.6
    use_local_db = os.getenv("USE_LOCAL_DB", "True").lower() == "true"
    search_mode = os.getenv("SEARCH_MODE", "hybrid").lower()  # hybrid/local/web
    internal_mode = os.getenv("INTERNAL_MODE", "True").lower() == "true"
    minimal_sources = int(os.getenv("MINIMAL_SOURCES", "3"))
    maximal_sources = int(os.getenv("MAXIMAL_SOURCES", "5"))
    min_relevance = float(os.getenv("MIN_RELEVANCE", "0.45"))
    
    contents = []
    
    # Try local database first
    if use_local_db and search_mode in ["hybrid", "local"]:
        print("[*] Searching local database...")
        
        # Show DB stats
        stats = get_db_stats()
        print(f"[*] Local database: {stats.get('count', 0)} documents")
        
        if stats.get('count', 0) > 0:
            # Generate queries optimized for vector DB (semantic search)
            local_queries = generate_local_db_queries(query, language=os.getenv("LANGUAGE", "auto"))
            if not local_queries:
                print("[!] Could not generate local DB queries")
            else:
                print(f"[*] Local DB queries: {local_queries}")
                local_results = search_local_db(local_queries, n_results=maximal_sources)
                
                # Filter out irrelevant results
                relevant_results = filter_relevant(local_results, min_relevance)
                
                if relevant_results:
                    print(f"[*] Found {len(relevant_results)} relevant local results (filtered from {len(local_results)} total)")
                    contents.extend(relevant_results)
                    
                    # If local-only mode, skip web
                    if search_mode == "local":
                        print("[*] Local-only mode, skipping web search")
                    # If hybrid and enough good results, skip web
                    elif len(relevant_results) >= minimal_sources:
                        print("[*] Sufficient local results, skipping web search")
                    else:
                        print("[*] Local results found, but searching web for more context...")
                else:
                    print(f"[!] No relevant local results found (0/{len(local_results)} passed threshold {min_relevance})")
        else:
            print("[!] Local database is empty")
    
    # Web search
    if search_mode in ["hybrid", "web"] and len(contents) < minimal_sources:
        print("[*] Preparing web search...")
        
        # Generate search queries for Google
        search_queries = generate_search_queries(query, language=os.getenv("LANGUAGE", "auto"), max_input_length=max_query_length)
        if not search_queries:
            print("[!] The input query was deemed inappropriate. Process terminated.")
            return
        print(f"[*] Web search queries: {search_queries}")
        
        # Check Selenium container
        selenium_required = os.getenv("CONTAIN_SELENIUM", "False").lower() == "true"
        allow_fallback = os.getenv("ALLOW_LOCAL_SELENIUM", "False").lower() == "true"

        selenium_available = False
        can_proceed = True
        if selenium_required:
            if ensure_selenium_container():
                print("[+] Selenium container ready")
                selenium_available = True
            elif allow_fallback:
                print("[*] Selenium container failed. Falling back to local ChromeDriver...")
                selenium_available = True  # local ChromeDriver still usable
            else:
                print("[!] Selenium container failed and fallback is not allowed.")
                if len(contents) == 0:
                    print("[!] No local results available. Process terminated.")
                    return
                print("[*] Continuing with local results only.")
                can_proceed = False
        else:
            # Selenium not required — local ChromeDriver is always usable as fallback
            selenium_available = True
        
        if not can_proceed:
            # Skip web search, proceed with local results only
            pass
        else:
            max_results = int(os.getenv("MAXIMAL_RESULTS", "3"))
            urls = search_google(search_queries, max=max_results, disregard_files=os.getenv("SKIP_FILES", "True").lower() == "true")
            if not urls:
                if len(contents) == 0:
                    print("[!] No results found (neither local nor web). Process terminated.")
                    return
            else:
                # Remove duplicate URLs
                urls = list(dict.fromkeys(urls))
                print(f"[*] Fetched URLs: {len(urls)}")
                
                # Fetch page contents
                use_selenium = os.getenv("FORCE_SELENIUM", "False").lower() == "true"
                extract_mode = os.getenv("EXTRACT_MODE", "text").lower()

                for url in urls:
                    content = fetch_page_text(url, use_selenium, extract_mode, selenium_available)
                    if content:
                        contents.append(content)
    
    # Check if we have any results
    if not contents:
        print("[!] No content found. Process terminated.")
        return
    
    # Display source preview
    print(f"\n[*] Total sources found: {len(contents)}")
    for i, source in enumerate(contents, 1):
        print(f"  {i}. [{source.get('type', 'N/A')}] {source.get('title', 'N/A')}")
    
    # Process results
    if search_mode in ["local", "hybrid"] and internal_mode:
        # Internal mode - display raw results without AI processing
        print("\n[*] Internal mode - displaying raw results (no AI processing)")
        display_raw_results(contents, query)
    else:
        # Normal mode - AI processing
        response = process_with_ai(contents, query, language=os.getenv("LANGUAGE", "auto"))
        pretty_output(response)

# Function to pretty print AI response
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

# Function to display raw results (internal mode)
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

# Execute main function
if __name__ == "__main__":
    main()