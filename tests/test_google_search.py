import os
import json
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.getenv("PYTHONPATH"))

from page_search import search_google, fetch_page_content

def test_google_search():
    query = "as4u"

    results = search_google([query], max=10)

    output_file = "test_google_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"Results saved to {output_file}")

def test_google_search_with_content():
    query = "as4u"

    results = search_google([query], max=5)

    contents = {}
    for url in results:
        content = fetch_page_content(url)
        if content:
            contents[url] = content

    output_file = "test_google_results_with_content.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"results": results, "contents": contents}, f, ensure_ascii=False, indent=4)

    print(f"Results with content saved to {output_file}")

if __name__ == "__main__":
    #test_google_search()
    test_google_search_with_content()