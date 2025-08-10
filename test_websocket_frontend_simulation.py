import asyncio
import websockets
import json
import time

async def simulate_frontend():
    uri = "ws://localhost:8000/ws/logs"
    try:
        # Connect to the WebSocket
        websocket = await websockets.connect(uri)
        print("Connected to WebSocket server")
        
        # Send a message to identify as frontend
        await websocket.send("Hello from frontend simulation")
        print("Sent frontend identification message")
        
        # Listen for messages for 60 seconds
        start_time = time.time()
        while time.time() - start_time < 60:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(message)
                timestamp = time.strftime('%H:%M:%S', time.localtime())
                print(f"[{timestamp}] Received: {data}")
                
                # If it's a ping message, respond with pong
                if data.get("type") == "ping":
                    print(f"[{timestamp}] Sending pong response")
                    await websocket.send(json.dumps({"type": "pong", "timestamp": int(time.time())}))
                    
            except asyncio.TimeoutError:
                # Send a periodic message to keep connection alive
                if int(time.time()) % 10 == 0:  # Send every 10 seconds
                    await websocket.send("Keep alive message from frontend")
                    print(f"[{timestamp}] Sent keep alive message")
                continue
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed by server")
                break
                
        # Close connection gracefully
        await websocket.close()
        print("Connection closed gracefully")
                    
    except Exception as e:
        print(f"Error connecting to WebSocket: {e}")

if __name__ == "__main__":
    print("Simulating frontend WebSocket connection...")
    asyncio.run(simulate_frontend())
