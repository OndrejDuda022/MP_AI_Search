import os
import chromadb
from typing import List, Dict, Optional

_client = None
_collection = None

#get or create the ChromaDB client
#parameters: none
#returns: ChromaDB client instance
def get_db_client():
    global _client
    if _client is None:
        db_path = os.path.join(os.path.dirname(__file__), "..", "vector_db")
        _client = chromadb.PersistentClient(path=db_path)
    return _client

#get or create the collection
#parameters: name (str) - name of the collection
#returns: ChromaDB collection instance
def get_collection(name: str = "knowledge_base"):
    global _collection
    if _collection is None:
        client = get_db_client()
        _collection = client.get_or_create_collection(name=name)
    return _collection

#search the local database
#parameters: queries (List[str]) - list of query strings, n_results (int) - number of results to return per query
#returns: List[Dict] - list of search results
def search_local_db(queries: List[str], n_results: int = 5) -> List[Dict]:
    try:
        collection = get_collection()
        
        if collection.count() == 0:
            print("[!] Local database is empty")
            return []
        
        all_results = []
        
        for query in queries:
            results = collection.query(
                query_texts=[query],
                n_results=min(n_results, collection.count())
            )
            
            if results and results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    all_results.append({
                        'url': f"local_db://{results['ids'][0][i]}",
                        'title': f"Local Document {i+1}",
                        'content': doc,
                        'type': 'local_db',
                        'length': len(doc),
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    })
        
        seen = set()
        unique_results = []
        for result in all_results:
            if result['content'] not in seen:
                seen.add(result['content'])
                unique_results.append(result)
        
        return unique_results[:n_results]
        
    except Exception as e:
        print(f"[!] Error searching local database: {e}")
        return []

#filter results based on distance threshold
#parameters: results (List[Dict]) - list of search results, min_relevance (float) - minimum relevance threshold (distance)
#returns: List[Dict] - list of relevant results only
def filter_relevant(results: List[Dict], min_relevance: float) -> List[Dict]:
    if not results:
        return []
    
    relevant_results = []
    for result in results:
        distance = result.get('distance')
        if distance is not None and distance < min_relevance:
            relevant_results.append(result)
    
    return relevant_results

#add or update a document in the local database
#parameters: content (str) - document content, metadata (Optional[Dict]) - document metadata, doc_id (Optional[str]) - document ID
#returns: none
def add_document(content: str, metadata: Optional[Dict] = None, doc_id: Optional[str] = None):
    collection = get_collection()
    
    if doc_id is None:
        import hashlib
        doc_id = hashlib.md5(content.encode()).hexdigest()
    
    collection.upsert(
        documents=[content],
        ids=[doc_id],
        metadatas=[metadata] if metadata else None
    )
    
    print(f"[*] Document added/updated in local database: {doc_id}")

#retrieve database statistics
#parameters: none
#returns: Dict - database statistics
def get_db_stats() -> Dict:
    try:
        collection = get_collection()
        return {
            'count': collection.count(),
            'name': collection.name
        }
    except Exception as e:
        return {'count': 0, 'error': str(e)}
