"""Script management API endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.models import (
    ScriptCreate,
    ScriptListResponse,
    ScriptResponse,
    ScriptUpdate,
)
from src.models import crud, get_db


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ScriptResponse)
async def create_script(
    script_data: ScriptCreate,
    db: Session = Depends(get_db),
) -> ScriptResponse:
    """Create a new script."""
    script = crud.script.create(
        db,
        obj_in={
            "title": script_data.title,
            "content": script_data.content,
        }
    )
    
    logger.info(f"Created script: {script.title} (ID: {script.id})")
    return script


@router.get("/", response_model=ScriptListResponse)
async def list_scripts(
    skip: int = 0,
    limit: int = 100,
    search: str = Query(None, description="Search in title or content"),
    db: Session = Depends(get_db),
) -> ScriptListResponse:
    """List all scripts with optional search."""
    if search:
        scripts = crud.script.search(db, query=search)
        # Apply pagination to search results
        total = len(scripts)
        scripts = scripts[skip : skip + limit]
    else:
        scripts = crud.script.get_multi(db, skip=skip, limit=limit)
        total = db.query(crud.script.model).count()
    
    return ScriptListResponse(
        success=True,
        data=scripts,
        total=total,
    )


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: int,
    db: Session = Depends(get_db),
) -> ScriptResponse:
    """Get a specific script."""
    script = crud.script.get(db, id=script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    return script


@router.get("/{script_id}/versions", response_model=List[ScriptResponse])
async def get_script_versions(
    script_id: int,
    db: Session = Depends(get_db),
) -> List[ScriptResponse]:
    """Get all versions of a script."""
    script = crud.script.get(db, id=script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Get the parent ID (or use current ID if it's the parent)
    parent_id = script.parent_id or script.id
    
    # Get all versions
    versions = crud.script.get_versions(db, parent_id=parent_id)
    
    # Include the parent in the list
    if script.parent_id is None:
        versions.insert(0, script)
    
    return versions


@router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: int,
    script_update: ScriptUpdate,
    db: Session = Depends(get_db),
) -> ScriptResponse:
    """Update a script."""
    script = crud.script.get(db, id=script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Update script
    update_data = script_update.model_dump(exclude_unset=True)
    script = crud.script.update(db, db_obj=script, obj_in=update_data)
    
    logger.info(f"Updated script: {script.title} (ID: {script.id})")
    return script


@router.post("/{script_id}/version", response_model=ScriptResponse)
async def create_script_version(
    script_id: int,
    content: str,
    db: Session = Depends(get_db),
) -> ScriptResponse:
    """Create a new version of a script."""
    new_version = crud.script.create_version(
        db, script_id=script_id, content=content
    )
    
    if not new_version:
        raise HTTPException(status_code=404, detail="Script not found")
    
    logger.info(f"Created version {new_version.version} of script: {new_version.title} (ID: {new_version.id})")
    return new_version


@router.delete("/{script_id}")
async def delete_script(
    script_id: int,
    delete_versions: bool = Query(False, description="Delete all versions"),
    db: Session = Depends(get_db),
) -> dict:
    """Delete a script."""
    script = crud.script.get(db, id=script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # If delete_versions is True and this is a parent, delete all versions
    if delete_versions and script.parent_id is None:
        versions = crud.script.get_versions(db, parent_id=script.id)
        for version in versions:
            crud.script.delete(db, id=version.id)
            logger.info(f"Deleted script version: {version.title} v{version.version} (ID: {version.id})")
    
    # Delete the script
    crud.script.delete(db, id=script_id)
    
    logger.info(f"Deleted script: {script.title} (ID: {script_id})")
    return {"success": True, "message": f"Script '{script.title}' deleted"}


@router.post("/{script_id}/improve")
async def improve_script(
    script_id: int,
    instructions: str = Query(..., description="Instructions for improvement"),
    db: Session = Depends(get_db),
) -> dict:
    """Get AI suggestions to improve a script."""
    script = crud.script.get(db, id=script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # TODO: Implement Ollama integration in Phase 7
    return {
        "success": True,
        "message": "AI improvement will be available in a future update",
        "script_id": script_id,
        "instructions": instructions,
    }