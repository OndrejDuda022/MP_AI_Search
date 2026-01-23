import os
import chromadb
from typing import List, Dict, Optional

_client = None
_collection = None

def get_db_client():
    global _client
    if _client is None:
        db_path = os.path.join(os.path.dirname(__file__), "..", "vector_db")
        _client = chromadb.PersistentClient(path=db_path)
    return _client

def get_collection(name: str = "knowledge_base"):
    global _collection
    if _collection is None:
        client = get_db_client()
        _collection = client.get_or_create_collection(name=name)
    return _collection

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

def is_relevant(results: List[Dict], min_relevance: float = 0.3) -> bool:
    if not results:
        return False
    
    relevant_count = 0
    for result in results:
        distance = result.get('distance')
        if distance is not None:
            if distance < min_relevance:
                relevant_count += 1
    
    return relevant_count > 0

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

def get_db_stats() -> Dict:
    try:
        collection = get_collection()
        return {
            'count': collection.count(),
            'name': collection.name
        }
    except Exception as e:
        return {'count': 0, 'error': str(e)}
