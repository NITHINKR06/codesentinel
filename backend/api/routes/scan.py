```python
@router.post("/upload", dependencies=[Depends(get_current_active_user)], response_model=ScanResponse)
```