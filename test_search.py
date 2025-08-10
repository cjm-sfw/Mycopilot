import requests
import time

def test_search():
    # Make a request to the search endpoint
    url = "http://localhost:8000/search/papers"
    params = {
        "query": "machine learning",
        "max_results": 5
    }
    
    try:
        print("Making search request...")
        response = requests.get(url, params=params)
        print(f"Search response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('results', []))} results")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error making search request: {e}")

if __name__ == "__main__":
    test_search()
