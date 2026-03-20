import re
import networkx as nx
from typing import List, Dict, Optional
import structlog

log = structlog.get_logger()

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _extract_functions(content: str, file_path: str) -> List[Dict]:
    functions = []
    ext = file_path.split(".")[-1].lower()
    lines = content.split("\n")

    if ext == "py":
        for m in re.finditer(r'^(?:async\s+)?def\s+(\w+)\s*\(', content, re.MULTILINE):
            functions.append({"name": m.group(1), "file": file_path,
                              "line": content[:m.start()].count("\n") + 1, "type": "function"})
        for m in re.finditer(r'^\s+(?:async\s+)?def\s+(\w+)\s*\(self', content, re.MULTILINE):
            functions.append({"name": m.group(1), "file": file_path,
                              "line": content[:m.start()].count("\n") + 1, "type": "method"})
        for m in re.finditer(r'@(?:app|router)\.\w+\([^)]*\)\s*\n\s*(?:async\s+)?def\s+(\w+)', content):
            functions.append({"name": m.group(1), "file": file_path,
                              "line": content[:m.start()].count("\n") + 1, "type": "route"})

    elif ext in ("js", "ts", "jsx", "tsx"):
        for m in re.finditer(r'(?:async\s+)?function\s+(\w+)\s*\(', content):
            functions.append({"name": m.group(1), "file": file_path,
                              "line": content[:m.start()].count("\n") + 1, "type": "function"})
        for m in re.finditer(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(', content):
            functions.append({"name": m.group(1), "file": file_path,
                              "line": content[:m.start()].count("\n") + 1, "type": "arrow"})
        for m in re.finditer(r'(?:app|router)\.\w+\s*\([^,)]+,\s*(?:async\s*)?\(?\s*(\w+)', content):
            functions.append({"name": m.group(1), "file": file_path,
                              "line": content[:m.start()].count("\n") + 1, "type": "route"})
        for m in re.finditer(r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{', content):
            name = m.group(1)
            if name not in ("if","for","while","switch","catch","function","class"):
                functions.append({"name": name, "file": file_path,
                                  "line": content[:m.start()].count("\n") + 1, "type": "method"})

    # Deduplicate by name+line
    seen = set()
    unique = []
    for f in functions:
        key = (f["name"], f["line"])
        if key not in seen:
            seen.add(key)
            unique.append(f)

    return unique


def _get_function_end_line(functions: List[Dict], fn_index: int, total_lines: int) -> int:
    """Estimate where a function ends — next function start or end of file."""
    if fn_index + 1 < len(functions):
        return functions[fn_index + 1]["line"] - 1
    return total_lines


def _extract_calls(content: str, file_path: str) -> List[Dict]:
    calls = []
    ext = file_path.split(".")[-1].lower()

    if ext == "py":
        for m in re.finditer(r'(?<!\bdef\s)\b(\w+)\s*\(', content):
            calls.append({"callee": m.group(1), "file": file_path,
                          "line": content[:m.start()].count("\n") + 1})
        for m in re.finditer(r'(?:self|cls)\.(\w+)\s*\(', content):
            calls.append({"callee": m.group(1), "file": file_path,
                          "line": content[:m.start()].count("\n") + 1})
        for m in re.finditer(r'await\s+(?:\w+\.)*(\w+)\s*\(', content):
            calls.append({"callee": m.group(1), "file": file_path,
                          "line": content[:m.start()].count("\n") + 1})
    elif ext in ("js", "ts", "jsx", "tsx"):
        for m in re.finditer(r'(?:await\s+)?(?:\w+\.)*(\w+)\s*\(', content):
            name = m.group(1)
            if name not in ("if","for","while","switch","catch","return","typeof","instanceof","require"):
                calls.append({"callee": name, "file": file_path,
                              "line": content[:m.start()].count("\n") + 1})
    return calls


def build_call_graph(files: List[Dict], findings: List[Dict]) -> nx.DiGraph:
    G = nx.DiGraph()

    # Index findings by file
    finding_index: Dict[str, List] = {}
    for f in findings:
        finding_index.setdefault(f["file_path"], []).append(f)

    all_functions: Dict[str, str] = {}

    for file_info in files:
        ext = file_info["path"].split(".")[-1].lower()
        if ext not in ("py", "js", "ts", "jsx", "tsx", "php"):
            continue

        content = file_info["content"]
        total_lines = content.count("\n") + 1
        funcs = _extract_functions(content, file_info["path"])
        funcs_sorted = sorted(funcs, key=lambda x: x["line"])

        for i, fn in enumerate(funcs_sorted):
            node_id = f"{fn['file']}::{fn['name']}"
            fn_start = fn["line"]
            fn_end = _get_function_end_line(funcs_sorted, i, total_lines)

            # Assign findings that fall WITHIN this function's line range
            file_findings = finding_index.get(fn["file"], [])
            fn_vulns = [
                fnd for fnd in file_findings
                if fn_start <= fnd.get("line_number", 0) <= fn_end
            ]

            # Also assign file-level findings to first function if no line match
            if not fn_vulns and i == 0:
                fn_vulns = [
                    fnd for fnd in file_findings
                    if not any(
                        other_fn["line"] <= fnd.get("line_number", 0)
                        for other_fn in funcs_sorted[1:]
                    )
                ]

            max_sev = max(
                (SEVERITY_RANK.get(v["severity"], 0) for v in fn_vulns),
                default=0
            )

            G.add_node(node_id, **{
                "function": fn["name"],
                "file": fn["file"],
                "line": fn_start,
                "type": fn["type"],
                "vulns": fn_vulns,
                "has_vuln": len(fn_vulns) > 0,
                "max_severity": max_sev,
            })
            all_functions[fn["name"]] = node_id

    # Add edges
    for file_info in files:
        ext = file_info["path"].split(".")[-1].lower()
        if ext not in ("py", "js", "ts", "jsx", "tsx", "php"):
            continue

        content = file_info["content"]
        calls = _extract_calls(content, file_info["path"])
        caller_funcs = sorted(
            _extract_functions(content, file_info["path"]),
            key=lambda x: x["line"]
        )

        for call in calls:
            if call["callee"] not in all_functions:
                continue
            callee_node = all_functions[call["callee"]]

            caller_node = None
            for fn in reversed(caller_funcs):
                if fn["line"] <= call["line"]:
                    caller_node = f"{fn['file']}::{fn['name']}"
                    break

            if (caller_node and caller_node != callee_node and
                    G.has_node(caller_node) and G.has_node(callee_node)):
                G.add_edge(caller_node, callee_node)

    log.info("Call graph built", nodes=G.number_of_nodes(), edges=G.number_of_edges())
    return G


def find_vuln_chains(G: nx.DiGraph, min_chain_severity: int = 1) -> List[Dict]:
    """Find exploit chains — lowered threshold to catch more real chains."""
    chains = []
    vuln_nodes = [n for n, d in G.nodes(data=True) if d.get("has_vuln")]

    log.info("Finding chains", vuln_nodes=len(vuln_nodes), total_nodes=G.number_of_nodes())

    # If fewer than 2 vuln nodes, return single high-severity findings as chains
    if len(vuln_nodes) < 2:
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
                        path_vulns.extend(G.nodes[node].get("vulns", []))

                    if not path_vulns:
                        continue

                    max_sev = max(
                        SEVERITY_RANK.get(v["severity"], 0) for v in path_vulns
                    )
                    if max_sev < min_chain_severity:
                        continue

                    chains.append({
                        "chain_id": f"chain_{len(chains)+1}",
                        "nodes": path,
                        "vulns": path_vulns,
                        "length": len(path),
                        "escalated_severity": _escalate_severity(path_vulns),
                        "attack_narrative": _build_narrative(path_vulns, path, G),
                    })
                    seen_pairs.add(pair)

            except nx.NetworkXError:
                continue

    # Deduplicate
    seen_keys = set()
    unique = []
    for chain in sorted(
        chains,
        key=lambda c: (SEVERITY_RANK.get(c["escalated_severity"], 0), c["length"]),
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
        fn = path[min(i-1, len(path)-1)].split("::")[-1] if path else "unknown"
        steps.append(
            f"Step {i}: [{vuln.get('severity','').upper()}] {vuln['title']}\n"
            f"  File: {vuln['file_path']}:{vuln.get('line_number','?')}\n"
            f"  Impact: {vuln['plain_impact']}"
        )
    if len(path) > 1:
        path_str = " → ".join(n.split("::")[-1] for n in path[:6])
        steps.append(f"\nCall path: {path_str}")
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