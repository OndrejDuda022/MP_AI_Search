import sys
import os
from dotenv import load_dotenv

#prepare environment
load_dotenv()
sys.path.insert(0, os.getenv("PYTHONPATH"))
from src.local_db import search_local_db

#test query
#query_x = "obory obor informační technologie specializace"
query = "Jaké studijní obory nabízíte?"

print(f"Question: {query}\n")

#search database
results = search_local_db([query], n_results=3)

#filter with low relevance threshold
min_relevance = 0.7
relevant_results = [res for res in results if res['distance'] is not None and res['distance'] <= min_relevance]
if not relevant_results:
    print("No relevant documents found.")
    quit()

#display results
print(f"Found {len(relevant_results)} documents:\n")
for i, result in enumerate(relevant_results, 1):
    print(f"{i}. {result['content']}")
    print(f"Score: {result['distance']:.4f}\n")