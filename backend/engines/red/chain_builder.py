import re
import networkx as nx
from typing import List, Dict, Optional
import structlog

log = structlog.get_logger()

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _extract_functions(content: str, file_path: str) -> List[Dict]:
    """Extract function definitions from source code."""
    functions = []
    # Python
    for m in re.finditer(r'^def\s+(\w+)\s*\(', content, re.MULTILINE):
        functions.append({
            "name": m.group(1),
            "file": file_path,
            "line": content[:m.start()].count("\n") + 1,
        })
    # JS/TS
    for m in re.finditer(r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\()', content, re.MULTILINE):
        name = m.group(1) or m.group(2)
        if name:
            functions.append({
                "name": name,
                "file": file_path,
                "line": content[:m.start()].count("\n") + 1,
            })
    return functions


def _extract_calls(content: str, file_path: str) -> List[Dict]:
    """Extract function call sites."""
    calls = []
    for m in re.finditer(r'(\w+)\s*\(', content):
        calls.append({
            "callee": m.group(1),
            "file": file_path,
            "line": content[:m.start()].count("\n") + 1,
        })
    return calls


def build_call_graph(files: List[Dict], findings: List[Dict]) -> nx.DiGraph:
    G = nx.DiGraph()

    # Index findings by (file, line)
    finding_index: Dict = {}
    for f in findings:
        key = (f["file_path"], f.get("line_number"))
        finding_index.setdefault(key, []).append(f)

    # Add nodes for each function
    all_functions: Dict[str, Dict] = {}
    for file_info in files:
        funcs = _extract_functions(file_info["content"], file_info["path"])
        for fn in funcs:
            node_id = f"{fn['file']}::{fn['name']}"
            vulns = finding_index.get((fn["file"], fn["line"]), [])
            G.add_node(node_id, **{
                "function": fn["name"],
                "file": fn["file"],
                "line": fn["line"],
                "vulns": vulns,
                "has_vuln": len(vulns) > 0,
                "max_severity": max((SEVERITY_RANK.get(v["severity"], 0) for v in vulns), default=0),
            })
            all_functions[fn["name"]] = node_id

    # Add edges via call relationships
    for file_info in files:
        calls = _extract_calls(file_info["content"], file_info["path"])
        caller_funcs = _extract_functions(file_info["content"], file_info["path"])
        for call in calls:
            if call["callee"] in all_functions:
                callee_node = all_functions[call["callee"]]
                # Find which function this call is inside
                caller = None
                for fn in reversed(caller_funcs):
                    if fn["line"] <= call["line"]:
                        caller = f"{fn['file']}::{fn['name']}"
                        break
                if caller and caller != callee_node and G.has_node(caller):
                    G.add_edge(caller, callee_node)

    log.info("Call graph built", nodes=G.number_of_nodes(), edges=G.number_of_edges())
    return G


def find_vuln_chains(G: nx.DiGraph, min_chain_severity: int = 2) -> List[Dict]:
    """
    Find paths in the call graph where multiple vulnerabilities chain together.
    Returns chains sorted by escalated severity.
    """
    chains = []
    vuln_nodes = [n for n, d in G.nodes(data=True) if d.get("has_vuln")]

    for source in vuln_nodes:
        for target in vuln_nodes:
            if source == target:
                continue
            try:
                paths = list(nx.all_simple_paths(G, source, target, cutoff=5))
                for path in paths:
                    # Collect all vulns along this path
                    path_vulns = []
                    for node in path:
                        node_data = G.nodes[node]
                        path_vulns.extend(node_data.get("vulns", []))

                    if len(path_vulns) < 2:
                        continue

                    max_sev = max(SEVERITY_RANK.get(v["severity"], 0) for v in path_vulns)
                    if max_sev < min_chain_severity:
                        continue

                    # Escalate severity based on chain length
                    escalated_sev = _escalate_severity(path_vulns)

                    chain = {
                        "chain_id": f"chain_{len(chains)+1}",
                        "nodes": path,
                        "vulns": path_vulns,
                        "length": len(path),
                        "escalated_severity": escalated_sev,
                        "attack_narrative": _build_narrative(path_vulns, path, G),
                    }
                    chains.append(chain)
            except nx.NetworkXError:
                continue

    # Deduplicate and sort
    seen = set()
    unique_chains = []
    for chain in sorted(chains, key=lambda c: SEVERITY_RANK.get(c["escalated_severity"], 0), reverse=True):
        key = frozenset(v["file_path"] + str(v.get("line_number")) for v in chain["vulns"])
        if key not in seen:
            seen.add(key)
            unique_chains.append(chain)

    log.info("Chains found", count=len(unique_chains))
    return unique_chains[:20]  # cap at 20 chains


def _escalate_severity(vulns: List[Dict]) -> str:
    """3+ chained vulns can escalate to critical."""
    has_critical = any(v["severity"] == "critical" for v in vulns)
    has_high = any(v["severity"] == "high" for v in vulns)

    if has_critical or (has_high and len(vulns) >= 2):
        return "critical"
    elif has_high or (len(vulns) >= 3):
        return "high"
    return "medium"


def _build_narrative(vulns: List[Dict], path: List[str], G: nx.DiGraph) -> str:
    steps = []
    for i, vuln in enumerate(vulns[:5], 1):
        steps.append(
            f"Step {i}: Exploit {vuln['title']} in {vuln['file_path']} "
            f"(line {vuln.get('line_number', '?')}) — {vuln['plain_impact']}"
        )
    return "\n".join(steps)


def build_graph_data_for_ui(G: nx.DiGraph, chains: List[Dict]) -> Dict:
    """Serialize graph for D3.js force graph rendering."""
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
            "vulns": data.get("vulns", []),
        })

    edges = [{"source": u, "target": v} for u, v in G.edges()]

    return {"nodes": nodes, "edges": edges}


def _sev_label(rank: int) -> Optional[str]:
    return {4: "critical", 3: "high", 2: "medium", 1: "low"}.get(rank)
