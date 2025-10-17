import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.getenv("PYTHONPATH"))
from src.ai_processing import process_with_ai, generate_search_queries

#test processing data with AI
def test_process_with_ai():
    input_file = "debug/test_google_results_with_content.json"
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    user_query = "Stručně v pár větách vypiš co je as4u."

    combined_data = (
        f"User Query: {user_query}\n"
        f"Results: {data['results']}\n"
        f"Contents: {data['contents']}"
    )

    response = process_with_ai(combined_data, user_query)
    
    print("\n=== AI Response (Structured Output) ===")
    print(f"Summary: {response.summary}")
    print(f"\nKey Points:")
    for i, point in enumerate(response.key_points, 1):
        print(f"  {i}. {point}")
    print(f"\nSources Used: {response.sources_used}")
    print(f"Confidence: {response.confidence}")
    
    #save to json file
    output_file = "debug/test_ai_response_structured.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(response.model_dump(), f, ensure_ascii=False, indent=4)
        print(f"\nStructured response saved to {output_file}")

#test generating search queries with AI
def test_generate_search_queries():
    user_input = "Kde leží Liberec?"
    queries = generate_search_queries(user_input)
    if queries:
        print("Generated Search Queries:", queries)
        
        #save to json file
        output_file = "debug/test_generated_search_queries.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({"queries": queries}, f, ensure_ascii=False, indent=4)
            print(f"Generated search queries saved to {output_file}")
    else:
        print("The input was deemed inappropriate.")

if __name__ == "__main__":
    test_generate_search_queries()
    #test_process_with_ai()
    