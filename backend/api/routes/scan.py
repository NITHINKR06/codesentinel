from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pydantic import BaseModel
from typing import Optional
import uuid

from db.database import get_db
from models.scan import Scan, ScanStatus, ScanType

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
        id=uuid.uuid4(),
        scan_type=scan_type.value,
        github_url=request.github_url,
        live_url=request.live_url,
        status=ScanStatus.PENDING.value,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    # Dispatch background Celery task
    try:
        from workers.scan_worker import run_scan_task
        run_scan_task.delay(str(scan.id))
    except Exception as e:
        # Celery not running — scan will stay pending
        print(f"Warning: Could not dispatch task: {e}")

    return ScanResponse(
        scan_id=str(scan.id),
        status=scan.status,
        message="Scan queued. Connect to /ws/scan/{scan_id} for live updates.",
    )


@router.post("/upload", response_model=ScanResponse)
async def create_scan_from_zip(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(400, "Only .zip files supported")

    content = await file.read()
    import tempfile
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.write(content)
    tmp.close()

    scan = Scan(
        id=uuid.uuid4(),
        scan_type=ScanType.ZIP.value,
        status=ScanStatus.PENDING.value,
        repo_name=file.filename,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    try:
        from workers.scan_worker import run_scan_task
        run_scan_task.delay(str(scan.id), zip_path=tmp.name)
    except Exception as e:
        print(f"Warning: Could not dispatch task: {e}")

    return ScanResponse(
        scan_id=str(scan.id),
        status=scan.status,
        message="Scan started from ZIP upload.",
    )


@router.get("")
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


@router.post("/{scan_id}/cancel")
async def cancel_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Scan).where(Scan.id == scan_id)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(404, "Scan not found")

    try:
        from workers.celery_app import celery_app
        i = celery_app.control.inspect()
        active_tasks = i.active()
        if active_tasks:
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    if task["name"] == "workers.scan_worker.run_scan_task" and scan_id in task["args"]:
                        celery_app.control.revoke(task["id"], terminate=True, signal="SIGKILL")
                        break
        
        # Also clean up the database state just in case it was terminated abruptly
        scan.status = ScanStatus.FAILED.value
        await db.commit()
        
        # Output a message to the websocket
        import redis
        import json
        r = redis.from_url("redis://localhost:6379/0")
        event = {
            "scan_id": scan_id,
            "stage": "failed",
            "message": "Scan cancelled by user",
            "progress": 0,
            "data": {},
        }
        r.publish(f"scan:{scan_id}:events", json.dumps(event))
        r.close()

    except Exception as e:
        print(f"Failed to cancel scan: {e}")
        raise HTTPException(500, "Failed to cancel scan")

    return {"message": "Scan cancelled successfully"}


@router.get("/{scan_id}")
async def get_scan(scan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Scan).where(Scan.id == scan_id)
    )
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