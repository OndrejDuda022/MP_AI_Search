"""FastAPI application for AI-powered search with base64 document support"""
import os
import base64
import logging
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

from src.search_engine import execute_search, SearchConfig
from src.local_db import get_db_stats, add_document_to_db
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
    version="1.0.0"
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
    
    @validator('content')
    def validate_base64(cls, v):
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
    
    @validator('search_mode')
    def validate_search_mode(cls, v):
        """Validate search mode"""
        if v not in ['hybrid', 'local', 'web']:
            raise ValueError("search_mode must be 'hybrid', 'local', or 'web'")
        return v
    
    @validator('language')
    def validate_language(cls, v):
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
    """Request to add documents to local database"""
    documents: List[Base64Document]

class DocumentUploadResponse(BaseModel):
    """Response for document upload"""
    success: bool
    added_count: int
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
        "health": "/api/health"
    }

@app.get("/api/health", response_model=HealthResponse, tags=["General"])
async def health_check():
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
async def get_database_stats():
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
async def search(request: SearchRequest):
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
async def upload_documents(request: DocumentUploadRequest):
    """
    Upload base64-encoded documents to the local database
    
    - **documents**: List of base64-encoded documents with filenames
    """
    try:
        added_count = 0
        
        for doc in request.documents:
            try:
                # Decode base64 content
                content = base64.b64decode(doc.content).decode('utf-8', errors='ignore')
                
                # Add to database
                add_document_to_db(
                    content=content,
                    metadata={"filename": doc.filename}
                )
                added_count += 1
                logger.info(f"Added document '{doc.filename}' to database")
            except Exception as e:
                logger.warning(f"Failed to add document '{doc.filename}': {e}")
        
        return DocumentUploadResponse(
            success=added_count > 0,
            added_count=added_count,
            message=f"Successfully added {added_count}/{len(request.documents)} documents"
        )
        
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
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
