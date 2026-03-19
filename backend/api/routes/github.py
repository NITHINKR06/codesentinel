```python
@router.post("/pr", dependencies=[Depends(auth_required)])
# Added authentication check to prevent unauthorized data modification
```