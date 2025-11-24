from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import List, Optional

from app.infrastructure.db.database import SessionLocal
from app.infrastructure.db.repositories.documental_categoria_repository_sql import SqlDocumentalCategoriaRepository
from app.interfaces.schemas.documental_categoria import (
    DocumentalCategoriaCreate,
    DocumentalCategoriaUpdate,
    DocumentalCategoriaResponse
)
from app.domain.entities.documental_categoria import DocumentalCategoria

router = APIRouter(prefix="/documental-categorias", tags=["Documental Categorias"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repo(db: Session = Depends(get_db)):
    return SqlDocumentalCategoriaRepository(session=db)

@router.get("",
           summary="Listar todas las categorias de documentos",
           description="Devuelve todas las categorías de documentos definidas en el sistema.")
def listar(
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Cantidad de resultados por página"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
        documental_categorias = repo.listar()
        total = len(documental_categorias)

        # Aplicar ordenación si se especifica y hay datos para ordenar
        if sort_field and documental_categorias and hasattr(documental_categorias[0], sort_field):
            reverse = sort_direction == "desc"

            # Función de ordenación que maneja valores None
            def sort_key(categoria):
                value = getattr(categoria, sort_field, None)
                if value is None:
                    return ""  # Los valores None van al final

                # Manejo especial para diferentes tipos de campos
                if sort_field == "id":
                    try:
                        return int(value)
                    except (ValueError, TypeError):
                        return 0
                else:
                    # Para campos de texto (nombre), convertir a minúsculas
                    # para ordenación insensible a mayúsculas
                    return str(value).lower()

            documental_categorias.sort(key=sort_key, reverse=reverse)

        # Aplicar paginación después de ordenar
        if page is not None and limit is not None:
            start = (page - 1) * limit
            end = start + limit
            documental_categorias = documental_categorias[start:end]

        # Devolver respuesta exitosa incluso si no hay categorías después de la paginación
        return {
            "total": total,
            "documental_categorias": documental_categorias
        }

@router.get("/cliente/{cliente_id}",
           summary="Listar categorías de documentos por cliente",
           description="Devuelve todas las categorías de documentos de un cliente específico.")
def listar_por_cliente(
    cliente_id: str = Path(..., description="ID del cliente"),
    page: Optional[int] = Query(None, ge=1, description="Página actual"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Cantidad de resultados por página"),
    sort_field: Optional[str] = Query(None, description="Campo por el cual ordenar"),
    sort_direction: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Dirección de ordenación: asc o desc"),
    repo = Depends(get_repo)
):
        # Obtener todas las categorías y filtrar por cliente
        documental_categorias = repo.obtener_por_cliente(cliente_id)
        total = len(documental_categorias)

        # Aplicar ordenación si se especifica y hay datos para ordenar
        if sort_field and documental_categorias and hasattr(documental_categorias[0], sort_field):
            reverse = sort_direction == "desc"

            # Función de ordenación que maneja valores None
            def sort_key(categoria):
                value = getattr(categoria, sort_field, None)
                if value is None:
                    return ""  # Los valores None van al final

                # Manejo especial para diferentes tipos de campos
                if sort_field == "id":
                    try:
                        return int(value)
                    except (ValueError, TypeError):
                        return 0
                else:
                    # Para campos de texto (nombre), convertir a minúsculas
                    # para ordenación insensible a mayúsculas
                    return str(value).lower()

            documental_categorias.sort(key=sort_key, reverse=reverse)

        # Aplicar paginación después de ordenar
        if page is not None and limit is not None:
            start = (page - 1) * limit
            end = start + limit
            documental_categorias = documental_categorias[start:end]

        # Devolver respuesta exitosa incluso si no hay categorías después de la paginación
        return {
            "total": total,
            "documental_categorias": documental_categorias
        }


@router.get("/{id}",
           response_model=DocumentalCategoriaResponse,
           summary="Obtener categoría de documento por ID",
           description="Devuelve una categoría de documento específica por su ID.")
def obtener_por_id(
    categoria_id: int = Path(..., description="ID de la categoría de documento"),
    repo = Depends(get_repo)
):
    categoria = repo.obtener_por_id(categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría de documento no encontrada")
    return categoria

@router.post("",
            response_model=DocumentalCategoriaResponse,
            summary="Crear nueva categoría de documento",
            description="Crea una nueva categoría de documento.")
def crear(
    data: DocumentalCategoriaCreate,
    repo = Depends(get_repo)
):
    categoria = DocumentalCategoria(
        id=None,
        cliente_id=data.cliente_id,
        nombre=data.nombre
    )
    return repo.guardar(categoria)

@router.put("/{id}",
           response_model=DocumentalCategoriaResponse,
           summary="Actualizar categoría de documento",
           description="Actualiza una categoría de documento existente.")
def actualizar(
    categoria_id: int = Path(..., description="ID de la categoría de documento a actualizar"),
    data: DocumentalCategoriaUpdate = Body(...),
    repo = Depends(get_repo)
):
    # Verificar que la categoría existe
    categoria_existente = repo.obtener_por_id(categoria_id)
    if not categoria_existente:
        raise HTTPException(status_code=404, detail="Categoría de documento no encontrada")

    # Crear diccionario con solo los campos que no son None
    update_data = {}
    if data.nombre is not None:
        update_data["nombre"] = data.nombre

    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")

    categoria_actualizada = repo.actualizar(categoria_id, update_data)
    if not categoria_actualizada:
        raise HTTPException(status_code=404, detail="Error al actualizar la categoría de documento")

    return categoria_actualizada

@router.delete("/{id}",
              summary="Eliminar categoría de documento",
              description="Elimina una categoría de documento por su ID.")
def eliminar(
    categoria_id: int = Path(..., description="ID de la categoría de documento a eliminar"),
    repo = Depends(get_repo)
):
    categoria = repo.obtener_por_id(categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría de documento no encontrada")

    resultado = repo.eliminar(categoria_id)
    if not resultado:
        raise HTTPException(status_code=500, detail="Error al eliminar la categoría de documento")

    return {"mensaje": "Categoría de documento eliminada exitosamente"}
