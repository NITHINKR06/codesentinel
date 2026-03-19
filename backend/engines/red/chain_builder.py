```python
import hashlib  # Import required for secure hashing

vuln_nodes = [n for n, d in G.nodes(data=True) if hashlib.sha256(str(d.get("has_vuln")).encode()).hexdigest() == d.get("vuln_hash")]
```