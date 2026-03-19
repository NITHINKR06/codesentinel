from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from db.database import get_db
from models.scan import Scan

router = APIRouter()


@router.get("/{scan_id}")
async def get_report(scan_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scan).where(Scan.id == uuid.UUID(scan_id)))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(404, "Report not found")

    return {
        "scan_id": str(scan.id),
        "status": scan.status,
        "repo_name": scan.repo_name,
        "github_url": scan.github_url,
        "score_before": scan.score_before,
        "score_after": scan.score_after,
        "total_findings": scan.total_findings,
        "critical_count": scan.critical_count,
        "high_count": scan.high_count,
        "medium_count": scan.medium_count,
        "low_count": scan.low_count,
        "findings": scan.findings_data or [],
        "chains": scan.chains_data or [],
        "patches": scan.patches_data or [],
        "ghost_commits": scan.ghost_commits_data or [],
        "threat_actor": scan.threat_actor_data,
        "attack_graph": scan.attack_graph_data,
        "pr_url": scan.pr_url,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
    }


@router.get("/{scan_id}/badge")
async def get_badge(scan_id: str, db: AsyncSession = Depends(get_db)):
    """Returns SVG badge for README embedding."""
    result = await db.execute(select(Scan).where(Scan.id == uuid.UUID(scan_id)))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(404, "Scan not found")

    score = scan.score_after or scan.score_before or 0
    color = "#1D9E75" if score >= 80 else "#BA7517" if score >= 50 else "#E24B4A"
    label = "secured" if score >= 80 else "needs work" if score >= 50 else "at risk"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="180" height="20">
  <rect width="110" height="20" rx="3" fill="#555"/>
  <rect x="110" width="70" height="20" rx="3" fill="{color}"/>
  <text x="55" y="14" font-family="monospace" font-size="11" fill="white" text-anchor="middle">CodeSentinel</text>
  <text x="145" y="14" font-family="monospace" font-size="11" fill="white" text-anchor="middle">{score}/100 {label}</text>
</svg>"""

    from fastapi.responses import Response
    return Response(content=svg, media_type="image/svg+xml")
