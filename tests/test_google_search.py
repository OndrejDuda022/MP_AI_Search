import os
import json
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.getenv("PYTHONPATH"))

from page_search import search_google, fetch_page_text

#test google search
def test_google_search():
    query = "as4u"

    results = search_google([query], max=10)

    output_file = "test_google_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"Results saved to {output_file}")

#test google search and fetch page contents
def test_google_search_with_content():
    query = "as4u"

    results = search_google([query], max=5)

    contents = {}
    for url in results:
        content = fetch_page_text(url)
        if content:
            contents[url] = content

    output_file = "test_google_results_with_content.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"results": results, "contents": contents}, f, ensure_ascii=False, indent=4)

    print(f"Results with content saved to {output_file}")

#test fetching a single page
def test_page_scrape():
    print("\n=== Testing Page Scrape ===")

    url = "https://www.alza.cz/EN/"

    content = fetch_page_text(url)

    output_file = "debug/test_page_content.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Page content saved to {output_file}")

#URLs that might require Selenium
def test_selenium_fallback():
    print("\n=== Testing Selenium Fallback ===")
    
    test_urls = [
        "https://www.as4u.cz",
        "https://www.alza.cz/EN/",
    ]
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        content = fetch_page_text(url)
        
        if content:
            print(f"Success! Extracted {len(content)} characters")
            preview = content[:150] + "..." if len(content) > 150 else content
            print(f"Preview: {preview}")
        else:
            print(f"Failed to fetch {url}")

#always use Selenium
def test_force_selenium():
    print("\n=== Testing Force Selenium Mode ===")
    
    url = "https://github.com"
    print(f"Testing: {url} (forcing Selenium)")
    
    content = fetch_page_text(url, use_selenium=True)
    
    if content:
        print(f"Success! Extracted {len(content)} characters")
    else:
        print(f"Failed to fetch {url}")

if __name__ == "__main__":
    #test_google_search()
    #test_google_search_with_content()
    test_page_scrape()
    #test_selenium_fallback()
    #test_force_selenium()