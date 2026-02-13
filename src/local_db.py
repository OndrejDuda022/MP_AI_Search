import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional

_client = None
_collection = None
_hf_authenticated = False

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
    global _collection, _hf_authenticated
    if _collection is None:
        if not _hf_authenticated:
            hf_token = os.getenv("HF_TOKEN")
            if hf_token:
                try:
                    from huggingface_hub import login
                    login(token=hf_token, add_to_git_credential=False)
                    print("[*] Authenticated with Hugging Face")
                except Exception as e:
                    print(f"[!] Warning: Could not authenticate with Hugging Face: {e}")
            _hf_authenticated = True
        
        client = get_db_client()
        
        #model: paraphrase-multilingual-mpnet-base-v2
        multilingual_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-mpnet-base-v2"
        )
        
        _collection = client.get_or_create_collection(
            name=name,
            embedding_function=multilingual_ef,
            metadata={"description": "Knowledge base with multilingual embeddings"}
        )
        
        print(f"[*] Using embedding model: paraphrase-multilingual-mpnet-base-v2")
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
            'collection': collection.name,
            'embedding_model': 'paraphrase-multilingual-mpnet-base-v2'
        }
    except Exception as e:
        return {'count': 0, 'collection': 'unknown', 'error': str(e)}

#add document to database (API-friendly wrapper)
#parameters: content (str) - document content, metadata (Optional[Dict]) - document metadata
#returns: str - document ID
def add_document_to_db(content: str, metadata: Optional[Dict] = None) -> str:
    """Add a document to the database and return its ID"""
    import hashlib
    doc_id = hashlib.md5(content.encode()).hexdigest()
    add_document(content, metadata, doc_id)
    return doc_id

#get all documents from the database
#parameters: limit (Optional[int]) - maximum number of documents to return
#returns: List[Dict] - list of documents with id, content, and metadata
def get_all_documents(limit: Optional[int] = None) -> List[Dict]:
    """Retrieve all documents from the database"""
    try:
        collection = get_collection()
        total = collection.count()
        
        if total == 0:
            return []
        
        # Get all documents (ChromaDB doesn't have built-in pagination)
        results = collection.get(
            limit=limit if limit else total,
            include=['documents', 'metadatas']
        )
        
        documents = []
        for i in range(len(results['ids'])):
            documents.append({
                'id': results['ids'][i],
                'content': results['documents'][i],
                'metadata': results['metadatas'][i] if results['metadatas'] else {}
            })
        
        return documents
        
    except Exception as e:
        print(f"[!] Error retrieving documents: {e}")
        return []

#get a specific document by ID
#parameters: doc_id (str) - document ID
#returns: Optional[Dict] - document with id, content, and metadata, or None if not found
def get_document_by_id(doc_id: str) -> Optional[Dict]:
    """Retrieve a specific document by its ID"""
    try:
        collection = get_collection()
        
        results = collection.get(
            ids=[doc_id],
            include=['documents', 'metadatas']
        )
        
        if not results['ids']:
            return None
        
        return {
            'id': results['ids'][0],
            'content': results['documents'][0],
            'metadata': results['metadatas'][0] if results['metadatas'] else {}
        }
        
    except Exception as e:
        print(f"[!] Error retrieving document {doc_id}: {e}")
        return None

#delete a document by ID
#parameters: doc_id (str) - document ID to delete
#returns: bool - True if deleted, False if not found or error
def delete_document(doc_id: str) -> bool:
    """Delete a document from the database"""
    try:
        collection = get_collection()
        collection.delete(ids=[doc_id])
        print(f"[*] Document deleted: {doc_id}")
        return True
    except Exception as e:
        print(f"[!] Error deleting document {doc_id}: {e}")
        return False
