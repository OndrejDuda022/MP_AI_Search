import sys
import os
from dotenv import load_dotenv

#prepare environment
load_dotenv()
sys.path.insert(0, os.getenv("PYTHONPATH"))
from src.local_db import search_local_db
from src.ai_processing import generate_local_db_queries

#test with direct query (keywords)
def test_local_with_direct_query():
    query = "obory obor informační technologie specializace"
    print(f"Direct query: {query}\n")
    
    #search database
    results = search_local_db([query], n_results=3)
    
    #filter with low relevance threshold
    # distance is squared L2; for unit vectors: cosine_sim = 1 - distance/2
    min_relevance = 0.45
    relevant_results = [res for res in results if res['distance'] is not None and (1.0 - res['distance'] / 2.0) >= min_relevance]
    
    if not relevant_results:
        print("No relevant documents found.")
    else:
        print(f"Found {len(relevant_results)} documents:\n")
        for i, result in enumerate(relevant_results, 1):
            print(f"{i}. {result['content']}")
            cosine_sim = 1.0 - result['distance'] / 2.0
            print(f"   Score: {result['distance']:.4f}  (cosine_sim: {cosine_sim:.4f})\n")

#test with AI-generated queries
def test_local_with_generated_queries():
    question = "Jaké studijní obory nabízíte?"
    print(f"Question: {question}\n")
    
    #generate optimized queries
    generated_queries = generate_local_db_queries(question)
    
    if not generated_queries:
        print("Could not generate queries.")
        return
    
    print(f"Generated queries: {generated_queries}\n")
    
    #search database
    results = search_local_db(generated_queries, n_results=5)
    
    print(f"Total results returned: {len(results)}\n")
    
    #display ALL results with scores for debugging
    print("ALL RESULTS (for debugging):")
    for i, result in enumerate(results, 1):
        score = result.get('distance', 'N/A')
        print(f"{i}. Score: {score}")
        print(f"   Content: {result['content'][:150]}...")
        print()
    
    #filter with low relevance threshold
    # distance is squared L2; for unit vectors: cosine_sim = 1 - distance/2
    min_relevance = 0.45
    relevant_results = [res for res in results if res['distance'] is not None and (1.0 - res['distance'] / 2.0) >= min_relevance]
    
    print(f"\n{'='*60}")
    if not relevant_results:
        print(f"No relevant documents found (cosine_sim threshold: {min_relevance}).")
    else:
        print(f"Found {len(relevant_results)} documents passing cosine_sim threshold {min_relevance}:\n")
        for i, result in enumerate(relevant_results, 1):
            cosine_sim = 1.0 - result['distance'] / 2.0
            print(f"{i}. {result['content']}")
            print(f"   Score: {result['distance']:.4f}  (cosine_sim: {cosine_sim:.4f})\n")

#run tests
if __name__ == "__main__":
    #test_local_with_direct_query()
    test_local_with_generated_queries()