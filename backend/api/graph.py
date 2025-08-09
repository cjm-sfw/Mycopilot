import requests
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from backend.cache.redis_cache import cache
from backend.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])

# Semantic Scholar API configuration
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"

@router.get("/paper/{paper_id}")
async def get_paper(paper_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific paper"""
    logger.info(f"Getting paper details for paper_id: {paper_id}")
    try:
        # # Check cache first
        # cache_key = f"paper:{paper_id}"
        # logger.info(f"Checking cache for key: {cache_key}")
        # cached_result = cache.get(cache_key)
        # if cached_result:
        #     logger.info("Returning cached result")
        #     return cached_result
        
        # Get paper information from Semantic Scholar API
        logger.info("Fetching paper information from Semantic Scholar API")
        headers = {"User-Agent": "ScholarAssistant/1.0"}
        paper_url = f"{SEMANTIC_SCHOLAR_API}/paper/{paper_id}"
        params = {
            "fields": "title,abstract,year,authors,citationCount,references,venue"
        }
        
        response = requests.get(paper_url, params=params, headers=headers)
        response.raise_for_status()
        
        paper_data = response.json()
        logger.info(f"Successfully retrieved paper data with title: {paper_data.get('title', 'Unknown')}")
        
        # # Cache the result
        # logger.info("Caching paper data")
        # cache.set(cache_key, paper_data)
        
        return paper_data
    
    except Exception as e:
        logger.error(f"Error getting paper details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting paper details: {str(e)}")

@router.get("/citations/{paper_id}")
async def get_citations(paper_id: str, depth: int = 1, max_nodes: int = 50) -> Dict[str, Any]:
    """Get citation network for a paper"""
    logger.info(f"Getting citation network for paper_id: {paper_id}, depth: {depth}, max_nodes: {max_nodes}")
    try:
        # Check cache first
        # cache_key = f"graph:citations:{paper_id}:{depth}:{max_nodes}"
        # logger.info(f"Checking cache for key: {cache_key}")
        # cached_result = cache.get(cache_key)
        # if cached_result:
        #     logger.info("Returning cached result")
        #     return cached_result
        
        # Get citation network from Semantic Scholar API
        logger.info("Fetching citation network from Semantic Scholar API")
        headers = {"User-Agent": "ScholarAssistant/1.0"}
        citations_url = f"{SEMANTIC_SCHOLAR_API}/paper/{paper_id}/citations"
        params = {
            "limit": min(max_nodes, 100)  # Limit to 100 to avoid rate limiting
        }
        
        # Try up to 5 times with exponential backoff
        max_retries = 5
        for attempt in range(max_retries):
            response = requests.get(citations_url, params=params, headers=headers)
            # Handle rate limiting
            if response.status_code == 429:
                wait_time = 5 * (2 ** attempt)  # Exponential backoff: 5, 10, 20, 40, 80 seconds
                logger.warning(f"Rate limit exceeded. Attempt {attempt + 1}/{max_retries}. Waiting for {wait_time} seconds before retry...")
                import time
                time.sleep(wait_time)
                continue
            else:
                # Add a small delay to avoid rate limiting
                import time
                time.sleep(0.5)
                break
        else:
            # If we've exhausted all retries
            logger.error(f"Failed to get citation data after {max_retries} attempts due to rate limiting")
            # Return empty data instead of raising an exception
            citation_data = {"data": []}
        
        response.raise_for_status()
        
        citation_data = response.json()
        logger.info(f"Retrieved citation data with {len(citation_data.get('data', []))} citations")
        
        # Process and format the data for visualization
        logger.info("Processing citation data")
        processed_data = process_citation_data(citation_data, paper_id)
        
        # Cache the result
        # logger.info("Caching citation data")
        # cache.set(cache_key, processed_data)
        
        return processed_data
    
    except Exception as e:
        logger.error(f"Error getting citation network: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting citation network: {str(e)}")

@router.get("/references/{paper_id}")
async def get_references(paper_id: str, depth: int = 1, max_nodes: int = 50) -> Dict[str, Any]:
    """Get reference network for a paper"""
    logger.info(f"Getting reference network for paper_id: {paper_id}, depth: {depth}, max_nodes: {max_nodes}")
    try:
        # Check cache first
        # cache_key = f"graph:references:{paper_id}:{depth}:{max_nodes}"
        # logger.info(f"Checking cache for key: {cache_key}")
        # cached_result = cache.get(cache_key)
        # if cached_result:
        #     logger.info("Returning cached result")
        #     return cached_result
        
        # Get reference network from Semantic Scholar API
        logger.info("Fetching reference network from Semantic Scholar API")
        headers = {"User-Agent": "ScholarAssistant/1.0"}
        references_url = f"{SEMANTIC_SCHOLAR_API}/paper/{paper_id}/references"
        params = {
            "limit": min(max_nodes, 100),  # Limit to 100 to avoid rate limiting
            "fields": "paperId,title,citationCount,year"  # Specify fields to retrieve
        }
        
        # Try up to 5 times with exponential backoff
        max_retries = 5
        for attempt in range(max_retries):
            response = requests.get(references_url, params=params, headers=headers)
            # Handle rate limiting
            if response.status_code == 429:
                wait_time = 5 * (2 ** attempt)  # Exponential backoff: 5, 10, 20, 40, 80 seconds
                logger.warning(f"Rate limit exceeded. Attempt {attempt + 1}/{max_retries}. Waiting for {wait_time} seconds before retry...")
                import time
                time.sleep(wait_time)
                continue
            else:
                # Add a small delay to avoid rate limiting
                import time
                time.sleep(0.5)
                break
        else:
            # If we've exhausted all retries
            logger.error(f"Failed to get reference data after {max_retries} attempts due to rate limiting")
            # Return empty data instead of raising an exception
            reference_data = {"data": []}
        
        response.raise_for_status()
        
        reference_data = response.json()
        logger.info(f"Retrieved reference data with {len(reference_data.get('data', [])) if reference_data.get('data') else 0} references")
        
        # Process and format the data for visualization
        logger.info("Processing reference data")
        processed_data = process_reference_data(reference_data, paper_id)
        
        # Cache the result
        # logger.info("Caching reference data")
        # cache.set(cache_key, processed_data)
        
        return processed_data
    
    except Exception as e:
        logger.error(f"Error getting reference network: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting reference network: {str(e)}")

def process_citation_data(data: Dict[str, Any], root_id: str) -> Dict[str, Any]:
    """Process citation data into a visualization-friendly format"""
    logger.info("Processing citation data for visualization")
    nodes = []
    links = []
    
    # Process citations
    citations = data.get("data", [])
    logger.info(f"Processing {len(citations)} citations")
    for i, citation in enumerate(citations):
        # Check if citation data is valid
        if not citation or not isinstance(citation, dict):
            continue
            
        # Extract paper data from citation (it might be nested)
        paper_data = citation.get("citingPaper", citation)
        
        # Add cited paper
        paper_id = paper_data.get("paperId")
        if not paper_id:
            continue
            
        title = paper_data.get("title", "Unknown title")
        logger.info(f"Adding cited paper {i+1}: {title}")
        nodes.append({
            "id": paper_id,
            "cited_by_count": paper_data.get("citationCount", 0),
            "year": paper_data.get("year"),
            "title": title[:50] + ("..." if len(title) > 50 else ""),
            "type": "citation"
        })
        
        # Add link
        links.append({
            "source": root_id,
            "target": paper_id,
            "type": "citation"
        })
    
    logger.info(f"Finished processing citation data with {len(nodes)} nodes and {len(links)} links")
    return {
        "nodes": nodes,
        "links": links
    }

def process_reference_data(data: Dict[str, Any], root_id: str) -> Dict[str, Any]:
    """Process reference data into a visualization-friendly format"""
    logger.info("Processing reference data for visualization")
    nodes = []
    links = []
    
    # Process references
    references = data.get("data", [])
    if references is None:
        references = []
    logger.info(f"Processing {len(references)} references")
    for i, reference in enumerate(references):
        # Check if reference data is valid
        if not reference or not isinstance(reference, dict):
            continue
            
        # Extract paper data from reference (it might be nested)
        paper_data = reference.get("citedPaper", reference)
        
        # Add reference paper
        paper_id = paper_data.get("paperId")
        if not paper_id:
            continue
            
        title = paper_data.get("title", "Unknown title")
        logger.info(f"Adding reference paper {i+1}: {title}")
        nodes.append({
            "id": paper_id,
            "cited_by_count": paper_data.get("citationCount", 0),
            "year": paper_data.get("year"),
            "title": title[:50] + ("..." if len(title) > 50 else ""),
            "type": "reference"
        })
        
        # Add link
        links.append({
            "source": paper_id,
            "target": root_id,
            "type": "reference"
        })
    
    logger.info(f"Finished processing reference data with {len(nodes)} nodes and {len(links)} links")
    return {
        "nodes": nodes,
        "links": links
    }
