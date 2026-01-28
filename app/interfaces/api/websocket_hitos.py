from fastapi import WebSocket, WebSocketDisconnect, Depends, status, APIRouter
from fastapi.exceptions import WebSocketException
from sqlalchemy.orm import Session
from typing import Dict, Optional, Any, List
import json
import jwt
from datetime import datetime
import logging
import importlib
import asyncio

from app.config import settings
from app.infrastructure.db.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT settings from app config
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

# Try to dynamically import models from common project paths (best-effort)
def _try_import_model(candidates, class_name):
    for module_path in candidates:
        try:
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        except Exception:
            continue
    return None

UsuarioModel = _try_import_model(
    [
        "app.domain.entities.usuario",
        "app.infrastructure.entities.usuario",
        "app.domain.models.usuario",
        "app.models.usuario",
    ],
    "Usuario",
)

DepartamentoModel = _try_import_model(
    [
        "app.domain.entities.departamento",
        "app.infrastructure.entities.departamento",
        "app.domain.models.departamento",
        "app.models.departamento",
    ],
    "Departamento",
)

# WebSocket router
router = APIRouter(tags=["WebSockets"])

class ConnectionManager:
    """Manages active WebSocket connections grouped by department code"""
    
    def __init__(self):
        # Format: {cod_subdepar: {client_id: WebSocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self.connection_count = 0
    
    async def connect(self, websocket: WebSocket, cod_subdepar: str) -> str:
        """Connect a client to a specific department channel"""
        await websocket.accept()
        
        # Generate unique client ID
        client_id = f"client_{self.connection_count}"
        self.connection_count += 1
        
        # Initialize department if not exists
        if cod_subdepar not in self.active_connections:
            self.active_connections[cod_subdepar] = {}
        
        # Add connection to department
        self.active_connections[cod_subdepar][client_id] = websocket
        
        logger.info(f"Client {client_id} connected to department {cod_subdepar}")
        logger.info(f"Active connections: {sum(len(conns) for conns in self.active_connections.values())}")
        
        return client_id
    
    def disconnect(self, cod_subdepar: str, client_id: str) -> None:
        """Remove a client connection"""
        if cod_subdepar in self.active_connections and client_id in self.active_connections[cod_subdepar]:
            del self.active_connections[cod_subdepar][client_id]
            
            # Clean up empty department entries
            if not self.active_connections[cod_subdepar]:
                del self.active_connections[cod_subdepar]
                
            logger.info(f"Client {client_id} disconnected from department {cod_subdepar}")
            logger.info(f"Active connections: {sum(len(conns) for conns in self.active_connections.values())}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """Send a message to a specific client"""
        await websocket.send_text(message)
    
    async def broadcast(self, message: Any, cod_subdepar: str) -> None:
        """Broadcast a message to all clients in a department"""
        if cod_subdepar not in self.active_connections:
            logger.info(f"No active connections for department {cod_subdepar}")
            return
        
        # Convert dict to JSON string if needed
        if isinstance(message, dict):
            message = json.dumps(message)
        
        disconnected = []
        for client_id, connection in self.active_connections[cod_subdepar].items():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send message to client {client_id}: {e}")
                disconnected.append((cod_subdepar, client_id))
        
        # Clean up any failed connections
        for dept, client in disconnected:
            self.disconnect(dept, client)

# Create global connection manager instance
manager = ConnectionManager()


class DebounceBroadcaster:
    """
    Debounces rapid-fire events per subdepartment channel.

    - If multiple events arrive within `delay_ms`, they are buffered and sent as a single
      batch message: { tipo: "batch", count, events: [...], timestamp }
    - If only one event arrives within the window, the original single event is sent as-is
      to preserve backward compatibility.
    """

    def __init__(self, delay_ms: int = 200):
        self.delay = delay_ms / 1000.0
        self._buffers: Dict[str, List[Dict[str, Any]]] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    async def enqueue(self, cod_subdepar: str, payload: Dict[str, Any]):
        async with self._lock:
            # Initialize buffer list
            buf = self._buffers.setdefault(cod_subdepar, [])
            buf.append(payload)

            # Cancel previous pending flush for this channel
            task = self._tasks.get(cod_subdepar)
            if task and not task.done():
                task.cancel()

            # Schedule a new flush
            self._tasks[cod_subdepar] = asyncio.create_task(self._flush_after_delay(cod_subdepar))

    async def _flush_after_delay(self, cod_subdepar: str):
        try:
            await asyncio.sleep(self.delay)
            await self._flush_now(cod_subdepar)
        except asyncio.CancelledError:
            # Expected when a new event arrives before the debounce window ends
            return
        except Exception as e:
            logger.error(f"Debounce flush error for {cod_subdepar}: {e}")

    async def _flush_now(self, cod_subdepar: str):
        async with self._lock:
            items = self._buffers.get(cod_subdepar, [])
            self._buffers[cod_subdepar] = []
            # Clean task reference if this is the active task
            self._tasks.pop(cod_subdepar, None)

        if not items:
            return

        # Send single event as-is to maintain compatibility
        if len(items) == 1:
            await manager.broadcast(items[0], cod_subdepar)
            return

        # Build batch message
        batch = {
            "tipo": "batch",
            "count": len(items),
            "events": items,
            "timestamp": datetime.now().isoformat(),
        }
        await manager.broadcast(batch, cod_subdepar)


# Global debouncer instance
debouncer = DebounceBroadcaster(delay_ms=200)

async def get_current_user_from_token(
    token: Optional[str], db: Session = Depends(get_db)
) -> Any:
    """Validate JWT and (best-effort) user existence. Returns a dict with username."""
    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Token not provided")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        
        if not username:
            raise WebSocketException(code=4001, reason="Invalid authentication credentials")
        
    except jwt.PyJWTError:
        raise WebSocketException(code=4001, reason="Could not validate credentials")

    # Best-effort DB validation only if model is available
    if UsuarioModel is not None:
        user = db.query(UsuarioModel).filter(getattr(UsuarioModel, "username") == username).first()
        if user is None:
            raise WebSocketException(code=4001, reason="User not found")

    return {"username": username}

async def validate_department_access(
    cod_subdepar: str,
    user: Any,
    db: Session = Depends(get_db)
) -> None:
    """Best-effort department validation (skipped if model not found)."""
    if DepartamentoModel is None:
        return  # Skip validation if we can't import the model

    departamento = db.query(DepartamentoModel).filter(
        getattr(DepartamentoModel, "cod_subdepar") == cod_subdepar
    ).first()
    if not departamento:
        raise WebSocketException(code=4004, reason=f"Department {cod_subdepar} not found")
    # Optional: user-department permission check can be added here if models are available

@router.websocket("/api/admin/hitos-departamento/ws/{cod_subdepar}")
async def websocket_hitos_endpoint(
    websocket: WebSocket,
    cod_subdepar: str,
    db: Session = Depends(get_db),
):
    """WebSocket endpoint for real-time hito updates by department"""
    client_id: Optional[str] = None
    try:
        # Extract token from query params explicitly for WebSocket endpoints
        token = websocket.query_params.get("token")
        user = await get_current_user_from_token(token, db)

        # Validate department access (best-effort)
        await validate_department_access(cod_subdepar, user, db)

        # Accept connection and register client
        client_id = await manager.connect(websocket, cod_subdepar)

        # Welcome message
        await manager.send_personal_message(
            json.dumps(
                {
                    "tipo": "connected",
                    "message": f"Conectado a actualizaciones del departamento {cod_subdepar}",
                    "username": user.get("username"),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            websocket,
        )

        # Message handling loop
        while True:
            data = await websocket.receive_text()

            # Texto plano "ping" (compatibilidad)
            if data == "ping":
                await websocket.send_text("pong")
                continue

            # Intentar parsear JSON
            obj = None
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                # Mantener compatibilidad: eco de mensajes no JSON
                await websocket.send_text(f"Mensaje recibido: {data}")
                continue

            if not isinstance(obj, dict):
                await websocket.send_text(json.dumps({
                    "tipo": "warning",
                    "message": "Formato de mensaje no soportado"
                }))
                continue

            msg_type = obj.get("tipo")

            # Ping JSON
            if msg_type == "ping":
                await websocket.send_text(json.dumps({
                    "tipo": "pong",
                    "timestamp": datetime.now().isoformat(),
                }))
                continue

            # Difundir actualización de hito a todo el departamento
            if msg_type == "hito_actualizado":
                cliente_proceso_hito_id = obj.get("cliente_proceso_hito_id")
                nuevo_estado = obj.get("nuevo_estado")
                if not cliente_proceso_hito_id or not nuevo_estado:
                    await websocket.send_text(json.dumps({
                        "tipo": "error",
                        "message": "Campos requeridos: cliente_proceso_hito_id y nuevo_estado"
                    }))
                    continue

                # Enriquecer con usuario y timestamp
                if not obj.get("usuario"):
                    obj["usuario"] = user.get("username")
                if "timestamp" not in obj:
                    obj["timestamp"] = datetime.now().isoformat()

                # Asegurar el tipo correcto
                obj["tipo"] = "hito_actualizado"

                # Reenviar a todos los clientes del mismo departamento
                await manager.broadcast(obj, cod_subdepar)
                logger.info(
                    f"Broadcast hito_actualizado dept={cod_subdepar} id={cliente_proceso_hito_id} estado={nuevo_estado}"
                )
                continue

            # Tipo desconocido: advertencia al cliente
            await websocket.send_text(json.dumps({
                "tipo": "warning",
                "message": f"Tipo de mensaje no reconocido: {msg_type}",
            }))

    except WebSocketDisconnect:
        if client_id:
            manager.disconnect(cod_subdepar, client_id)
    except WebSocketException as e:
        try:
            await websocket.close(code=e.code, reason=str(e.reason))
        finally:
            logger.error(f"WebSocket error: {e.reason} (code: {e.code})")
            if client_id:
                manager.disconnect(cod_subdepar, client_id)
    except Exception:
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        finally:
            if client_id:
                manager.disconnect(cod_subdepar, client_id)

async def broadcast_hito_update(cod_subdepar: str, hito_data: dict):
    """
    Function to broadcast hito updates to all clients in a department.
    Call this function from other parts of the app when a hito is updated.
    
    Example usage:
    ```
    await broadcast_hito_update("221101", {
        "tipo": "hito_actualizado",
        "cliente_proceso_hito_id": 12345,
        "nuevo_estado": "Finalizado",
        "nombre_hito": "Entrega documentos",
        "observaciones": "Completado con éxito",
        "usuario_modificador": "jorge.varela",
        "timestamp": "2024-01-15T10:30:00"
    })
    ```
    """
    # Ensure timestamp is present
    if isinstance(hito_data, dict) and "timestamp" not in hito_data:
        hito_data["timestamp"] = datetime.now().isoformat()
    
    # Ensure type field is present for frontend handling
    if isinstance(hito_data, dict) and "tipo" not in hito_data:
        hito_data["tipo"] = "hito_actualizado"
    
    # Route through debouncer to coalesce rapid events
    await debouncer.enqueue(cod_subdepar, hito_data)
    logger.info(f"Queued hito update for department {cod_subdepar}")


async def broadcast_departament_event(cod_subdepar: str, tipo: str, data: Optional[dict] = None):
    """
    Generic helper to broadcast an event to all clients in a subdepartment.

    - Ensures consistent payload with 'tipo' and 'timestamp'.
    - Does not change existing logic or message handling for specific event types.

    Parameters:
    - cod_subdepar: Target subdepartment code (room/channel)
    - tipo: Event type string (e.g., 'proceso_actualizado', 'hito_actualizado')
    - data: Optional dict payload to include with the event
    """
    payload: Dict[str, Any] = {}
    if isinstance(data, dict):
        payload.update(data)
    # Ensure standard fields
    payload.setdefault("tipo", tipo)
    payload.setdefault("timestamp", datetime.now().isoformat())

    # Use debouncer to buffer frequent writes and reduce event spam
    await debouncer.enqueue(cod_subdepar, payload)
    logger.info(f"Queued event '{tipo}' to department {cod_subdepar}")
