import sys
import os
from dotenv import load_dotenv

#prepare environment
load_dotenv()
sys.path.insert(0, os.getenv("PYTHONPATH"))
from src.local_db import search_local_db, get_db_stats

#test query
query = "kontakt škola adresa"

print(f"Dotaz: {query}\n")

#search database
results = search_local_db([query], n_results=3)

#display results
print(f"Nalezeno {len(results)} dokumentů:\n")
for i, result in enumerate(results, 1):
    print(f"{i}. {result['content']}")
    print(f"   Skóre: {result['distance']:.4f}\n")
