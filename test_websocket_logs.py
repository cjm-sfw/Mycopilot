import asyncio
import websockets
import json
import time

async def test_websocket_logs():
    uri = "ws://localhost:8000/ws/logs"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            print("Listening for messages (press Ctrl+C to stop)...")
            
            # Listen for messages
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    timestamp = time.strftime('%H:%M:%S', time.localtime())
                    print(f"[{timestamp}] Received: {data}")
                    
                    if data.get("type") == "log":
                        print(f"[{timestamp}] LOG: {data.get('message')}")
                    elif data.get("type") == "ping":
                        print(f"[{timestamp}] PING received")
                        # Send pong response
                        await websocket.send(json.dumps({"type": "pong", "timestamp": int(time.time())}))
                        
                except asyncio.TimeoutError:
                    # Send a ping to keep connection alive
                    await websocket.send(json.dumps({"type": "ping", "timestamp": int(time.time())}))
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed")
                    break
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_logs())
