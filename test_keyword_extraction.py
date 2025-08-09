import os
import sys
import logging
from openai import OpenAI

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_keywords(query: str, api_key: str) -> str:
    """Extract English keywords from Chinese query using LLM API"""
    logger.info(f"Extracting keywords from query: {query}")
    try:
        # Initialize OpenAI client with DashScope
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
        # Create prompt for keyword extraction
        prompt = f"""
        请将以下中文查询转换为适合学术搜索的英文关键词。只需要返回关键词，不需要其他解释。
        
        中文查询: {query}
        
        英文关键词:
        """
        
        # Call LLM API
        completion = client.chat.completions.create(
            model="qwen-plus",
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

def test_keyword_extraction():
    """Test the keyword extraction function"""
    try:
        # Get API key from environment
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            print("Error: DASHSCOPE_API_KEY not found in environment variables")
            return
            
        # Test cases
        test_queries = [
            "机器学习在医疗诊断中的应用",
            "深度学习与自然语言处理",
            "人工智能在金融领域的最新进展",
            "计算机视觉技术研究",
            "神经网络优化算法"
        ]
        
        print("Testing keyword extraction function:")
        print("=" * 50)
        
        for query in test_queries:
            print(f"Chinese query: {query}")
            keywords = extract_keywords(query, api_key)
            print(f"Extracted keywords: {keywords}")
            print("-" * 30)
            
    except Exception as e:
        logger.error(f"Error testing keyword extraction: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_keyword_extraction()
