```python
@router.post("/pr", dependencies=[Depends(auth_required)])
async def create_pull_request(request: PRRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scan).where(Scan.id == uuid.UUID(request.scan_id)))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(404, "Scan not found")

    if not scan.patches_data:
        raise HTTPException(400, "No patches available for this scan")

    from github import Github
```