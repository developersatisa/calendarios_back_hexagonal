# app/main.py

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# Carga las variables de entorno (DATABASE_URL, FILE_STORAGE_ROOT, etc.)
from app.config import settings

# Rutas de autenticación (login, refresh, etc.)
from app.interfaces.api import auth_routes
# Guard que protege tus endpoints con JWT / API-Key
from app.interfaces.api.security.auth import get_current_user

# WebSocket integration
from app.interfaces.api.websocket_integration import configure_websockets

# Importa todos tus routers de la versión 1
from app.interfaces.api.v1.endpoints import (
    plantilla,
    proceso,
    hito,
    cliente,
    cliente_proceso,
    cliente_proceso_hito,
    cliente_proceso_hito_cumplimiento,
    plantilla_proceso,
    proceso_hito_maestro,
    admin_api_cliente,
    metadato,
    metadatos_area,
    documento,
    documentos_cumplimiento,
    documental_categoria,
    documental_documentos,
    documento_metadato,
    subdepar,
    metricas,
    auditoria_calendarios,
    admin_hitos_departamento,
    exportar_status_hitos,
    exportar_status_hitos,
    status_todos_clientes,
    persona,
    api_rol
)


# Orígenes permitidos para CORS
origins = [
    "http://localhost:5174",
    "http://localhost:3000",      # frontend local
    "http://127.0.0.1:3000",
    "http://10.150.22.15:5174",   # IP local frontend
    "http://10.150.22.15:5173",   # IP local frontend
    "http://10.150.22.15:8050",   # IP local backend
    "http://10.150.22.15:8049",
    "http://gestorcalendarios.test",
    "https://gestorcalendarios.es",
    "https://82.223.35.103:8022",  # IP del servidor
    "https://localhost:8022",
    "http://gestorcalendarios.es",
    "http://82.223.35.103:8022",  # IP del servidor
    "http://localhost:8022",
    "https://gestorcalendarios.atisa.es"
    # "https://tu-front-en-produccion.com",  <-- producción
]

app = FastAPI(
    title="API de Procesos de Clientes",
    version="1.0.0",
    root_path="/api",  # Importante cuando está detrás de un proxy
)

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],   # ["GET","POST",...] si quieres restringir
    allow_headers=["*"],   # ["x_api_key","Content-Type"] si quieres restringir
)

# --- Routers públicos (login, signup, etc.) ---
app.include_router(auth_routes.router)

# --- Routers de administración (sin autenticación JWT/API-Key) ---
app.include_router(admin_api_cliente.router)

# --- Routers v1 protegidos por get_current_user ---
app.include_router(plantilla.router,            dependencies=[Depends(get_current_user)])
app.include_router(proceso.router,              dependencies=[Depends(get_current_user)])
app.include_router(hito.router,                 dependencies=[Depends(get_current_user)])
app.include_router(cliente.router,              dependencies=[Depends(get_current_user)])
app.include_router(cliente_proceso.router,      dependencies=[Depends(get_current_user)])
app.include_router(cliente_proceso.router_calendario, dependencies=[Depends(get_current_user)])
app.include_router(cliente_proceso_hito.router, dependencies=[Depends(get_current_user)])
app.include_router(cliente_proceso_hito_cumplimiento.router, dependencies=[Depends(get_current_user)])
app.include_router(plantilla_proceso.router,    dependencies=[Depends(get_current_user)])
app.include_router(proceso_hito_maestro.router, dependencies=[Depends(get_current_user)])
app.include_router(metadato.router,             dependencies=[Depends(get_current_user)])
app.include_router(documento.router,            dependencies=[Depends(get_current_user)])
app.include_router(documentos_cumplimiento.router, dependencies=[Depends(get_current_user)])
app.include_router(documental_categoria.router, dependencies=[Depends(get_current_user)])
app.include_router(documental_documentos.router, dependencies=[Depends(get_current_user)])
app.include_router(documento_metadato.router,   dependencies=[Depends(get_current_user)])
app.include_router(metadatos_area.router,       dependencies=[Depends(get_current_user)])
app.include_router(subdepar.router,             dependencies=[Depends(get_current_user)])
app.include_router(metricas.router,             dependencies=[Depends(get_current_user)])
app.include_router(auditoria_calendarios.router, dependencies=[Depends(get_current_user)])
app.include_router(admin_hitos_departamento.router, dependencies=[Depends(get_current_user)])
app.include_router(exportar_status_hitos.router, dependencies=[Depends(get_current_user)])
app.include_router(status_todos_clientes.router, dependencies=[Depends(get_current_user)])
app.include_router(persona.router,              dependencies=[Depends(get_current_user)])
app.include_router(api_rol.router,            dependencies=[Depends(get_current_user)])


configure_websockets(app)

# --- Health check opcional ---
@app.get("/health", tags=["Status"])
def health_check():
    return {
        "status": "ok",
        "environment": settings.ENV_NAME if hasattr(settings, "ENV_NAME") else "default",
        "storage_root": settings.FILE_STORAGE_ROOT,
    }
