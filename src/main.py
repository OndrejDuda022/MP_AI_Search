import os
from src.google_search import search_google
from src.ai_processing import process_with_ai
from dotenv import load_dotenv

def main():
    load_dotenv()
    query = input("Enter your search query: ")
    results = search_google(query)
    response = process_with_ai(results)
    print("AI Response:", response)

if __name__ == "__main__":
    main()