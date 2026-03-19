```python
@router.post("/pr", dependencies=[Depends(auth_required)])
async def create_pull_request(request: PRRequest, db: AsyncSession = Depends(get_db)):
    # Token comes from server env — never from the client
    if not settings.GITHUB_TOKEN:
        raise HTTPException(400, "GITHUB_TOKEN not configured on server")

    result = await db.execute(select(Scan).where(Scan.id == request.scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(404, "Scan not found")
```

```python
from fastapi.security import OAuth2PasswordBearer, Security

auth_required = OAuth2PasswordBearer(tokenUrl="login")
```