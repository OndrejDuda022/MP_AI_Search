"""Local database management using ChromaDB with a local embedding model."""
import os
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from chromadb.config import Settings
from typing import List, Dict, Optional
import uuid
import logging

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

_client = None
_collection = None  
_embedding_function = None
_model = None  # Cache the model globally


#local embedding function (module-level class for proper ChromaDB serialization)
class _LocalEmbeddingFunction(EmbeddingFunction[Documents]):
    """Local-only embedding function using SentenceTransformer."""
    
    model_name = "paraphrase-multilingual-mpnet-base-v2"

    def __call__(self, input: Documents) -> Embeddings:  # noqa: A002
        global _model
        if _model is None:
            from sentence_transformers import SentenceTransformer
            local_model_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "models", "paraphrase-multilingual-mpnet-base-v2")
            )
            _model = SentenceTransformer(local_model_path, local_files_only=True)
        # normalize_embeddings=True ensures unit vectors so that the
        # squared-L2 distance returned by ChromaDB maps cleanly to
        # cosine similarity via:  cosine_sim = 1 - (L2_squared / 2)
        embeddings = _model.encode(input, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()

#get or create the ChromaDB client
#parameters: none
#returns: ChromaDB client instance
def get_db_client():
    global _client
    if _client is None:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "vector_db"))
        _client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        logger.info(f"ChromaDB client initialised at: {db_path}")
    return _client

#build a local-only embedding function using SentenceTransformer directly
#parameters: none
#returns: callable embedding function
def get_embedding_function():
    global _embedding_function
    if _embedding_function is None:
        local_model_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "models", "paraphrase-multilingual-mpnet-base-v2")
        )
        logger.info(f"Loading embedding model from local path: {local_model_path}")
        
        _embedding_function = _LocalEmbeddingFunction()
        logger.info("Local embedding model loaded successfully (no network access).")
    return _embedding_function

#get or create the collection
#parameters: name (str) - name of the collection
#returns: ChromaDB collection instance
def get_collection(name: str = "knowledge_base"):
    global _collection
    if _collection is None:
        client = get_db_client()
        ef = get_embedding_function()

        _collection = client.get_or_create_collection(
            name=name,
            embedding_function=ef,
            metadata={"description": "Knowledge base with multilingual embeddings"}
        )

        logger.info(f"Using collection '{name}' with local embedding model.")
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

#filter results based on cosine similarity threshold
#parameters: results (List[Dict]) - list of search results, min_relevance (float) - minimum cosine similarity (0-1, higher = stricter)
#returns: List[Dict] - list of relevant results only
def filter_relevant(results: List[Dict], min_relevance: float) -> List[Dict]:
    if not results:
        return []
    
    relevant_results = []
    for result in results:
        distance = result.get('distance')
        if distance is not None:
            # ChromaDB's default "l2" metric stores the *squared* Euclidean
            # distance (|A-B|^2).  For unit-normalized embeddings this equals
            # 2*(1 - cosine_similarity), so:
            #   cosine_similarity = 1 - (L2_squared / 2)
            # Range: 1.0 = identical, 0.0 = orthogonal, -1.0 = opposite.
            cosine_sim = 1.0 - distance / 2.0
            if cosine_sim >= min_relevance:
                relevant_results.append(result)
    
    return relevant_results

#add or update a document in the local database
#parameters: content (str) - document content, metadata (Optional[Dict]) - document metadata, doc_id (Optional[str]) - document ID
#returns: none
def add_document(content: str, metadata: Optional[Dict] = None, doc_id: Optional[str] = None):
    collection = get_collection()

    if doc_id is None:
        # Generate a unique ID if not provided
        doc_id = str(uuid.uuid4())

    # Use the add method to insert or overwrite the document
    collection.add(
        documents=[content],    
        ids=[doc_id],
        metadatas=[metadata or {}]
    )
    logger.info(f"Document with ID '{doc_id}' added/updated successfully.")

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
#parameters: content (str) - document content, metadata (Optional[Dict]) - document metadata, doc_id (Optional[str]) - document ID
#returns: str - document ID
def add_document_to_db(content: str, metadata: Optional[Dict] = None, doc_id: Optional[str] = None) -> str:
    """Add a document to the database and return its ID"""
    import hashlib

    # Generate doc_id if not provided
    if doc_id is None:
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
