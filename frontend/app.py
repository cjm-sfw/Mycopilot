import gradio as gr
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_message(message: str) -> dict:
    """Process user message and return appropriate response"""
    logger.info(f"Processing message: {message}")
    message = message.strip().lower()
    logger.info(f"Lowercased message: {message}")
    
    if message.startswith("search "):
        # Handle paper search
        query = message[7:]
        logger.info(f"Search query: {query}")
        try:
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            logger.info(f"Making request to http://localhost:8000/search/papers?query={encoded_query}&max_results=50")
            response = requests.get(f"http://localhost:8000/search/papers?query={encoded_query}&max_results=50")
            logger.info(f"Response status code: {response.status_code}")
            data = response.json()
            logger.info(f"Search data received: {data}")
            
            # Format search results
            result_text = f"Found {len(data['results'])} papers related to '{query}':\n\n"
            for i, paper in enumerate(data['results'], 1):
                result_text += f"{i}. **{paper['title']}**\n"
                result_text += f"   Year: {paper['year'] or 'N/A'}\n"
                result_text += f"   Citations: {paper['cited_by_count']}\n"
                result_text += f"   Abstract: {paper['abstract'] or 'N/A'}\n"
                result_text += f"   [Link]({paper['link']})\n\n"
            
            result_text += "\nType 'graph [paper title]' to visualize a knowledge graph for any paper."
            
            logger.info(f"result_text: {result_text}")
            
            return {"response": result_text}
        
        except Exception as e:
            return {"response": f"Error searching for papers: {str(e)}"}
    
    elif message.startswith("graph "):
        # Handle graph visualization
        title = message[5:]
        try:
            # Search for the paper to get its ID
            import urllib.parse
            encoded_title = urllib.parse.quote(title)
            search_response = requests.get(f"http://localhost:8000/search/papers?query={encoded_title}&max_results=1")
            search_data = search_response.json()
            
            if not search_data['results']:
                return {"response": f"No paper found with title '{title}'"}
            
            paper = search_data['results'][0]
            paper_id = paper.get('id') or paper.get('paperId')
            
            if not paper_id:
                return {"response": f"Could not find paper ID for '{title}'"}
            
            # Get citation and reference networks
            citation_response = requests.get(f"http://localhost:8000/graph/citations/{paper_id}")
            reference_response = requests.get(f"http://localhost:8000/graph/references/{paper_id}")
            
            citation_data = citation_response.json()
            reference_data = reference_response.json()
            
            # Combine the graph data
            # Create a set to track unique node IDs
            node_ids = set()
            combined_nodes = []
            combined_links = []
            
            # Add root paper node
            root_node = {
                "id": paper_id,
                "type": "root",
                "title": paper.get("title", title),
                "cited_by_count": paper.get("cited_by_count", 0),
                "year": paper.get("year")
            }
            combined_nodes.append(root_node)
            node_ids.add(paper_id)
            
            # Add citation nodes and links
            for node in citation_data.get("nodes", []):
                if node["id"] not in node_ids:
                    combined_nodes.append(node)
                    node_ids.add(node["id"])
            
            for link in citation_data.get("links", []):
                combined_links.append(link)
            
            # Add reference nodes and links
            for node in reference_data.get("nodes", []):
                if node["id"] not in node_ids:
                    combined_nodes.append(node)
                    node_ids.add(node["id"])
            
            for link in reference_data.get("links", []):
                combined_links.append(link)
            
            combined_graph = {
                "nodes": combined_nodes,
                "links": combined_links
            }
            
            return {
                "response": f"Visualizing knowledge graph for paper: {citation_data.get('title', title)}",
                "graph_data": combined_graph
            }
        
        except Exception as e:
            return {"response": f"Error generating graph: {str(e)}"}
    
    elif message == "help":
        # Show help information
        help_text = """
        # Scholar Assistant Help
        
        ## Available Commands:
        
        1. **search [topic]** - Search for academic papers on a topic
           Example: "search machine learning in healthcare"
        
        2. **graph [paper title]** - Visualize a knowledge graph for a paper
           Example: "graph Deep Learning for Medical Image Analysis"
        
        3. **help** - Show this help information
        
        ## Features:
        
        - Search for academic papers using natural language queries
        - Visualize citation and reference networks as interactive graphs
        - Explore paper details including abstracts, authors, and publication year
        - Save and export search results and knowledge graphs
        
        Type a command to get started!
        """
        return {"response": help_text}
    
    else:
        # Default response for unrecognized commands
        return {
            "response": "Welcome to Scholar Assistant! Type 'help' to see available commands.\n\n"
                        "I can help you search for academic papers and visualize knowledge graphs of citation networks.\n\n"
                        "Try searching for a topic or asking for help to get started!"
        }


# Create Gradio interface
def create_interface():
    logger.info("Creating Gradio interface")
    def chat_interface(message, history, additional_inputs=None):
        logger.info(f"Chat interface received message: {message}")
        # Use the process_message function directly instead of making an API call
        try:
            result = process_message(message)
            if "graph_data" in result:
                # For now, just return the text response
                # In a future implementation, we could handle graph visualization differently
                return result["response"]
            else:
                return result["response"]
        except Exception as e:
            logger.error(f"Error in chat interface: {str(e)}")
            return f"Error: {str(e)}"

    interface = gr.ChatInterface(
        fn=chat_interface,
        chatbot=gr.Chatbot(
            bubble_full_width=False,
            render="html"
        ),
        additional_inputs_accordion=gr.Accordion("Search Options", open=False),
        additional_inputs=[gr.Textbox(label="Search Query", placeholder="Enter your search query...")]
    )
    
    return interface

if __name__ == "__main__":
    # Run the Gradio interface
    import uvicorn
    app = create_interface()
    app.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=7860
    )
