import io
import json
import re
import zipfile

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import WebScratchProject
from app.web_studio.schemas import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/web-projects", tags=["Web Scratch Studio"])


def to_response(project: WebScratchProject) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        name=project.name,
        template_id=project.template_id,
        workspace=json.loads(project.workspace_json),
        html_code=project.html_code,
        css_code=project.css_code,
        javascript_code=project.javascript_code,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return cleaned or "thantrajnana-web-project"


@router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)) -> list[ProjectResponse]:
    projects = db.scalars(select(WebScratchProject).order_by(WebScratchProject.updated_at.desc())).all()
    return [to_response(project) for project in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)) -> ProjectResponse:
    project = db.get(WebScratchProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return to_response(project)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    project = WebScratchProject(
        name=payload.name,
        template_id=payload.template_id,
        workspace_json=json.dumps(payload.workspace, separators=(",", ":")),
        html_code=payload.html_code,
        css_code=payload.css_code,
        javascript_code=payload.javascript_code,
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
    project = db.get(WebScratchProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    project.name = payload.name
    project.template_id = payload.template_id
    project.workspace_json = json.dumps(payload.workspace, separators=(",", ":"))
    project.html_code = payload.html_code
    project.css_code = payload.css_code
    project.javascript_code = payload.javascript_code
    db.commit()
    db.refresh(project)
    return to_response(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: Session = Depends(get_db)) -> Response:
    project = db.get(WebScratchProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{project_id}/export", response_class=StreamingResponse)
def export_project(project_id: str, db: Session = Depends(get_db)) -> StreamingResponse:
    project = db.get(WebScratchProject, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
        package.writestr("index.html", project.html_code)
        package.writestr("styles.css", project.css_code)
        package.writestr("script.js", project.javascript_code)
        package.writestr(
            "project.json",
            json.dumps(
                {
                    "app": "Thantrajnana Web Scratch Studio",
                    "version": 1,
                    "project_name": project.name,
                    "template_id": project.template_id,
                    "workspace": json.loads(project.workspace_json),
                },
                indent=2,
            ),
        )
        package.writestr(
            "README.md",
            f"# {project.name}\n\nGenerated with Thantrajnana Web Scratch Studio.\n",
        )
    archive.seek(0)

    filename = f'{safe_filename(project.name)}.zip'
    return StreamingResponse(
        archive,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
