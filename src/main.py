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

#main function
def main():
    # Check Selenium container if remote URL is configured
    if not ensure_selenium_container():
        if os.getenv("CONTAIN_SELENIUM", "False").lower() != "true":
            print("[*] Proceeding without Selenium docker setup. Continuing with local ChromeDriver...")
        else:
            if os.getenv("ALLOW_LOCAL_SELENIUM", "False").lower() == "true":
                print("[!] Selenium container setup failed. Continuing with local ChromeDriver...")
            else:
                print("[!] Selenium container setup failed and local Selenium is not allowed. Process terminated.")
                return
    
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

#check and start Selenium container if needed
def ensure_selenium_container():
    contain_selenium = os.getenv("CONTAIN_SELENIUM")
    if not contain_selenium.lower() == "true":
        return False
    
    print("[*] Checking Selenium container...")
    
    try:
        # Check if Docker is available
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("[!] Docker is not running. Please start Docker Desktop or remove SELENIUM_REMOTE_URL from .env")
            return False
        
        # Check if selenium-chrome container is running
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=selenium-chrome", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=5
        )
        
        if "selenium-chrome" in result.stdout:
            print("[+] Selenium container is already running")
            return True
        
        # Try to start the container
        print("[*] Starting Selenium container...")
        if sys.platform == "win32":
            # Use PowerShell script on Windows
            script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src/scripts/start_selenium.ps1")
            if os.path.exists(script_path):
                result = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path], 
                                      capture_output=True, text=True, timeout=30)
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