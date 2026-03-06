import os
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from chromadb.config import Settings
from typing import List, Dict, Optional

_client = None
_collection = None
_embedding_function = None
_model = None  # cached globally to avoid reloading

MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"


#local embedding function
#parameters: input (Documents) - list of document texts to embed
#returns: Embeddings - list of embedding vectors corresponding to the input documents
class _LocalEmbeddingFunction(EmbeddingFunction[Documents]):
    model_name = MODEL_NAME

    def __call__(self, input: Documents) -> Embeddings:  # noqa: A002
        global _model
        if _model is None:
            from sentence_transformers import SentenceTransformer
            local_model_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "models", MODEL_NAME)
            )
            _model = SentenceTransformer(local_model_path, local_files_only=True)
        # normalize_embeddings=True keeps unit vectors so squared-L2 maps to
        # cosine similarity:  cosine_sim = 1 - (L2_squared / 2)
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
    return _client


#get the local embedding function (singleton)
def get_embedding_function():
    global _embedding_function
    if _embedding_function is None:
        model_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "models", MODEL_NAME)
        )
        if not os.path.isdir(model_path):
            raise FileNotFoundError(
                f"[!] Embedding model not found at: {model_path}\n"
                "    Run FIRSTSETUP.ps1 to copy or download the model."
            )
        _embedding_function = _LocalEmbeddingFunction()
        print(f"[*] Using local embedding model: {MODEL_NAME}")
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
        print(f"[*] Using collection '{name}' with local embedding model.")
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
            # ChromaDB returns squared L2 distance for normalized embeddings.
            # cosine_similarity = 1 - (L2_squared / 2)  →  range: 1.0 (identical) to -1.0 (opposite)
            cosine_sim = 1.0 - distance / 2.0
            result['cosine_sim'] = round(cosine_sim, 4)
            print(f"[*] {result.get('url', '?')}  cosine_sim={cosine_sim:.4f}  threshold={min_relevance}")
            if cosine_sim >= min_relevance:
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
