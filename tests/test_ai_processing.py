import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.getenv("PYTHONPATH"))
from src.ai_processing import process_with_ai, generate_search_queries

def test_process_with_ai():
    input_file = "test_google_results_with_content.json"
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    user_query = "Stručně v pár větách vypiš co je as4u."

    combined_data = (
        f"User Query: {user_query}\n"
        f"Results: {data['results']}\n"
        f"Contents: {data['contents']}"
    )

    response = process_with_ai(combined_data)
    print("AI Response:", response)

def test_generate_search_queries():
    user_input = "Kde leží Liberec?"
    queries = generate_search_queries(user_input)
    if queries:
        print("Generated Search Queries:", queries)
    else:
        print("The input was deemed inappropriate.")

if __name__ == "__main__":
    test_generate_search_queries()
    test_process_with_ai()
    