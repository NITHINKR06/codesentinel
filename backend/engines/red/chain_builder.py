```python
import hashlib  # Import required for the fix

for node_id, data in G.nodes(data=True):
    # Use SHA-256 for security-sensitive operations
    hashed_node_id = hashlib.sha256(node_id.encode()).hexdigest()
    nodes.append({
        "id": hashed_node_id,
        "label": data.get("function", node_id.split("::")[-1]),
        "file": data.get("file", ""),
        "hasVuln": data.get("has_vuln", False),
        "severity": _sev_label(data.get("max_severity", 0)),
        "inChain": node_id in chain_nodes,
        "vulns": data.get("vulns", []),
    })
```