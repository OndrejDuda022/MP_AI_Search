import sys
import os
from dotenv import load_dotenv

# Prepare environment
load_dotenv()
sys.path.insert(0, os.getenv("PYTHONPATH"))
from src.local_db import search_local_db
from src.ai_processing import generate_local_db_queries

# Test with direct query (keywords)
def test_local_with_direct_query():
    query = "obory obor informační technologie specializace"
    print(f"Direct query: {query}\n")
    
    # Search database
    results = search_local_db([query], n_results=3)
    
    # 'min_relevance' here is a raw squared-L2 distance threshold (lower = better match).
    # This is the inverse of filter_relevant() in local_db.py which uses cosine similarity (higher = better).
    min_relevance = 0.7
    relevant_results = [res for res in results if res['distance'] is not None and res['distance'] <= min_relevance]
    
    if not relevant_results:
        print("No relevant documents found.")
    else:
        print(f"Found {len(relevant_results)} documents:\n")
        for i, result in enumerate(relevant_results, 1):
            print(f"{i}. {result['content']}")
            print(f"   Score: {result['distance']:.4f}\n")

# Test with AI-generated queries
def test_local_with_generated_queries():
    question = "Jaké studijní obory nabízíte?"
    print(f"Question: {question}\n")
    
    # Generate optimized queries
    generated_queries = generate_local_db_queries(question)
    
    if not generated_queries:
        print("Could not generate queries.")
        return
    
    print(f"Generated queries: {generated_queries}\n")
    
    # Search database
    results = search_local_db(generated_queries, n_results=5)
    
    print(f"Total results returned: {len(results)}\n")
    
    # Display ALL results with scores for debugging
    print("ALL RESULTS (for debugging):")
    for i, result in enumerate(results, 1):
        score = result.get('distance', 'N/A')
        print(f"{i}. Score: {score}")
        print(f"   Content: {result['content'][:150]}...")
        print()
    
    # NOTE: same raw squared-L2 distance threshold as above (lower = better match).
    min_relevance = 0.7
    relevant_results = [res for res in results if res['distance'] is not None and res['distance'] <= min_relevance]

    print(f"\n{'='*60}")
    if not relevant_results:
        print(f"No relevant documents found (threshold: {min_relevance}).")
    else:
        print(f"Found {len(relevant_results)} documents passing threshold {min_relevance}:\n")
        for i, result in enumerate(relevant_results, 1):
            print(f"{i}. {result['content']}")
            print(f"   Score: {result['distance']:.4f}\n")

# Run tests
if __name__ == "__main__":
    # Test_local_with_direct_query()
    test_local_with_generated_queries()