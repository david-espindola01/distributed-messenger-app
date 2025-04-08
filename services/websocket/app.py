# services/websocket/app.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import uvicorn
import json

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            if connection.client_state.value == 1:  # WEBSOCKET_STATE.OPEN == 1
                await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Opcional: leer query params, ej. user_id
    user_id = websocket.query_params.get("user_id", None)
    await manager.connect(websocket)
    print(f"Usuario conectado: {user_id}")

    try:
        while True:
            data = await websocket.receive_text()
            # Se espera que el cliente envíe un JSON con campos de chat
            message_data = json.loads(data)

            # Lógica para decidir a quién reenviar (ej: difundir a todos)
            await manager.broadcast(json.dumps(message_data))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Usuario desconectado: {user_id}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
