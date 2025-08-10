import asyncio
import websockets
import json
import time

async def test_websocket_connection():
    uri = "ws://localhost:8000/ws/logs"
    try:
        # Connect to the WebSocket
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Listen for messages
            for i in range(10):  # Listen for 10 messages or 30 seconds
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(message)
                    timestamp = time.strftime('%H:%M:%S', time.localtime())
                    print(f"[{timestamp}] Received: {data}")
                    
                    # If it's a ping message, respond with pong
                    if data.get("type") == "ping":
                        print(f"[{timestamp}] Sending pong response")
                        await websocket.send(json.dumps({"type": "pong", "timestamp": int(time.time())}))
                        
                except asyncio.TimeoutError:
                    print("No message received within timeout period")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed by server")
                    break
                    
    except Exception as e:
        print(f"Error connecting to WebSocket: {e}")

if __name__ == "__main__":
    print("Testing WebSocket connection...")
    asyncio.run(test_websocket_connection())
