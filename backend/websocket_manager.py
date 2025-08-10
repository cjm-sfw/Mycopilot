import asyncio
import json
import logging
import time
from typing import List

# Configure logging
logger = logging.getLogger(__name__)

# Store active WebSocket connections
active_connections: List = []

async def broadcast_log(message: str):
    """Broadcast log message to all active WebSocket connections"""
    timestamp = time.strftime('%H:%M:%S', time.localtime())
    # Create a copy of active_connections to avoid modification during iteration
    connections = active_connections.copy()
    disconnected_connections = []
    
    for connection in connections:
        try:
            await connection.send_text(json.dumps({
                "type": "log",
                "message": message,
                "timestamp": timestamp
            }))
        except Exception as e:
            logger.error(f"Error broadcasting log: {str(e)}")
            # Mark connection for removal
            disconnected_connections.append(connection)
    
    # Remove disconnected connections
    for connection in disconnected_connections:
        if connection in active_connections:
            active_connections.remove(connection)

def log_and_send(message: str):
    """Log a message and send it to all active WebSocket connections"""
    # Log the message
    logger.info(message)
    
    # Broadcast the message immediately using asyncio
    try:
        # Try to get the running event loop
        try:
            loop = asyncio.get_running_loop()
            # Schedule the broadcast to run soon
            loop.create_task(broadcast_log(message))
        except RuntimeError:
            # No event loop running, run the broadcast directly
            asyncio.run(broadcast_log(message))
    except Exception as e:
        logger.error(f"Error broadcasting message: {str(e)}")
