import asyncio
import websockets
import json
import time

async def test_websocket():
    uri = "ws://localhost:8000/ws/logs"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            
            # Listen for 10 seconds
            start_time = time.time()
            while time.time() - start_time < 10:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    timestamp = time.strftime('%H:%M:%S', time.localtime())
                    if data.get("type") == "log":
                        print(f"[{timestamp}] LOG: {data.get('message')}")
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed")
                    break
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
