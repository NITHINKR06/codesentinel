from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import uuid

from db.database import get_db
from models.scan import Scan, ScanStatus, ScanType
from workers.scan_worker import run_scan_task

router = APIRouter()


class ScanRequest(BaseModel):
    github_url: Optional[str] = None
    live_url: Optional[str] = None


class ScanResponse(BaseModel):
    scan_id: str
    status: str
    message: str


@router.post("", response_model=ScanResponse)
async def create_scan(request: ScanRequest, db: AsyncSession = Depends(get_db)):
    if not request.github_url and not request.live_url:
        raise HTTPException(400, "Provide github_url or live_url")

    scan_type = ScanType.GITHUB if request.github_url else ScanType.URL

    scan = Scan(
        scan_type=scan_type,
        github_url=request.github_url,
        live_url=request.live_url,
        status=ScanStatus.PENDING,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    # Dispatch background task
    run_scan_task.delay(str(scan.id))

    return ScanResponse(
        scan_id=str(scan.id),
        status=scan.status,
        message="Scan started. Connect to /ws/scan/{scan_id} for live updates.",
    )


@router.post("/upload", response_model=ScanResponse)
async def create_scan_from_zip(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(".zip"):
        raise HTTPException(400, "Only .zip files supported")

    content = await file.read()
    import tempfile, os

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.write(content)
    tmp.close()

    scan = Scan(
        scan_type=ScanType.ZIP,
        status=ScanStatus.PENDING,
        repo_name=file.filename,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    run_scan_task.delay(str(scan.id), zip_path=tmp.name)

    return ScanResponse(
        scan_id=str(scan.id),
        status=scan.status,
        message="Scan started from ZIP upload.",
    )


@router.get("/{scan_id}")
async def get_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scan).where(Scan.id == uuid.UUID(scan_id)))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(404, "Scan not found")

    return {
        "scan_id": str(scan.id),
        "status": scan.status,
        "scan_type": scan.scan_type,
        "repo_name": scan.repo_name,
        "github_url": scan.github_url,
        "total_findings": scan.total_findings,
        "critical_count": scan.critical_count,
        "high_count": scan.high_count,
        "medium_count": scan.medium_count,
        "low_count": scan.low_count,
        "score_before": scan.score_before,
        "score_after": scan.score_after,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
        "pr_url": scan.pr_url,
    }


@router.get("/")
async def list_scans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Scan).order_by(Scan.created_at.desc()).limit(20)
    )
    scans = result.scalars().all()
    return [
        {
            "scan_id": str(s.id),
            "status": s.status,
            "repo_name": s.repo_name,
            "github_url": s.github_url,
            "score_before": s.score_before,
            "score_after": s.score_after,
            "total_findings": s.total_findings,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in scans
    ]
