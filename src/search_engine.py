"""Core search engine logic - reusable for both CLI and API"""
import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

from src.page_search import search_google, fetch_page_text
from src.ai_processing import process_with_ai, generate_search_queries, generate_local_db_queries
from src.local_db import search_local_db, filter_relevant, get_db_stats
from src.docker_manager import ensure_selenium_container

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class SearchConfig:
    """Configuration for search execution"""
    use_local_db: bool = True
    search_mode: str = "hybrid"  # hybrid/local/web
    internal_mode: bool = False
    language: str = "auto"
    minimal_sources: int = 3
    maximal_sources: int = 5
    min_relevance: float = 0.45

#main search execution function
#parameters: query (str) - user search query, config (SearchConfig) - search configuration
#returns: Dict[str, Any] - search results and metadata
def execute_search(query: str, config: Optional[SearchConfig] = None) -> Dict[str, Any]:
    # Use default config if not provided
    if config is None:
        config = SearchConfig(
            use_local_db=os.getenv("USE_LOCAL_DB", "True").lower() == "true",
            search_mode=os.getenv("SEARCH_MODE", "hybrid").lower(),
            internal_mode=os.getenv("INTERNAL_MODE", "True").lower() == "true",
            minimal_sources=int(os.getenv("MINIMAL_SOURCES", "3")),
            maximal_sources=int(os.getenv("MAXIMAL_SOURCES", "5")),
            min_relevance=float(os.getenv("MIN_RELEVANCE", "0.45"))
        )
    
    # Validate query
    if not query or not query.strip():
        return {
            'success': False,
            'query': query,
            'contents': [],
            'sources': [],
            'ai_response': None,
            'message': 'Empty query'
        }
    
    max_length = int(os.getenv("MAX_USER_QUERY_LENGTH", 300))
    if len(query) > max_length:
        return {
            'success': False,
            'query': query,
            'contents': [],
            'sources': [],
            'ai_response': None,
            'message': f'Query too long (max {max_length} characters)'
        }
    
    contents = []
    messages = []
    
    # Local database search
    if config.use_local_db and config.search_mode in ["hybrid", "local"]:
        logger.info("Searching local database...")
        messages.append("Searching local database...")
        
        stats = get_db_stats()
        logger.info(f"Local database: {stats.get('count', 0)} documents")
        
        if stats.get('count', 0) > 0:
            # Generate queries optimized for vector DB
            local_queries = generate_local_db_queries(query, language=config.language)
            
            if not local_queries:
                logger.warning("Could not generate local DB queries")
                messages.append("Could not generate local DB queries")
            else:
                logger.info(f"Local DB queries: {local_queries}")
                local_results = search_local_db(local_queries, n_results=config.maximal_sources)
                
                # Filter out irrelevant results
                relevant_results = filter_relevant(local_results, config.min_relevance)
                
                if relevant_results:
                    logger.info(f"Found {len(relevant_results)} relevant local results (filtered from {len(local_results)} total)")
                    messages.append(f"Found {len(relevant_results)} relevant local results")
                    contents.extend(relevant_results)
                    
                    # Decide whether to skip web search
                    if config.search_mode == "local":
                        logger.info("Local-only mode, skipping web search")
                        messages.append("Local-only mode, skipping web search")
                    elif len(relevant_results) >= config.minimal_sources:
                        logger.info("Sufficient local results, skipping web search")
                        messages.append("Sufficient local results, skipping web search")
                    else:
                        logger.info("Local results found, but searching web for more context...")
                        messages.append("Local results found, searching web for more context...")
                else:
                    logger.warning(f"No relevant local results found (0/{len(local_results)} passed threshold {config.min_relevance})")
                    messages.append(f"No relevant local results (threshold: {config.min_relevance})")
        else:
            logger.info("Local database is empty")
            messages.append("Local database is empty")
    
    # Web search if needed
    if config.search_mode in ["hybrid", "web"] and len(contents) < config.minimal_sources:
        logger.info("Preparing web search...")
        messages.append("Preparing web search...")
        
        # Generate search queries for Google
        search_queries = generate_search_queries(
            query,
            language=config.language,
            max_input_length=int(os.getenv("MAX_USER_QUERY_LENGTH", 300))
        )
        
        if not search_queries:
            return {
                'success': False,
                'query': query,
                'contents': contents,
                'sources': _extract_source_info(contents),
                'ai_response': None,
                'message': 'Input query was deemed inappropriate'
            }
        
        logger.info(f"Web search queries: {search_queries}")
        
        # Check Selenium container
        selenium_required = os.getenv("CONTAIN_SELENIUM", "False").lower() == "true"
        allow_fallback = os.getenv("ALLOW_LOCAL_SELENIUM", "False").lower() == "true"
        
        can_proceed = True
        if selenium_required:
            if ensure_selenium_container():
                logger.info("Selenium container ready")
                messages.append("Selenium container ready")
            elif allow_fallback:
                logger.info("Selenium container failed, falling back to local ChromeDriver...")
                messages.append("Falling back to local ChromeDriver")
            else:
                logger.warning("Selenium container failed and fallback is not allowed")
                messages.append("Selenium container failed, fallback not allowed")
                if len(contents) == 0:
                    return {
                        'success': False,
                        'query': query,
                        'contents': [],
                        'sources': [],
                        'ai_response': None,
                        'message': 'No local results and Selenium unavailable'
                    }
                can_proceed = False
        
        if can_proceed:
            max_results = int(os.getenv("MAXIMAL_RESULTS", "3"))
            urls = search_google(
                search_queries,
                max=max_results,
                disregard_files=os.getenv("SKIP_FILES", "True").lower() == "true"
            )
            
            if not urls:
                if len(contents) == 0:
                    return {
                        'success': False,
                        'query': query,
                        'contents': [],
                        'sources': [],
                        'ai_response': None,
                        'message': 'No results found (neither local nor web)'
                    }
                messages.append("No web results found")
            else:
                # Remove duplicate URLs
                urls = list(dict.fromkeys(urls))
                logger.info(f"Fetched URLs: {len(urls)}")
                messages.append(f"Fetched {len(urls)} URLs")
                
                # Fetch page contents
                use_selenium = os.getenv("FORCE_SELENIUM", "False").lower() == "true"
                extract_mode = os.getenv("EXTRACT_MODE", "text").lower()
                
                for url in urls:
                    content = fetch_page_text(url, use_selenium, extract_mode)
                    if content:
                        contents.append(content)
    
    # Post-search processing
    if not contents:
        return {
            'success': False,
            'query': query,
            'contents': [],
            'sources': [],
            'ai_response': None,
            'message': 'No content found'
        }
    
    logger.info(f"Total sources found: {len(contents)}")
    messages.append(f"Total sources found: {len(contents)}")
    
    # Extract source information
    sources = _extract_source_info(contents)
    
    # Process with AI if not in internal mode
    ai_response = None
    if not config.internal_mode:
        try:
            ai_response = process_with_ai(contents, query, language=config.language)
            logger.info("AI processing completed")
        except Exception as e:
            logger.error(f"AI processing failed: {e}")
            messages.append(f"AI processing failed: {str(e)}")
    
    return {
        'success': True,
        'query': query,
        'contents': contents,
        'sources': sources,
        'ai_response': ai_response,
        'message': '; '.join(messages)
    }

#extract source information from contents for display
#parameters: contents (List[Dict]) - list of content dictionaries with potential source info
#returns: List[Dict] - list of source info dictionaries with url, title, type, and length
def _extract_source_info(contents: List[Dict]) -> List[Dict]:
    sources = []
    for content in contents:
        sources.append({
            'url': content.get('url', 'N/A'),
            'title': content.get('title', 'N/A'),
            'type': content.get('type', 'N/A'),
            'length': content.get('length', 0)
        })
    return sources
