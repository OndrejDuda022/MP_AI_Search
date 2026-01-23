#load necessary libraries
import os
import sys
import subprocess
from dotenv import load_dotenv

#prepare environment
load_dotenv()
sys.path.insert(0, os.getenv("PYTHONPATH"))
from page_search import search_google, fetch_page_text
from src.ai_processing import process_with_ai, generate_search_queries
from src.local_db import search_local_db, is_relevant, get_db_stats

#main function
def main():
    query = input("[*] Enter your search query: ").strip()
    
    #basic input validation
    if not query:
        print("[!] Empty query. Process terminated.")
        return
    
    if len(query) > 500:
        print("[!] Query too long (max 500 characters). Process terminated.")
        return

    #generate search queries using AI
    search_queries = generate_search_queries(query)
    if not search_queries:
        print("[!] The input query was deemed inappropriate. Process terminated.")
        return
    print("[*] Generated search queries:", search_queries)

    #load configuration from .env
    use_local_db = os.getenv("USE_LOCAL_DB", "True").lower() == "true"
    if use_local_db:
        print("[*] Local database search is enabled")
        search_mode = os.getenv("SEARCH_MODE", "hybrid").lower()  # hybrid/local/web
        internal_mode = os.getenv("INTERNAL_MODE", "True").lower() == "true"
        minimal_sources = int(os.getenv("MINIMAL_SOURCES", "3"))
        min_relevance = float(os.getenv("MIN_RELEVANCE", "0.6"))
    
    contents = []
    
    #try local database first
    if use_local_db and search_mode in ["hybrid", "local"]:
        print("[*] Searching local database...")
        
        #show DB stats
        stats = get_db_stats()
        print(f"[*] Local database: {stats.get('count', 0)} documents")
        
        if stats.get('count', 0) > 0:
            local_results = search_local_db(search_queries, n_results=5)
            
            if local_results and is_relevant(local_results, min_relevance):
                print(f"[*] Found {len(local_results)} relevant local results")
                contents.extend(local_results)
                
                #if local-only mode, skip web
                if search_mode == "local":
                    print("[*] Local-only mode, skipping web search")
                #if hybrid and enough good results, skip web
                elif len(local_results) >= minimal_sources:
                    print("[*] Sufficient local results, skipping web search")
                else:
                    print("[*] Local results found, but searching web for more context...")
            else:
                print("[!] No relevant local results found")
        else:
            print("[!] Local database is empty")
    
    #web search
    if search_mode in ["hybrid", "web"] and len(contents) < minimal_sources:
        print("[*] Searching web...")
        
        #check Selenium container (only when needed for web search)
        if not ensure_selenium_container():
            if os.getenv("CONTAIN_SELENIUM", "False").lower() != "true":
                print("[*] Proceeding without Selenium docker setup. Continuing with local ChromeDriver...")
            else:
                if os.getenv("ALLOW_LOCAL_SELENIUM", "False").lower() == "true":
                    print("[!] Selenium container setup failed. Continuing with local ChromeDriver...")
                else:
                    print("[!] Selenium container setup failed and local Selenium is not allowed.")
                    if len(contents) == 0:
                        print("[!] Process terminated.")
                        return
                    else:
                        print("[*] Continuing with local results only.")
        
        urls = search_google(search_queries, disregard_files=True)
        if not urls:
            if len(contents) == 0:
                print("[!] No results found (neither local nor web). Process terminated.")
                return
        else:
            #remove duplicate URLs
            urls = list(dict.fromkeys(urls))
            print(f"[*] Fetched URLs: {len(urls)}")
            
            #fetch page contents
            use_selenium = os.getenv("FORCE_SELENIUM", "False").lower() == "true"
            extract_mode = os.getenv("EXTRACT_MODE", "text").lower()
            
            for url in urls:
                content = fetch_page_text(url, use_selenium, extract_mode)
                if content:
                    contents.append(content)
    
    #check if we have any results
    if not contents:
        print("[!] No content found. Process terminated.")
        return
    
    #display source preview
    print(f"\n[*] Total sources found: {len(contents)}")
    for i, source in enumerate(contents, 1):
        print(f"  {i}. [{source.get('type', 'N/A')}] {source.get('title', 'N/A')}")
    
    #process results
    if internal_mode:
        #internal mode - display raw results without AI processing
        print("\n[*] Internal mode - displaying raw results (no AI processing)")
        display_raw_results(contents, query)
    else:
        #normal mode - AI processing
        response = process_with_ai(contents, query)
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

#check and start Selenium container if needed
def ensure_selenium_container():
    contain_selenium = os.getenv("CONTAIN_SELENIUM")
    if not contain_selenium.lower() == "true":
        return False
    
    print("[*] Checking Selenium container...")
    
    try:
        #check if Docker is available
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("[!] Docker is not running. Please start Docker Desktop or remove SELENIUM_REMOTE_URL from .env")
            return False
        
        #check if selenium-chrome container is running
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=selenium-chrome", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=5
        )
        
        if "selenium-chrome" in result.stdout:
            print("[+] Selenium container is already running")
            return True
        
        #try to start the container
        print("[*] Starting Selenium container...")
        if sys.platform == "win32":
            #use PowerShell script on Windows
            script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src/scripts/start_selenium.ps1")
            if os.path.exists(script_path):
                result = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path], capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print("[+] Selenium container started successfully")
                    return True
                else:
                    print(f"[!] Failed to start container: {result.stderr}")
                    return False
        
        print("[!] Please run './start_selenium.ps1' manually or check Docker setup")
        return False
        
    except FileNotFoundError:
        print("[!] Docker is not installed. Please install Docker or use local ChromeDriver")
        return False
    except subprocess.TimeoutExpired:
        print("[!] Docker command timed out")
        return False
    except Exception as e:
        print(f"[!] Error checking Selenium: {e}")
        return False

#execute main function
if __name__ == "__main__":
    main()