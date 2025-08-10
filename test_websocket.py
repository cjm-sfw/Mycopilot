import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/logs"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Listen for messages
            async def listen():
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        if data.get("type") == "log":
                            print(f"[{data.get('timestamp')}] {data.get('message')}")
                    except Exception as e:
                        print(f"Error receiving message: {e}")
                        break
            
            # Start listening
            listen_task = asyncio.create_task(listen())
            
            # Wait for a while to receive messages
            await asyncio.sleep(10)
            
            # Cancel the listen task
            listen_task.cancel()
            
    except Exception as e:
        print(f"Error connecting to WebSocket: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
