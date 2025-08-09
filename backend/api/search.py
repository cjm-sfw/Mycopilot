import requests
import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from backend.cache.redis_cache import cache
from backend.config import settings
import serpapi
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

# Semantic Scholar API configuration
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"

@router.get("/papers")
async def search_papers(query: str, max_results: int = 50) -> Dict[str, Any]:
    """
    Search for academic papers using Google Scholar API via SerpAPI
    and enrich the results with information from Semantic Scholar API.
    """
    logger.info(f"Starting search for papers with query: {query}, max_results: {max_results}")
    try:
        # Extract English keywords from Chinese query if needed
        english_query = extract_keywords(query)
        logger.info(f"Using English query for search: {english_query}")
        
        # Check cache first using the English query
        # cache_key = f"search:{english_query}:{max_results}"
        # logger.info(f"Checking cache for key: {cache_key}")
        # cached_result = cache.get(cache_key)
        # if cached_result:
        #     logger.info("Returning cached result")
        #     return cached_result
        
        # Google Scholar search using SerpAPI
        logger.info("Performing Google Scholar search via SerpAPI")
        params = {
            "engine": "google_scholar",
            "q": english_query,
            "api_key": settings.serpapi_key,
            "num": max_results
        }


        client = serpapi.Client(api_key=settings.serpapi_key)
        results = client.search(params)

        # Save the results to local
        import json
        import os
        from datetime import datetime
        
        # Create a directory for saving results if it doesn't exist
        save_dir = "search_results"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # Create a filename based on the query and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{save_dir}/search_results_{english_query.replace(' ', '_')}_{timestamp}.json"
        
        # Convert SerpResults to a serializable dictionary
        serializable_results = {}
        if hasattr(results, '__dict__'):
            # If results is a SerpResults object, convert it to dict
            serializable_results = results.as_dict()
        else:
            # If results is already a dict, use it directly
            serializable_results = dict(results)
        
        # Save the raw results
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2)
            logger.info(f"Search results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving search results: {str(e)}")
        

        organic_results = results.get("organic_results", [])
        logger.info(f"Google Scholar search returned {len(organic_results)} results")
        
        # Process results and enrich with Semantic Scholar data
        processed_results = []
        for i, result in enumerate(organic_results):
            logger.info(f"Processing result {i+1}: {result.get('title', 'Unknown title')}")
            paper_info = {
                "title": result.get("title"),
                "link": result.get("link"),
                "snippet": result.get("snippet"),
                "source": result.get("source"),
                "id": result.get("result_id"),
                "cited_by_count": 0,
                "year": None,
                "authors": [],
                "abstract": result.get("snippet")
            }
            
            # Get more detailed information from Semantic Scholar API
            semantic_scholar_id = None
            if settings.serpapi_key and result.get("title"):
                logger.info(f"Fetching Semantic Scholar data for: {result['title']}")
                semantic_data = get_semantic_scholar_data(result["title"])
                if semantic_data:
                    logger.info("Successfully retrieved Semantic Scholar data")
                    semantic_scholar_id = semantic_data.get("paperId")
                    paper_info.update({
                        "title": semantic_data.get("title", paper_info["title"]),
                        "abstract": semantic_data.get("abstract", paper_info["abstract"]),
                        "year": semantic_data.get("year"),
                        "cited_by_count": semantic_data.get("citationCount", 0),
                        "authors": [author["name"] for author in semantic_data.get("authors", [])],
                        "paperId": semantic_scholar_id  # Add Semantic Scholar ID
                    })
                else:
                    logger.info("No Semantic Scholar data found for this paper")
            
            # If we found a Semantic Scholar ID, use it; otherwise skip this paper
            if semantic_scholar_id:
                paper_info["id"] = semantic_scholar_id
                processed_results.append(paper_info)
            else:
                logger.info("Skipping paper due to missing Semantic Scholar ID")
        
        # Cache the results
        # logger.info("Caching search results")
        # cache.set(cache_key, {"results": processed_results})
        
        logger.info(f"Search completed successfully with {len(processed_results)} results")
        return {"results": processed_results}
    
    except Exception as e:
        logger.error(f"Error searching for papers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching for papers: {str(e)}")

def extract_keywords(query: str) -> str:
    """Extract English keywords from Chinese query using LLM API"""
    logger.info(f"Extracting keywords from query: {query}")
    try:
        # Initialize OpenAI client with DashScope
        client = OpenAI(
            api_key=settings.dashscope_api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
        # Create prompt for keyword extraction
        prompt = f"""
        请将以下中文查询转换为适合学术搜索的英文关键词。只需要返回3个关键词，不需要其他解释。
        
        中文查询: {query}
        
        英文关键词:
        """
        
        # Call LLM API
        completion = client.chat.completions.create(
            model="qwen-plus-2025-07-28",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts English keywords from Chinese queries for academic search."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=100,
        )
        
        # Extract keywords from response
        keywords = completion.choices[0].message.content.strip()
        logger.info(f"Extracted keywords: {keywords}")
        return keywords
    
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        # If keyword extraction fails, return the original query
        return query

def get_semantic_scholar_data(title: str) -> Optional[Dict[str, Any]]:
    """Get detailed paper information from Semantic Scholar API"""
    logger.info(f"Getting Semantic Scholar data for title: {title}")
    try:
        headers = {"User-Agent": "ScholarAssistant/1.0"}
        
        # Search for the paper by title
        search_url = f"{SEMANTIC_SCHOLAR_API}/paper/search"
        params = {
            "query": title,
            "limit": 1,
            "fields": "title,abstract,year,authors,citationCount,paperId"
        }
        logger.info(f"Making request to Semantic Scholar search API: {search_url}")
        
        response = requests.get(search_url, params=params, headers=headers)
        # Handle rate limiting
        if response.status_code == 429:
            logger.warning("Rate limit exceeded. Waiting for 5 seconds before retry...")
            import time
            time.sleep(5)
            # Retry once
            response = requests.get(search_url, params=params, headers=headers)
        
        response.raise_for_status()
        
        search_results = response.json()
        logger.info(f"Semantic Scholar search returned {search_results.get('total', 0)} results")
        if search_results.get("total") == 0 or not search_results.get("data"):
            logger.info("No results found in Semantic Scholar")
            return None
        
        paper_data = search_results["data"][0]
        logger.info(f"Found paper ID: {paper_data['paperId']}")
        
        # Return the data directly since we already requested all needed fields
        logger.info("Successfully retrieved detailed paper information")
        return paper_data
    
    except Exception as e:
        logger.error(f"Error getting Semantic Scholar data: {str(e)}")
        return None
