import logging
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
# Add the parent directory to the path so we can import backend modules
import sys
import os
import asyncio
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import search, graph
from backend.config import settings
from backend.websocket_manager import active_connections, broadcast_log
import uvicorn
import json

# Configure logging with timestamp format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Scholar Assistant API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
# Use absolute paths to avoid directory issues
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(current_dir, "..", "frontend")
static_dir = os.path.join(frontend_dir, "static")
templates_dir = os.path.join(frontend_dir, "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Include API routers
app.include_router(search.router)
app.include_router(graph.router)

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for real-time log streaming"""
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket connection established. Total connections: {len(active_connections)}")
    
    # Send a test log message to the newly connected client
    try:
        await websocket.send_text(json.dumps({
            "type": "log",
            "message": "WebSocket connection established successfully",
            "timestamp": time.strftime('%H:%M:%S', time.localtime())
        }))
    except Exception as e:
        logger.error(f"Error sending test message: {str(e)}")
    
    try:
        while True:
            # Wait for a message from the client (with a timeout)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Process received data if needed
                try:
                    message = json.loads(data)
                    if message.get("type") == "pong":
                        # Received pong response, connection is alive
                        pass
                except json.JSONDecodeError:
                    # Not a JSON message, ignore
                    pass
            except asyncio.TimeoutError:
                # Send a ping message to keep the connection alive
                await websocket.send_text(json.dumps({"type": "ping", "timestamp": int(time.time())}))
                continue
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Total connections: {len(active_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Total connections: {len(active_connections)}")

# Custom logging handler to broadcast logs
class WebSocketLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        # Use the queue-based approach for sending logs
        from backend.websocket_manager import log_and_send
        log_and_send(log_entry)

# Add the custom handler to all relevant loggers
search_logger = logging.getLogger("backend.api.search")
search_logger.addHandler(WebSocketLogHandler())

graph_logger = logging.getLogger("backend.api.graph")
graph_logger.addHandler(WebSocketLogHandler())

main_logger = logging.getLogger(__name__)
main_logger.addHandler(WebSocketLogHandler())

@app.get("/graph", response_class=HTMLResponse)
async def graph_page():
    """Serve the graph visualization page"""
    logger.info("Graph visualization page accessed")
    return templates.TemplateResponse("graph.html", {"request": {}})

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to Scholar Assistant API"}

@app.post("/api/chat")
async def chat(message: dict):
    """Handle chat messages from the frontend"""
    logger.info(f"Chat endpoint accessed with message: {message}")
    # Import the process_message function from frontend
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from frontend.app import process_message
    
    result = process_message(message.get("message", ""))
    logger.info("Chat message processed successfully")
    return result

@app.get("/api/export/search/{query}")
async def export_search(query: str):
    """Export search results to JSON"""
    logger.info(f"Export search endpoint accessed with query: {query}")
    try:
        from backend.api.search import search_papers
        # Call the search_papers function directly
        result = await search_papers(query)
        logger.info("Search export completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error exporting search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting search: {str(e)}")

@app.get("/api/export/graph/{paper_id}")
async def export_graph(paper_id: str):
    """Export graph data to JSON"""
    logger.info(f"Export graph endpoint accessed with paper_id: {paper_id}")
    try:
        from backend.api.graph import get_citations, get_references
        # Call the get_citations and get_references functions directly
        citations = await get_citations(paper_id)
        references = await get_references(paper_id)
        
        logger.info("Graph export completed successfully")
        return {
            "citations": citations,
            "references": references
        }
    except Exception as e:
        logger.error(f"Error exporting graph: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting graph: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting Scholar Assistant API server")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
