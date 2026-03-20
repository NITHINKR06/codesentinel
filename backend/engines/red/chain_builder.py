import re
import networkx as nx
from typing import List, Dict, Optional
import structlog

log = structlog.get_logger()

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _extract_functions(content: str, file_path: str) -> List[Dict]:
    functions = []
    ext = file_path.split(".")[-1].lower()

    if ext == "py":
        # Regular functions
        for m in re.finditer(r'^(?:async\s+)?def\s+(\w+)\s*\(', content, re.MULTILINE):
            functions.append({
                "name": m.group(1),
                "file": file_path,
                "line": content[:m.start()].count("\n") + 1,
                "type": "function",
            })
        # Class methods
        for m in re.finditer(r'^\s+(?:async\s+)?def\s+(\w+)\s*\(self', content, re.MULTILINE):
            functions.append({
                "name": m.group(1),
                "file": file_path,
                "line": content[:m.start()].count("\n") + 1,
                "type": "method",
            })
        # FastAPI/Flask route handlers
        for m in re.finditer(r'@(?:app|router)\.\w+\([^)]*\)\s*\n\s*(?:async\s+)?def\s+(\w+)', content):
            functions.append({
                "name": m.group(1),
                "file": file_path,
                "line": content[:m.start()].count("\n") + 1,
                "type": "route",
            })

    elif ext in ("js", "ts", "jsx", "tsx"):
        # Named functions
        for m in re.finditer(r'(?:async\s+)?function\s+(\w+)\s*\(', content):
            functions.append({
                "name": m.group(1),
                "file": file_path,
                "line": content[:m.start()].count("\n") + 1,
                "type": "function",
            })
        # Arrow functions / const
        for m in re.finditer(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(', content):
            functions.append({
                "name": m.group(1),
                "file": file_path,
                "line": content[:m.start()].count("\n") + 1,
                "type": "arrow",
            })
        # Express route handlers
        for m in re.finditer(r'(?:app|router)\.\w+\s*\([^,)]+,\s*(?:async\s*)?\(?\s*(\w+)', content):
            functions.append({
                "name": m.group(1),
                "file": file_path,
                "line": content[:m.start()].count("\n") + 1,
                "type": "route",
            })
        # Class methods
        for m in re.finditer(r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{', content):
            name = m.group(1)
            if name not in ("if", "for", "while", "switch", "catch", "function"):
                functions.append({
                    "name": name,
                    "file": file_path,
                    "line": content[:m.start()].count("\n") + 1,
                    "type": "method",
                })

    return functions


def _extract_calls(content: str, file_path: str) -> List[Dict]:
    calls = []
    ext = file_path.split(".")[-1].lower()

    if ext == "py":
        # Direct calls: func()
        for m in re.finditer(r'(?<!\bdef\s)(\w+)\s*\(', content):
            calls.append({
                "callee": m.group(1),
                "file": file_path,
                "line": content[:m.start()].count("\n") + 1,
            })
        # Method calls: self.method() or obj.method()
        for m in re.finditer(r'(?:self|cls)\.(\w+)\s*\(', content):
            calls.append({
                "callee": m.group(1),
                "file": file_path,
                "line": content[:m.start()].count("\n") + 1,
            })
        # Await calls: await something()
        for m in re.finditer(r'await\s+(?:\w+\.)*(\w+)\s*\(', content):
            calls.append({
                "callee": m.group(1),
                "file": file_path,
                "line": content[:m.start()].count("\n") + 1,
            })

    elif ext in ("js", "ts", "jsx", "tsx"):
        for m in re.finditer(r'(?:await\s+)?(?:\w+\.)*(\w+)\s*\(', content):
            name = m.group(1)
            if name not in ("if", "for", "while", "switch", "catch", "return", "typeof", "instanceof"):
                calls.append({
                    "callee": name,
                    "file": file_path,
                    "line": content[:m.start()].count("\n") + 1,
                })

    return calls


def build_call_graph(files: List[Dict], findings: List[Dict]) -> nx.DiGraph:
    G = nx.DiGraph()

    # Index findings by file + approximate line
    finding_index: Dict = {}
    for f in findings:
        key = f["file_path"]
        finding_index.setdefault(key, []).append(f)

    # Build node for each function
    all_functions: Dict[str, str] = {}  # name -> node_id

    for file_info in files:
        ext = file_info["path"].split(".")[-1].lower()
        if ext not in ("py", "js", "ts", "jsx", "tsx", "php"):
            continue

        funcs = _extract_functions(file_info["content"], file_info["path"])
        for fn in funcs:
            node_id = f"{fn['file']}::{fn['name']}"

            # Find vulns at or near this function's line
            file_findings = finding_index.get(fn["file"], [])
            fn_vulns = []
            for fnd in file_findings:
                fnd_line = fnd.get("line_number", 0)
                fn_line = fn["line"]
                # Consider vuln belongs to function if within 30 lines after definition
                if fn_line <= fnd_line <= fn_line + 30:
                    fn_vulns.append(fnd)

            max_sev = max(
                (SEVERITY_RANK.get(v["severity"], 0) for v in fn_vulns),
                default=0
            )

            G.add_node(node_id, **{
                "function": fn["name"],
                "file": fn["file"],
                "line": fn["line"],
                "type": fn["type"],
                "vulns": fn_vulns,
                "has_vuln": len(fn_vulns) > 0,
                "max_severity": max_sev,
            })
            # Keep last definition if duplicate names
            all_functions[fn["name"]] = node_id

    # Add edges via call relationships
    for file_info in files:
        ext = file_info["path"].split(".")[-1].lower()
        if ext not in ("py", "js", "ts", "jsx", "tsx", "php"):
            continue

        content = file_info["content"]
        calls = _extract_calls(content, file_info["path"])
        caller_funcs = _extract_functions(content, file_info["path"])

        for call in calls:
            if call["callee"] not in all_functions:
                continue
            callee_node = all_functions[call["callee"]]

            # Find which function this call is inside
            caller_node = None
            for fn in reversed(caller_funcs):
                if fn["line"] <= call["line"]:
                    caller_node = f"{fn['file']}::{fn['name']}"
                    break

            if (caller_node and
                caller_node != callee_node and
                G.has_node(caller_node) and
                G.has_node(callee_node)):
                G.add_edge(caller_node, callee_node)

    log.info("Call graph built", nodes=G.number_of_nodes(), edges=G.number_of_edges())
    return G


def find_vuln_chains(G: nx.DiGraph, min_chain_severity: int = 1) -> List[Dict]:
    """Find paths where multiple vulnerabilities connect into exploit chains."""
    chains = []
    vuln_nodes = [n for n, d in G.nodes(data=True) if d.get("has_vuln")]

    if len(vuln_nodes) < 2:
        # Not enough vuln nodes for chains — try single-node chains with high severity
        for node, data in G.nodes(data=True):
            if data.get("max_severity", 0) >= 3:
                vulns = data.get("vulns", [])
                if vulns:
                    chains.append({
                        "chain_id": f"chain_{len(chains)+1}",
                        "nodes": [node],
                        "vulns": vulns,
                        "length": 1,
                        "escalated_severity": "critical" if data["max_severity"] >= 4 else "high",
                        "attack_narrative": _build_narrative(vulns, [node], G),
                    })
        return chains[:10]

    seen_pairs = set()

    for source in vuln_nodes:
        for target in vuln_nodes:
            if source == target:
                continue
            pair = tuple(sorted([source, target]))
            if pair in seen_pairs:
                continue

            try:
                paths = list(nx.all_simple_paths(G, source, target, cutoff=6))
                for path in paths:
                    path_vulns = []
                    for node in path:
                        node_data = G.nodes[node]
                        path_vulns.extend(node_data.get("vulns", []))

                    if len(path_vulns) < 1:
                        continue

                    max_sev = max(
                        SEVERITY_RANK.get(v["severity"], 0) for v in path_vulns
                    )
                    if max_sev < min_chain_severity:
                        continue

                    escalated = _escalate_severity(path_vulns)
                    chains.append({
                        "chain_id": f"chain_{len(chains)+1}",
                        "nodes": path,
                        "vulns": path_vulns,
                        "length": len(path),
                        "escalated_severity": escalated,
                        "attack_narrative": _build_narrative(path_vulns, path, G),
                    })
                    seen_pairs.add(pair)

            except nx.NetworkXError:
                continue

    # Deduplicate and sort by severity
    seen_keys = set()
    unique = []
    for chain in sorted(
        chains,
        key=lambda c: SEVERITY_RANK.get(c["escalated_severity"], 0),
        reverse=True
    ):
        key = frozenset(
            v.get("file_path", "") + str(v.get("line_number", ""))
            for v in chain["vulns"]
        )
        if key not in seen_keys:
            seen_keys.add(key)
            unique.append(chain)

    log.info("Chains found", count=len(unique))
    return unique[:20]


def _escalate_severity(vulns: List[Dict]) -> str:
    has_critical = any(v["severity"] == "critical" for v in vulns)
    has_high = any(v["severity"] == "high" for v in vulns)
    if has_critical or (has_high and len(vulns) >= 2):
        return "critical"
    elif has_high or len(vulns) >= 3:
        return "high"
    elif len(vulns) >= 2:
        return "medium"
    return "low"


def _build_narrative(vulns: List[Dict], path: List[str], G: nx.DiGraph) -> str:
    steps = []
    for i, vuln in enumerate(vulns[:6], 1):
        fn_name = vuln.get("function_name", path[min(i-1, len(path)-1)].split("::")[-1] if path else "")
        steps.append(
            f"Step {i}: Exploit {vuln['title']} in "
            f"`{vuln['file_path']}:{vuln.get('line_number','?')}`\n"
            f"  → {vuln['plain_impact']}"
        )
    if len(path) > 1:
        steps.append(f"\nAttack path: {' → '.join(n.split('::')[-1] for n in path[:6])}")
    return "\n".join(steps)


def build_graph_data_for_ui(G: nx.DiGraph, chains: List[Dict]) -> Dict:
    chain_nodes = set()
    for chain in chains:
        for node in chain.get("nodes", []):
            chain_nodes.add(node)

    nodes = []
    for node_id, data in G.nodes(data=True):
        nodes.append({
            "id": node_id,
            "label": data.get("function", node_id.split("::")[-1]),
            "file": data.get("file", ""),
            "hasVuln": data.get("has_vuln", False),
            "severity": _sev_label(data.get("max_severity", 0)),
            "inChain": node_id in chain_nodes,
            "type": data.get("type", "function"),
            "vulns": data.get("vulns", []),
        })

    edges = [{"source": u, "target": v} for u, v in G.edges()]
    return {"nodes": nodes, "edges": edges}


def _sev_label(rank: int) -> Optional[str]:
    return {4: "critical", 3: "high", 2: "medium", 1: "low"}.get(rank)