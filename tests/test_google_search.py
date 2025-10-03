import os
import json
from src.google_search import search_google

def test_google_search():
    # Test query
    query = "OpenAI"

    # Perform search
    results = search_google(query)

    # Save results to a file
    output_file = "test_google_results_1.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    test_google_search()