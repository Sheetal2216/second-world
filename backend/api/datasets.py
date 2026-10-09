from services.csv_parser import parse_csv
from services.text_parser import parse_text
from services.pdf_parser import parse_pdf

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from models.dataset_db import DatasetDB
from models.project_db import ProjectDB
from schemas.dataset import DatasetCreate, DatasetResponse


router = APIRouter(
    prefix="/api",
    tags=["Datasets"],
)


@router.post(
    "/projects/{project_id}/datasets",
    response_model=DatasetResponse,
)
def create_dataset(
    project_id: int,
    dataset: DatasetCreate,
    db: Session = Depends(get_db),
):
    project = db.get(ProjectDB, project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    db_dataset = DatasetDB(
        project_id=project_id,
        filename=dataset.filename,
        file_type=dataset.file_type,
        storage_path=dataset.storage_path,
        status=dataset.status,
        parsed_data=dataset.parsed_data,
    )

    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)

    return db_dataset


@router.get(
    "/projects/{project_id}/datasets",
    response_model=list[DatasetResponse],
)
def list_project_datasets(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = db.get(ProjectDB, project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return db.execute(
        select(DatasetDB).where(
            DatasetDB.project_id == project_id
        )
    ).scalars().all()


@router.get(
    "/datasets/{dataset_id}",
    response_model=DatasetResponse,
)
def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
):
    dataset = db.get(DatasetDB, dataset_id)

    if not dataset:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found",
        )

    return dataset


@router.post(
    "/projects/{project_id}/datasets/upload",
    response_model=DatasetResponse,
)
def upload_dataset(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Check that the project exists
    project = db.get(ProjectDB, project_id)

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # Check file type
    allowed_extensions = {".csv", ".pdf", ".txt"}

    original_filename = file.filename or "uploaded_file"
    extension = Path(original_filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only CSV, PDF, and TXT files are supported",
        )

    # Create a unique filename to avoid collisions
    unique_filename = f"{uuid4().hex}_{original_filename}"

    upload_directory = Path("data/uploads")
    upload_directory.mkdir(parents=True, exist_ok=True)

    file_path = upload_directory / unique_filename

    # Save the uploaded file
    with file_path.open("wb") as buffer:
        buffer.write(file.file.read())

    # Determine file type
    file_type = extension.lstrip(".")

    # Create database record
    db_dataset = DatasetDB(
        project_id=project_id,
        filename=original_filename,
        file_type=file_type,
        storage_path=str(file_path),
        status="pending",
        parsed_data=None,
    )

  try:
    if file_type == "csv":
        parsed_data = parse_csv(str(file_path))

    elif file_type == "txt":
        parsed_data = parse_text(str(file_path))

    elif file_type == "pdf":
        parsed_data = parse_pdf(str(file_path))

    else:
        raise ValueError("Unsupported file type")

    db_dataset.parsed_data = parsed_data
    db_dataset.status = "processed"

except Exception:
    db_dataset.status = "failed"

    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)

    return db_dataset  

