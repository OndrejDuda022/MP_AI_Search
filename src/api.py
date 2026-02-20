"""FastAPI application for AI-powered search with base64 document support"""
import os
import base64
import logging
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

from src.search_engine import execute_search, SearchConfig
from src.local_db import (
    get_db_stats, 
    add_document_to_db, 
    get_all_documents, 
    get_document_by_id,
    delete_document
)
from src.docker_manager import get_selenium_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="AI Search API",
    description="AI-powered search with local database and web search capabilities",
    version=os.getenv("VERSION", "not specified")
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class Base64Document(BaseModel):
    """Model for base64-encoded documents"""
    filename: str = Field(..., description="Name of the document file")
    content: str = Field(..., description="Base64-encoded document content")
    id: Optional[str] = Field(default=None, description="Optional custom document ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional per-document metadata")

    @field_validator('content')
    @classmethod
    def validate_base64(cls, v: str) -> str:
        """Validate that content is valid base64"""
        try:
            base64.b64decode(v, validate=True)
            return v
        except Exception:
            raise ValueError("Invalid base64 content")

class SearchRequest(BaseModel):
    """Model for search requests"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    documents: Optional[List[Base64Document]] = Field(default=None, description="Optional base64-encoded documents to add to search context")
    use_local_db: Optional[bool] = Field(default=True, description="Whether to search local database")
    search_mode: Optional[str] = Field(default="hybrid", description="Search mode: 'hybrid', 'local', or 'web'")
    internal_mode: Optional[bool] = Field(default=False, description="Return raw results without AI processing")
    language: Optional[str] = Field(default="auto", description="Language for queries: 'auto', 'en', 'cs', 'sk'")
    
    @field_validator('search_mode')
    @classmethod
    def validate_search_mode(cls, v: str) -> str:
        """Validate search mode"""
        if v not in ['hybrid', 'local', 'web']:
            raise ValueError("search_mode must be 'hybrid', 'local', or 'web'")
        return v
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language"""
        if v not in ['auto', 'en', 'cs', 'sk']:
            raise ValueError("language must be 'auto', 'en', 'cs', or 'sk'")
        return v

class SourceInfo(BaseModel):
    """Information about a source"""
    url: str
    title: str
    type: str
    length: int

class SearchResponse(BaseModel):
    """Model for search responses"""
    success: bool
    query: str
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    sources: List[SourceInfo]
    confidence: Optional[str] = None
    raw_results: Optional[List[Dict[str, Any]]] = None
    message: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    database_status: Dict[str, Any]
    selenium_status: Optional[str] = None

class DatabaseStats(BaseModel):
    """Database statistics"""
    document_count: int
    collection_name: str
    embedding_model: str

class DocumentUploadRequest(BaseModel):
    """Request to add documents to local database."""
    documents: List[Base64Document]
    default_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadata applied to all documents unless overridden per-document"
    )

class DocumentUploadResponse(BaseModel):
    """Response for document upload"""
    success: bool
    added_count: int
    document_ids: List[str] = Field(default_factory=list, description="IDs assigned to each added document")
    message: str

class DocumentInfo(BaseModel):
    """Information about a single document"""
    id: str
    content: str
    metadata: Dict[str, Any]

class DocumentListResponse(BaseModel):
    """Response for document list"""
    success: bool
    count: int
    documents: List[DocumentInfo]

class DocumentDeleteResponse(BaseModel):
    """Response for document deletion"""
    success: bool
    message: str

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "AI Search API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "search": "/search",
        "db_manager": "/db-manager"
    }

@app.get("/search", tags=["General"])
async def search_interface():
    """Serve the search web interface"""
    search_path = os.path.join(os.path.dirname(__file__), "search.html")
    if not os.path.exists(search_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search interface not found"
        )
    return FileResponse(search_path, media_type="text/html")

@app.get("/db-manager", tags=["General"])
async def db_manager():
    """Serve the database manager web interface"""
    db_manager_path = os.path.join(os.path.dirname(__file__), "db_manager.html")
    if not os.path.exists(db_manager_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Database manager not found"
        )
    return FileResponse(db_manager_path, media_type="text/html")

@app.get("/api/health", response_model=HealthResponse, tags=["General"])
def health_check():
    """Health check endpoint"""
    try:
        db_stats = get_db_stats()
        selenium_status = get_selenium_status()
        
        return HealthResponse(
            status="healthy",
            database_status=db_stats,
            selenium_status=selenium_status or "not_running"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

@app.get("/api/db/stats", response_model=DatabaseStats, tags=["Database"])
def get_database_stats():
    """Get database statistics"""
    try:
        stats = get_db_stats()
        return DatabaseStats(
            document_count=stats.get('count', 0),
            collection_name=stats.get('collection', 'unknown'),
            embedding_model=stats.get('embedding_model', 'paraphrase-multilingual-mpnet-base-v2')
        )
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve database stats: {str(e)}"
        )

@app.post("/api/search", response_model=SearchResponse, tags=["Search"])
def search(request: SearchRequest):
    """
    Execute search query with optional base64 documents
    
    - **query**: The search query string
    - **documents**: Optional list of base64-encoded documents to include in search
    - **use_local_db**: Whether to search local database
    - **search_mode**: Search mode (hybrid/local/web)
    - **internal_mode**: Return raw results without AI processing
    - **language**: Language for generated queries
    """
    try:
        logger.info(f"Search request: '{request.query}' (mode: {request.search_mode})")
        
        # Process uploaded documents if any
        temp_doc_ids = []
        if request.documents:
            logger.info(f"Processing {len(request.documents)} uploaded documents")
            for doc in request.documents:
                try:
                    # Decode base64 content
                    content = base64.b64decode(doc.content).decode('utf-8', errors='ignore')
                    
                    # Add to database temporarily or include in search context
                    doc_id = add_document_to_db(
                        content=content,
                        metadata={"filename": doc.filename, "temporary": True}
                    )
                    temp_doc_ids.append(doc_id)
                    logger.info(f"Added document '{doc.filename}' to search context")
                except Exception as e:
                    logger.warning(f"Failed to process document '{doc.filename}': {e}")
        
        # Configure search
        config = SearchConfig(
            use_local_db=request.use_local_db,
            search_mode=request.search_mode,
            internal_mode=request.internal_mode,
            language=request.language,
            minimal_sources=int(os.getenv("MINIMAL_SOURCES", "3")),
            maximal_sources=int(os.getenv("MAXIMAL_SOURCES", "5")),
            min_relevance=float(os.getenv("MIN_RELEVANCE", "0.6"))
        )
        
        # Execute search
        result = execute_search(request.query, config)
        
        # Build response
        if result.get('success'):
            sources = [
                SourceInfo(
                    url=s.get('url', 'N/A'),
                    title=s.get('title', 'N/A'),
                    type=s.get('type', 'N/A'),
                    length=s.get('length', 0)
                )
                for s in result.get('sources', [])
            ]
            
            response = SearchResponse(
                success=True,
                query=request.query,
                sources=sources,
                message=result.get('message')
            )
            
            if request.internal_mode:
                response.raw_results = result.get('contents', [])
            else:
                ai_response = result.get('ai_response')
                if ai_response:
                    response.summary = ai_response.summary
                    response.key_points = ai_response.key_points
                    response.confidence = ai_response.confidence
            
            return response
        else:
            return SearchResponse(
                success=False,
                query=request.query,
                sources=[],
                message=result.get('message', 'Search failed')
            )
            
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@app.post("/api/db/upload", response_model=DocumentUploadResponse, tags=["Database"])
def upload_documents(request: DocumentUploadRequest):
    """Upload one or more base64-encoded documents to the local database."""
    try:
        added_count = 0
        document_ids: List[str] = []

        for doc in request.documents:
            try:
                # Decode base64 content
                content = base64.b64decode(doc.content).decode('utf-8', errors='ignore')

                # Build merged metadata: defaults < per-document values
                merged_metadata: Dict[str, Any] = {"filename": doc.filename}
                if request.default_metadata:
                    merged_metadata.update(request.default_metadata)
                if doc.metadata:
                    merged_metadata.update(doc.metadata)

                issued_id = add_document_to_db(
                    content=content,
                    metadata=merged_metadata,
                    doc_id=doc.id  # per-document ID (None → auto-generated)
                )
                document_ids.append(issued_id)
                added_count += 1
                logger.info(f"Added document '{doc.filename}' with id '{issued_id}'")
            except Exception as e:
                logger.warning(f"Failed to add document '{doc.filename}': {e}")

        return DocumentUploadResponse(
            success=added_count > 0,
            added_count=added_count,
            document_ids=document_ids,
            message=f"Successfully added {added_count}/{len(request.documents)} documents"
        )

    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@app.get("/api/db/documents", response_model=DocumentListResponse, tags=["Database"])
def list_documents(limit: Optional[int] = None):
    """
    List all documents in the database
    
    - **limit**: Optional maximum number of documents to return
    """
    try:
        documents = get_all_documents(limit=limit)
        
        doc_list = [
            DocumentInfo(
                id=doc['id'],
                content=doc['content'],
                metadata=doc['metadata']
            )
            for doc in documents
        ]
        
        return DocumentListResponse(
            success=True,
            count=len(doc_list),
            documents=doc_list
        )
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )

@app.get("/api/db/documents/{doc_id}", response_model=DocumentInfo, tags=["Database"])
def get_document(doc_id: str):
    """
    Get a specific document by ID
    
    - **doc_id**: The document ID to retrieve
    """
    try:
        document = get_document_by_id(doc_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {doc_id}"
            )
        
        return DocumentInfo(
            id=document['id'],
            content=document['content'],
            metadata=document['metadata']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )

@app.delete("/api/db/documents/{doc_id}", response_model=DocumentDeleteResponse, tags=["Database"])
def delete_document_endpoint(doc_id: str):
    """
    Delete a document from the database
    
    - **doc_id**: The document ID to delete
    """
    try:
        # Check if document exists first
        document = get_document_by_id(doc_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {doc_id}"
            )
        
        # Delete the document
        success = delete_document(doc_id)
        
        if success:
            return DocumentDeleteResponse(
                success=True,
                message=f"Document {doc_id} deleted successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("AI Search API starting up...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Search mode: {os.getenv('SEARCH_MODE', 'hybrid')}")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("AI Search API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
