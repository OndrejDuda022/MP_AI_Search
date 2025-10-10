import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.getenv("PYTHONPATH"))
from page_search import search_google, fetch_page_content
from src.ai_processing import process_with_ai, generate_search_queries

def main():
    load_dotenv()
    query = input("Enter your search query: ")

    search_queries = generate_search_queries(query)
    if not search_queries:
        print("The input query was deemed inappropriate. Process terminated.")
        return
    print("Generated search queries:", search_queries)

    urls = search_google(search_queries, max=5)
    if not urls:
        print("No results found. Process terminated.")
        return
    
    urls = list(dict.fromkeys(urls))
    print("Fetched URLs:", urls)

    contents = []
    for url in urls:
        content = fetch_page_content(url)
        if content:
            contents.append(content)

    for i, content in enumerate(contents):
        print(f"Content {i + 1} (first 100 chars): {content[:100]}")

    final_input = f"Original query: {query}\n\nUse only the following information to answer the question. If the information is not sufficient, say so.\nFetched contents:\n{contents}"
    response = process_with_ai(final_input)
    print("AI Response:", response)

if __name__ == "__main__":
    main()