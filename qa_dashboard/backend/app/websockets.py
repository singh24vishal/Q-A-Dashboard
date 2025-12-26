import websockets
import asyncio

connected_clients = []

async def websocket_handler(websocket, path):
    connected_clients.append(websocket)
    try:
        while True:
            data = await websocket.recv()
            for client in connected_clients:
                if client != websocket:
                    await client.send(data)
    except websockets.exceptions.ConnectionClosed:
        connected_clients.remove(websocket)
