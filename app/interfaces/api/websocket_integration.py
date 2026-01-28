from fastapi import FastAPI, Request
from starlette.concurrency import run_in_threadpool
import logging
from typing import Optional, Dict, Any, List

from sqlalchemy import text, bindparam
from sqlalchemy.orm import Session

from app.infrastructure.db.database import SessionLocal

def configure_websockets(app: FastAPI):
    """Configure WebSocket routes on the main FastAPI application"""
    logger = logging.getLogger(__name__)
    try:
        # Import lazily to avoid import-time failures
        from app.interfaces.api.websocket_hitos import (
            router as websocket_router,
            broadcast_departament_event,
        )
    except ModuleNotFoundError as e:
        logger.warning(f"WebSocket routes not loaded: {e}")
        return
    except Exception as e:
        logger.error(f"Error loading WebSocket routes: {e}")
        return

    app.include_router(websocket_router)

    async def _emit_event(cod_subdepar: str, tipo: str, data: Optional[Dict[str, Any]] = None):
        try:
            await broadcast_departament_event(cod_subdepar, tipo, data or {})
        except Exception as e:
            logger.error(f"Failed to broadcast event '{tipo}' to {cod_subdepar}: {e}")

    def _get_db_session() -> Session:
        return SessionLocal()

    def _infer_subdepar_for_cph(session: Session, cph_id: int) -> Optional[str]:
        """Infer codSubDePar from a cliente_proceso_hito id."""
        sql = text(
            """
            SELECT sd.codSubDePar AS cod
            FROM [ATISA_Input].dbo.cliente_proceso_hito cph
            JOIN [ATISA_Input].dbo.cliente_proceso cp ON cp.id = cph.cliente_proceso_id
            JOIN [ATISA_Input].dbo.clienteSubDePar csd ON csd.id = cp.cliente_id
            JOIN [ATISA_Input].dbo.SubDePar sd ON sd.codSubDePar = csd.codSubDePar
            WHERE cph.id = :id
            """
        )
        row = session.execute(sql, {"id": cph_id}).mappings().first()
        return row["cod"] if row else None

    def _infer_subdepar_for_cp(session: Session, cp_id: int) -> Optional[str]:
        sql = text(
            """
            SELECT sd.codSubDePar AS cod
            FROM [ATISA_Input].dbo.cliente_proceso cp
            JOIN [ATISA_Input].dbo.clienteSubDePar csd ON csd.id = cp.cliente_id
            JOIN [ATISA_Input].dbo.SubDePar sd ON sd.codSubDePar = csd.codSubDePar
            WHERE cp.id = :id
            """
        )
        row = session.execute(sql, {"id": cp_id}).mappings().first()
        return row["cod"] if row else None

    def _infer_subdepar_for_proceso(session: Session, proceso_id: int) -> List[str]:
        """
        Get all subdepartments impacted by a proceso via its cliente_proceso relations.
        """
        sql = text(
            """
            SELECT DISTINCT sd.codSubDePar AS cod
            FROM [ATISA_Input].dbo.cliente_proceso cp
            JOIN [ATISA_Input].dbo.clienteSubDePar csd ON csd.id = cp.cliente_id
            JOIN [ATISA_Input].dbo.SubDePar sd ON sd.codSubDePar = csd.codSubDePar
            WHERE cp.proceso_id = :id
            """
        )
        rows = session.execute(sql, {"id": proceso_id}).mappings().all()
        return [r["cod"] for r in rows]

    def _infer_subdepar_for_hito(session: Session, hito_id: int) -> List[str]:
        sql = text(
            """
            SELECT DISTINCT sd.codSubDePar AS cod
            FROM [ATISA_Input].dbo.cliente_proceso_hito cph
            JOIN [ATISA_Input].dbo.cliente_proceso cp ON cp.id = cph.cliente_proceso_id
            JOIN [ATISA_Input].dbo.clienteSubDePar csd ON csd.id = cp.cliente_id
            JOIN [ATISA_Input].dbo.SubDePar sd ON sd.codSubDePar = csd.codSubDePar
            WHERE cph.hito_id = :id
            """
        )
        rows = session.execute(sql, {"id": hito_id}).mappings().all()
        return [r["cod"] for r in rows]

    def _fetch_cph_updates_for_hito(session: Session, hito_id: int) -> List[Dict[str, Any]]:
        """Fetch cliente_proceso_hito records impacted by a hito update, with their estado and subdepar."""
        sql = text(
            """
            SELECT 
                cph.id         AS cph_id,
                cph.estado     AS estado,
                cph.hito_id    AS hito_id,
                sd.codSubDePar AS cod
            FROM [ATISA_Input].dbo.cliente_proceso_hito cph
            JOIN [ATISA_Input].dbo.cliente_proceso cp ON cp.id = cph.cliente_proceso_id
            JOIN [ATISA_Input].dbo.clienteSubDePar csd ON csd.id = cp.cliente_id
            JOIN [ATISA_Input].dbo.SubDePar sd ON sd.codSubDePar = csd.codSubDePar
            WHERE cph.hito_id = :id
            """
        )
        return [dict(r) for r in session.execute(sql, {"id": hito_id}).mappings().all()]

    def _fetch_cph_by_id(session: Session, cph_id: int) -> Optional[Dict[str, Any]]:
        sql = text(
            """
            SELECT 
                cph.id         AS cph_id,
                cph.estado     AS estado,
                cph.hito_id    AS hito_id,
                sd.codSubDePar AS cod
            FROM [ATISA_Input].dbo.cliente_proceso_hito cph
            JOIN [ATISA_Input].dbo.cliente_proceso cp ON cp.id = cph.cliente_proceso_id
            JOIN [ATISA_Input].dbo.clienteSubDePar csd ON csd.id = cp.cliente_id
            JOIN [ATISA_Input].dbo.SubDePar sd ON sd.codSubDePar = csd.codSubDePar
            WHERE cph.id = :id
            """
        )
        row = session.execute(sql, {"id": cph_id}).mappings().first()
        return dict(row) if row else None

    @app.middleware("http")
    async def websocket_emit_on_write(request: Request, call_next):
        """
        Middleware that emits websocket updates on POST/PUT for specific resources,
        broadcasting only to sockets joined to the affected subdepartment(s).

        Targets:
        - Procesos (POST /procesos, PUT /procesos/{id})
        - Hitos (POST /hitos, PUT /hitos/{id})
        - Proceso-Hitos (POST/DELETE /proceso-hitos[/{id}])
        - Cliente-Proceso (POST /cliente-procesos, PUT-like operations if added)
        - Cliente-Proceso-Hito (POST/PUT /cliente-proceso-hitos)
        """

        method = request.method.upper()
        path = request.url.path

        # Fast-path for non-writes
        is_write = method in ("POST", "PUT")
        if not is_write:
            return await call_next(request)

        # Buffer body to allow both us and downstream handlers to read it
        try:
            raw_body: bytes = await request.body()
        except Exception:
            raw_body = b""

        # Re-inject body for downstream
        async def receive():
            return {"type": "http.request", "body": raw_body, "more_body": False}
        try:
            request._receive = receive  # type: ignore[attr-defined]
        except Exception:
            pass

        # Try parse JSON body for POST routes
        parsed_body = None
        if raw_body:
            try:
                import json as _json
                parsed_body = _json.loads(raw_body)
            except Exception:
                parsed_body = None

        response = await call_next(request)

        # Only emit if successful change (2xx)
        if response.status_code < 200 or response.status_code >= 300:
            return response

        # Determine entity type and id(s) to compute affected subdepartments
        try:
            # Procesos
            if path.startswith("/procesos"):
                # POST /procesos -> new proceso referenced by multiple subdepars via future links
                if method == "POST":
                    # No direct subdepar; emit nothing to avoid noisy broadcasts
                    return response
                # PUT /procesos/{id}
                import re
                m = re.match(r"^/procesos/(\d+)$", path)
                if m:
                    proceso_id = int(m.group(1))
                    session = _get_db_session()
                    try:
                        subdeps = await run_in_threadpool(_infer_subdepar_for_proceso, session, proceso_id)
                    finally:
                        session.close()
                    # Expandir por CIF (misma lógica del GET): incluir todos los subdeps asignados al CIF
                    session_cif = _get_db_session()
                    try:
                        sql_cifs = text(
                            """
                            SELECT DISTINCT c.cif AS cif
                            FROM [ATISA_Input].dbo.cliente_proceso cp
                            JOIN [ATISA_Input].dbo.clientes c ON c.idcliente = cp.cliente_id
                            WHERE cp.proceso_id = :id
                            """
                        )
                        cifs_rows = await run_in_threadpool(lambda: session_cif.execute(sql_cifs, {"id": proceso_id}).mappings().all())
                        cifs = [str(r["cif"]).strip() for r in cifs_rows if r.get("cif") is not None]
                        if cifs:
                            sql_subdeps = text(
                                """
                                SELECT DISTINCT sd.codSubDePar AS cod
                                FROM [ATISA_Input].dbo.clienteSubDePar csd
                                JOIN [ATISA_Input].dbo.SubDePar sd ON sd.codSubDePar = csd.codSubDePar
                                WHERE csd.cif IN :cifs
                                """
                            ).bindparams(bindparam("cifs", expanding=True))
                            extra = await run_in_threadpool(lambda: session_cif.execute(sql_subdeps, {"cifs": cifs}).mappings().all())
                            extra_codes = [r["cod"] for r in extra]
                            subdeps = list({*subdeps, *extra_codes})
                    finally:
                        session_cif.close()
                    # Build cambios from request body
                    allowed = {"nombre", "descripcion", "frecuencia", "temporalidad", "inicia_dia_1"}
                    cambios = {k: v for k, v in (parsed_body or {}).items() if k in allowed}
                    for cod in subdeps:
                        await _emit_event(cod, "proceso_actualizado", {
                            "proceso_id": proceso_id,
                            "cambios": cambios,
                        })
                    return response

            # Hitos
            if path.startswith("/hitos"):
                import re
                if method == "PUT":
                    m = re.match(r"^/hitos/(\d+)$", path)
                    if m:
                        hito_id = int(m.group(1))
                        session = _get_db_session()
                        try:
                            subdeps = await run_in_threadpool(_infer_subdepar_for_hito, session, hito_id)
                        finally:
                            session.close()
                        # Expandir por CIF (misma lógica del GET) para hito
                        session_cif = _get_db_session()
                        try:
                            sql_cifs = text(
                                """
                                SELECT DISTINCT c.cif AS cif
                                FROM [ATISA_Input].dbo.cliente_proceso_hito cph
                                JOIN [ATISA_Input].dbo.cliente_proceso cp ON cp.id = cph.cliente_proceso_id
                                JOIN [ATISA_Input].dbo.clientes c ON c.idcliente = cp.cliente_id
                                WHERE cph.hito_id = :id
                                """
                            )
                            cifs_rows = await run_in_threadpool(lambda: session_cif.execute(sql_cifs, {"id": hito_id}).mappings().all())
                            cifs = [str(r["cif"]).strip() for r in cifs_rows if r.get("cif") is not None]
                            if cifs:
                                sql_subdeps = text(
                                    """
                                    SELECT DISTINCT sd.codSubDePar AS cod
                                    FROM [ATISA_Input].dbo.clienteSubDePar csd
                                    JOIN [ATISA_Input].dbo.SubDePar sd ON sd.codSubDePar = csd.codSubDePar
                                    WHERE csd.cif IN :cifs
                                    """
                                ).bindparams(bindparam("cifs", expanding=True))
                                extra = await run_in_threadpool(lambda: session_cif.execute(sql_subdeps, {"cifs": cifs}).mappings().all())
                                extra_codes = [r["cod"] for r in extra]
                                subdeps = list({*subdeps, *extra_codes})
                        finally:
                            session_cif.close()
                        allowed = {"nombre", "descripcion", "fecha_limite", "hora_limite", "obligatorio", "tipo", "habilitado"}
                        cambios = {k: v for k, v in (parsed_body or {}).items() if k in allowed}
                        for cod in subdeps:
                            await _emit_event(cod, "hito_master_actualizado", {
                                "hito_id": hito_id,
                                "cambios": cambios,
                            })
                        return response
                # POST /hitos -> generic, no direct mapping, skip
                return response

            # Proceso-Hitos
            if path.startswith("/proceso-hitos"):
                # A change in proceso-hito relation affects all subdepars using that proceso
                # Extract proceso_id from body if available (for POST); for DELETE/{id} we cannot infer easily here
                proceso_id: Optional[int] = None
                if isinstance(parsed_body, dict) and "proceso_id" in parsed_body:
                    try:
                        proceso_id = int(parsed_body["proceso_id"])  # type: ignore[arg-type]
                    except Exception:
                        proceso_id = None
                if proceso_id:
                    session = _get_db_session()
                    try:
                        subdeps = await run_in_threadpool(_infer_subdepar_for_proceso, session, proceso_id)
                    finally:
                        session.close()
                    # Expandir por CIF
                    session_cif = _get_db_session()
                    try:
                        sql_cifs = text(
                            """
                            SELECT DISTINCT c.cif AS cif
                            FROM [ATISA_Input].dbo.cliente_proceso cp
                            JOIN [ATISA_Input].dbo.clientes c ON c.idcliente = cp.cliente_id
                            WHERE cp.proceso_id = :id
                            """
                        )
                        cifs_rows = await run_in_threadpool(lambda: session_cif.execute(sql_cifs, {"id": proceso_id}).mappings().all())
                        cifs = [str(r["cif"]).strip() for r in cifs_rows if r.get("cif") is not None]
                        if cifs:
                            sql_subdeps = text(
                                """
                                SELECT DISTINCT sd.codSubDePar AS cod
                                FROM [ATISA_Input].dbo.clienteSubDePar csd
                                JOIN [ATISA_Input].dbo.SubDePar sd ON sd.codSubDePar = csd.codSubDePar
                                WHERE csd.cif IN :cifs
                                """
                            ).bindparams(bindparam("cifs", expanding=True))
                            extra = await run_in_threadpool(lambda: session_cif.execute(sql_subdeps, {"cifs": cifs}).mappings().all())
                            extra_codes = [r["cod"] for r in extra]
                            subdeps = list({*subdeps, *extra_codes})
                    finally:
                        session_cif.close()
                    allowed = {"proceso_id", "hito_id"}
                    cambios = {k: v for k, v in (parsed_body or {}).items() if k in allowed}
                    cambios["accion"] = "creado"
                    for cod in subdeps:
                        await _emit_event(cod, "proceso_hitos_actualizado", {
                            "proceso_id": proceso_id,
                            "cambios": cambios,
                        })
                return response

            # Cliente-Proceso
            if path.startswith("/cliente-procesos"):
                # POST creation: infer subdepartment using cliente_id from payload
                if method == "POST" and isinstance(parsed_body, dict):
                    # Support both keys: 'cliente_id' and legacy 'idcliente'
                    cliente_id = parsed_body.get("cliente_id")
                    if cliente_id is None:
                        cliente_id = parsed_body.get("idcliente")
                    if cliente_id is not None:
                        session = _get_db_session()
                        try:
                            # Obtener CIF del cliente
                            sql_cif = text(
                                """
                                SELECT c.cif AS cif
                                FROM [ATISA_Input].dbo.clientes c
                                WHERE c.idcliente = :cliente_id
                                """
                            )
                            row_cif = await run_in_threadpool(lambda: session.execute(sql_cif, {"cliente_id": cliente_id}).mappings().first())
                            cif = row_cif["cif"] if row_cif else None
                            codes: List[str] = []
                            if cif:
                                sql_subdeps = text(
                                    """
                                    SELECT sd.codSubDePar AS cod
                                    FROM [ATISA_Input].dbo.clienteSubDePar csd
                                    JOIN [ATISA_Input].dbo.SubDePar sd ON sd.codSubDePar = csd.codSubDePar
                                    WHERE csd.cif = :cif
                                    """
                                )
                                rows_sub = await run_in_threadpool(lambda: session.execute(sql_subdeps, {"cif": cif}).mappings().all())
                                codes = [r["cod"] for r in rows_sub]
                        finally:
                            session.close()
                        if codes:
                            allowed = {"cliente_id", "idcliente", "proceso_id", "id_proceso", "fecha_inicio", "fecha_fin", "mes", "anio", "anterior_id", "id_anterior"}
                            cambios = {k: v for k, v in (parsed_body or {}).items() if k in allowed}
                            for cod in sorted(set(codes)):
                                await _emit_event(cod, "cliente_proceso_creado", {
                                    "cliente_id": cliente_id,
                                    # Support both keys: 'proceso_id' and legacy 'id_proceso'
                                    "proceso_id": parsed_body.get("proceso_id", parsed_body.get("id_proceso")),
                                    "cambios": cambios,
                                })
                # PUT updates (if ever added): infer by cp_id path param
                elif method == "PUT":
                    import re
                    m = re.match(r"^/cliente-procesos/(\d+)$", path)
                    if m:
                        cp_id = int(m.group(1))
                        session = _get_db_session()
                        try:
                            # Obtener CIF del cliente del CP
                            sql_cif = text(
                                """
                                SELECT c.cif AS cif
                                FROM [ATISA_Input].dbo.cliente_proceso cp
                                JOIN [ATISA_Input].dbo.clientes c ON c.idcliente = cp.cliente_id
                                WHERE cp.id = :cp_id
                                """
                            )
                            row_cif = await run_in_threadpool(lambda: session.execute(sql_cif, {"cp_id": cp_id}).mappings().first())
                            cif = row_cif["cif"] if row_cif else None
                            codes: List[str] = []
                            if cif:
                                sql_subdeps = text(
                                    """
                                    SELECT sd.codSubDePar AS cod
                                    FROM [ATISA_Input].dbo.clienteSubDePar csd
                                    JOIN [ATISA_Input].dbo.SubDePar sd ON sd.codSubDePar = csd.codSubDePar
                                    WHERE csd.cif = :cif
                                    """
                                )
                                rows_sub = await run_in_threadpool(lambda: session.execute(sql_subdeps, {"cif": cif}).mappings().all())
                                codes = [r["cod"] for r in rows_sub]
                        finally:
                            session.close()
                        if codes:
                            allowed = {"fecha_inicio", "fecha_fin", "mes", "anio", "anterior_id"}
                            cambios = {k: v for k, v in (parsed_body or {}).items() if k in allowed}
                            for cod in sorted(set(codes)):
                                await _emit_event(cod, "cliente_proceso_actualizado", {
                                    "cliente_proceso_id": cp_id,
                                    "cambios": cambios,
                                })
                return response

            # Admin Hitos Departamento: actualizar campos por CPH
            if path.startswith("/admin-hitos/departamento-hito/") and method == "POST":
                import re
                m = re.match(r"^/admin-hitos/departamento-hito/(\d+)$", path)
                if m:
                    cph_id = int(m.group(1))
                    session = _get_db_session()
                    try:
                        data = await run_in_threadpool(_fetch_cph_by_id, session, cph_id)
                    finally:
                        session.close()
                    if data:
                        # Cambios aplicados (si vienen en el body)
                        allowed = {"estado", "fecha_limite", "hora_limite", "tipo"}
                        cambios = {k: v for k, v in (parsed_body or {}).items() if k in allowed}

                        # 1) Subdepartamentos por hito (relaciones existentes de CPH con mismo hito_id)
                        session2 = _get_db_session()
                        try:
                            related_hito = await run_in_threadpool(_fetch_cph_updates_for_hito, session2, int(data.get("hito_id")))
                        finally:
                            session2.close()

                        # 2) Subdepartamentos por CIF (misma lógica del GET): cliente completo asignado a varios subdepartamentos
                        session3 = _get_db_session()
                        try:
                            sql_cif = text(
                                """
                                SELECT c.cif AS cif
                                FROM [ATISA_Input].dbo.cliente_proceso_hito cph
                                JOIN [ATISA_Input].dbo.cliente_proceso cp ON cp.id = cph.cliente_proceso_id
                                JOIN [ATISA_Input].dbo.clientes c ON c.idcliente = cp.cliente_id
                                WHERE cph.id = :id
                                """
                            )
                            row_cif = await run_in_threadpool(lambda: session3.execute(sql_cif, {"id": cph_id}).mappings().first())
                            cif = row_cif["cif"] if row_cif else None

                            related_cif: List[Dict[str, Any]] = []
                            if cif:
                                sql_subdeps = text(
                                    """
                                    SELECT sd.codSubDePar AS cod
                                    FROM [ATISA_Input].dbo.clienteSubDePar csd
                                    JOIN [ATISA_Input].dbo.SubDePar sd ON sd.codSubDePar = csd.codSubDePar
                                    WHERE csd.cif = :cif
                                    """
                                )
                                rows_sub = await run_in_threadpool(lambda: session3.execute(sql_subdeps, {"cif": cif}).mappings().all())
                                related_cif = [dict(r) for r in rows_sub]
                        finally:
                            session3.close()

                        # Unificar subdepartamentos (por hito y por CIF), evitando duplicados
                        cods: Dict[str, Dict[str, Any]] = {}
                        for r in (related_hito or []):
                            if r.get("cod"):
                                cods[r["cod"]] = {"cph_id": r.get("cph_id"), "estado": r.get("estado")}
                        for r in (related_cif or []):
                            if r.get("cod") and r["cod"] not in cods:
                                # Para los que vienen solo por CIF, usamos el CPH original y su estado
                                cods[r["cod"]] = {"cph_id": data.get("cph_id"), "estado": data.get("estado")}

                        # Emitir a todos los subdepartamentos resultantes
                        for cod, meta in cods.items():
                            payload = {
                                "cliente_proceso_hito_id": meta.get("cph_id", data.get("cph_id")),
                                "nuevo_estado": cambios.get("estado", meta.get("estado", data.get("estado"))),
                                "hito_id": data.get("hito_id"),
                                "cambios": cambios,
                            }
                            await _emit_event(cod, "hito_actualizado", payload)
                return response


        except Exception as e:
            logger.error(f"Websocket emit middleware error for {method} {path}: {e}")

        return response

    # Expose utility on app state for other modules if helpful
    app.state.websocket_emit_event = _emit_event  # type: ignore[attr-defined]
