import json

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import StudioProject
from app.studio.schemas import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["Studio Projects"])


def to_response(project: StudioProject) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        name=project.name,
        board_id=project.board_id,
        workspace=json.loads(project.workspace_json),
        generated_code=project.generated_code,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)) -> list[ProjectResponse]:
    projects = db.scalars(
        select(StudioProject).order_by(StudioProject.updated_at.desc())
    ).all()
    return [to_response(project) for project in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)) -> ProjectResponse:
    project = db.get(StudioProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return to_response(project)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ProjectResponse:
    project = StudioProject(
        name=payload.name.strip(),
        board_id=payload.board_id,
        workspace_json=json.dumps(payload.workspace, separators=(",", ":")),
        generated_code=payload.generated_code,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return to_response(project)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    payload: ProjectCreate,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    project = db.get(StudioProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    project.name = payload.name.strip()
    project.board_id = payload.board_id
    project.workspace_json = json.dumps(payload.workspace, separators=(",", ":"))
    project.generated_code = payload.generated_code
    db.commit()
    db.refresh(project)
    return to_response(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: Session = Depends(get_db)) -> Response:
    project = db.get(StudioProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
