import ast
import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set

import structlog

log = structlog.get_logger()

USER_INPUT_NAMES = {
    "request",
    "req",
    "params",
    "param",
    "query",
    "body",
    "data",
    "payload",
    "input",
    "form",
    "json",
    "headers",
    "cookies",
    "args",
    "kwargs",
    "user_input",
    "filename",
    "path",
    "command",
    "cmd",
    "url",
    "uri",
}

SOURCE_CALLS = {
    "input",
    "request.args.get",
    "request.form.get",
    "request.json.get",
    "request.get_json",
    "req.args.get",
    "req.form.get",
    "req.json.get",
    "req.get_json",
    "os.getenv",
    "os.environ.get",
    "flask.request.args.get",
    "flask.request.form.get",
}

SANITIZER_CALLS = {
    "escape",
    "html.escape",
    "markupsafe.escape",
    "sanitize",
    "bleach.clean",
    "quote",
    "urllib.parse.quote",
    "os.path.basename",
    "werkzeug.utils.secure_filename",
}

SINKS = {
    "sqli": {
        "execute",
        "executemany",
        "query",
        "raw",
        "raw_query",
        "cursor.execute",
        "cursor.executemany",
        "db.execute",
    },
    "command_injection": {
        "os.system",
        "os.popen",
        "subprocess.call",
        "subprocess.run",
        "subprocess.Popen",
        "subprocess.check_output",
        "subprocess.check_call",
        "exec",
        "eval",
    },
    "path_traversal": {
        "open",
        "io.open",
        "Path.open",
        "Path.read_text",
        "Path.read_bytes",
        "send_file",
        "send_from_directory",
    },
    "insecure_deserialization": {
        "pickle.load",
        "pickle.loads",
        "yaml.load",
        "marshal.load",
        "marshal.loads",
        "jsonpickle.decode",
    },
    "xss": {
        "render_template_string",
        "Markup",
    },
    "sensitive_logging": {
        "print",
        "logger.debug",
        "logger.info",
        "logger.warning",
        "logger.error",
        "logging.debug",
        "logging.info",
        "logging.warning",
        "logging.error",
    },
}


@dataclass
class FunctionInfo:
    name: str
    qualname: str
    file_path: str
    lineno: int
    params: List[str]
    node: ast.AST
    class_name: Optional[str] = None


@dataclass
class FindingRecord:
    vuln_type: str
    severity: str
    title: str
    description: str
    plain_impact: str
    file_path: str
    line_number: int
    function_name: Optional[str]
    vulnerable_code: str
    mitre_technique: Optional[str] = None
    mitre_tactic: Optional[str] = None
    extra: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "vuln_type": self.vuln_type,
            "severity": self.severity,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "function_name": self.function_name,
            "title": self.title,
            "description": self.description,
            "plain_impact": self.plain_impact,
            "vulnerable_code": self.vulnerable_code,
            "mitre_technique": self.mitre_technique,
            "mitre_tactic": self.mitre_tactic,
            "extra": self.extra,
        }


def _entropy(value: str) -> float:
    if not value:
        return 0.0
    frequency: Dict[str, int] = {}
    for char in value:
        frequency[char] = frequency.get(char, 0) + 1
    return -sum((count / len(value)) * math.log2(count / len(value)) for count in frequency.values())


def _full_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _full_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return _full_name(node.func)
    return ""


class PythonTaintEngine:
    def __init__(self, file_info: Dict):
        self.file_info = file_info
        self.file_path = file_info["path"]
        self.content = file_info["content"]
        self.lines = self.content.splitlines()
        self.tree = ast.parse(self.content)
        self.findings: List[FindingRecord] = []
        self.functions: Dict[str, FunctionInfo] = {}
        self.simple_name_index: Dict[str, List[str]] = {}
        self._collect_functions()

    def analyze(self) -> List[Dict]:
        self._analyze_block(self.tree.body, {}, scope_name=None, call_stack=[])
        for function in self.functions.values():
            self._analyze_function(function, initial_taint=set(), call_stack=[])
        self._detect_high_entropy_strings()
        self._detect_missing_auth_routes()
        return [finding.to_dict() for finding in self.findings]

    def _collect_functions(self) -> None:
        class Collector(ast.NodeVisitor):
            def __init__(self, engine: "PythonTaintEngine"):
                self.engine = engine
                self.class_stack: List[str] = []

            def visit_ClassDef(self, node: ast.ClassDef):
                self.class_stack.append(node.name)
                self.generic_visit(node)
                self.class_stack.pop()

            def visit_FunctionDef(self, node: ast.FunctionDef):
                self._store(node)
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
                self._store(node)
                self.generic_visit(node)

            def _store(self, node: ast.AST):
                args = getattr(node, "args", None)
                params: List[str] = []
                if args:
                    for arg in list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs):
                        params.append(arg.arg)
                    if args.vararg:
                        params.append(args.vararg.arg)
                    if args.kwarg:
                        params.append(args.kwarg.arg)
                name = getattr(node, "name", "unknown")
                qualname = ".".join(self.class_stack + [name]) if self.class_stack else name
                info = FunctionInfo(
                    name=name,
                    qualname=qualname,
                    file_path=self.engine.file_path,
                    lineno=getattr(node, "lineno", 1),
                    params=params,
                    node=node,
                    class_name=self.class_stack[-1] if self.class_stack else None,
                )
                self.engine.functions[qualname] = info
                self.engine.simple_name_index.setdefault(name, []).append(qualname)

        Collector(self).visit(self.tree)

    def _analyze_function(self, function: FunctionInfo, initial_taint: Set[str], call_stack: List[str]) -> bool:
        if function.qualname in call_stack:
            return False
        env = {param: (param in initial_taint) for param in function.params}
        stack = call_stack + [function.qualname]
        return self._analyze_block(function.node.body, env, scope_name=function.qualname, call_stack=stack)

    def _analyze_block(
        self,
        statements: List[ast.stmt],
        env: Dict[str, bool],
        scope_name: Optional[str],
        call_stack: List[str],
    ) -> bool:
        return_tainted = False
        for statement in statements:
            return_tainted = self._analyze_statement(statement, env, scope_name, call_stack) or return_tainted
        return return_tainted

    def _analyze_statement(
        self,
        statement: ast.stmt,
        env: Dict[str, bool],
        scope_name: Optional[str],
        call_stack: List[str],
    ) -> bool:
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            value = statement.value if isinstance(statement, ast.AnnAssign) else statement.value
            tainted = self._expr_tainted(value, env, scope_name, call_stack)
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            self._assign_targets(targets, tainted, env)
            return False

        if isinstance(statement, ast.AugAssign):
            tainted = self._expr_tainted(statement.value, env, scope_name, call_stack) or self._expr_tainted(
                statement.target, env, scope_name, call_stack
            )
            self._assign_targets([statement.target], tainted, env)
            return False

        if isinstance(statement, ast.Return):
            return self._expr_tainted(statement.value, env, scope_name, call_stack)

        if isinstance(statement, ast.Expr):
            self._handle_call(statement.value, env, scope_name, call_stack, statement)
            return False

        if isinstance(statement, ast.If):
            self._expr_tainted(statement.test, env, scope_name, call_stack)
            body_env = dict(env)
            self._analyze_block(statement.body, body_env, scope_name, call_stack)
            self._merge_env(env, body_env)
            else_env = dict(env)
            self._analyze_block(statement.orelse, else_env, scope_name, call_stack)
            self._merge_env(env, else_env)
            return False

        if isinstance(statement, (ast.For, ast.AsyncFor)):
            self._expr_tainted(statement.iter, env, scope_name, call_stack)
            self._assign_targets([statement.target], True, env)
            self._analyze_block(statement.body, env, scope_name, call_stack)
            self._analyze_block(statement.orelse, env, scope_name, call_stack)
            return False

        if isinstance(statement, ast.While):
            self._expr_tainted(statement.test, env, scope_name, call_stack)
            self._analyze_block(statement.body, env, scope_name, call_stack)
            self._analyze_block(statement.orelse, env, scope_name, call_stack)
            return False

        if isinstance(statement, ast.With):
            for item in statement.items:
                self._expr_tainted(item.context_expr, env, scope_name, call_stack)
                if item.optional_vars:
                    self._assign_targets([item.optional_vars], False, env)
            self._analyze_block(statement.body, env, scope_name, call_stack)
            return False

        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return False

        for child in ast.iter_child_nodes(statement):
            if isinstance(child, ast.expr):
                self._expr_tainted(child, env, scope_name, call_stack)
            elif isinstance(child, ast.stmt):
                self._analyze_statement(child, env, scope_name, call_stack)
        return False

    def _assign_targets(self, targets: List[ast.expr], tainted: bool, env: Dict[str, bool]) -> None:
        for target in targets:
            if isinstance(target, ast.Name):
                env[target.id] = env.get(target.id, False) or tainted
            elif isinstance(target, (ast.Tuple, ast.List)):
                for element in target.elts:
                    self._assign_targets([element], tainted, env)

    def _expr_tainted(
        self,
        node: Optional[ast.AST],
        env: Dict[str, bool],
        scope_name: Optional[str],
        call_stack: List[str],
    ) -> bool:
        if node is None:
            return False

        if isinstance(node, ast.Name):
            if node.id in env:
                return env.get(node.id, False)
            return node.id in USER_INPUT_NAMES

        if isinstance(node, ast.Constant):
            return False

        if isinstance(node, ast.Attribute):
            full_name = _full_name(node)
            if full_name in SOURCE_CALLS:
                return True
            return self._expr_tainted(node.value, env, scope_name, call_stack)

        if isinstance(node, ast.Subscript):
            return self._expr_tainted(node.value, env, scope_name, call_stack) or self._expr_tainted(
                node.slice, env, scope_name, call_stack
            )

        if isinstance(node, ast.BinOp):
            return self._expr_tainted(node.left, env, scope_name, call_stack) or self._expr_tainted(
                node.right, env, scope_name, call_stack
            )

        if isinstance(node, ast.JoinedStr):
            return any(
                self._expr_tainted(value.value, env, scope_name, call_stack)
                for value in node.values
                if isinstance(value, ast.FormattedValue)
            )

        if isinstance(node, ast.UnaryOp):
            return self._expr_tainted(node.operand, env, scope_name, call_stack)

        if isinstance(node, ast.BoolOp):
            return any(self._expr_tainted(value, env, scope_name, call_stack) for value in node.values)

        if isinstance(node, ast.Compare):
            return self._expr_tainted(node.left, env, scope_name, call_stack) or any(
                self._expr_tainted(comparator, env, scope_name, call_stack) for comparator in node.comparators
            )

        if isinstance(node, ast.Dict):
            return any(
                self._expr_tainted(value, env, scope_name, call_stack)
                for value in list(node.keys) + list(node.values)
                if value is not None
            )

        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return any(self._expr_tainted(element, env, scope_name, call_stack) for element in node.elts)

        if isinstance(node, ast.Call):
            return self._handle_call(node, env, scope_name, call_stack, node)

        if isinstance(node, ast.IfExp):
            return any(
                self._expr_tainted(part, env, scope_name, call_stack)
                for part in (node.test, node.body, node.orelse)
            )

        return any(self._expr_tainted(child, env, scope_name, call_stack) for child in ast.iter_child_nodes(node))

    def _handle_call(
        self,
        node: ast.Call,
        env: Dict[str, bool],
        scope_name: Optional[str],
        call_stack: List[str],
        origin_node: ast.AST,
    ) -> bool:
        callee_name = _full_name(node.func)
        arg_taints = [self._expr_tainted(arg, env, scope_name, call_stack) for arg in node.args]
        kw_taints = [self._expr_tainted(kw.value, env, scope_name, call_stack) for kw in node.keywords]
        any_tainted_arg = any(arg_taints) or any(kw_taints)

        if callee_name in SOURCE_CALLS:
            return True

        if callee_name in SANITIZER_CALLS:
            return False

        sink_map = {
            "sqli": "critical",
            "command_injection": "critical",
            "path_traversal": "high",
            "insecure_deserialization": "critical",
            "xss": "high",
            "sensitive_logging": "medium",
        }
        for vuln_type, sink_names in SINKS.items():
            if callee_name in sink_names or callee_name.endswith("." + next(iter(sink_names)).split(".")[-1]):
                if any_tainted_arg:
                    self._record_sink(origin_node, scope_name, vuln_type, node, env, sink_map[vuln_type])

        resolved = self._resolve_callees(callee_name)
        if resolved:
            for function in resolved:
                if function.qualname in call_stack:
                    continue
                call_taint = set()
                for index, arg in enumerate(node.args):
                    if index < len(function.params) and self._expr_tainted(arg, env, scope_name, call_stack):
                        call_taint.add(function.params[index])
                return_tainted = self._analyze_function(function, call_taint, call_stack)
                if return_tainted:
                    return True

        return any_tainted_arg

    def _resolve_callees(self, callee_name: str) -> List[FunctionInfo]:
        candidates: List[str] = []
        if callee_name in self.functions:
            candidates.append(callee_name)
        simple_name = callee_name.split(".")[-1]
        for qualname in self.simple_name_index.get(simple_name, []):
            if qualname not in candidates:
                candidates.append(qualname)
        return [self.functions[name] for name in candidates if name in self.functions]

    def _record_sink(
        self,
        node: ast.AST,
        scope_name: Optional[str],
        vuln_type: str,
        call_node: ast.Call,
        env: Dict[str, bool],
        severity: str,
    ) -> None:
        line_number = getattr(node, "lineno", getattr(call_node, "lineno", 1))
        function_name = scope_name.split(".")[-1] if scope_name else None
        vulnerable_code = self._line_for(line_number)

        title_map = {
            "sqli": "SQL Injection",
            "command_injection": "Command Injection",
            "path_traversal": "Path Traversal",
            "insecure_deserialization": "Insecure Deserialization",
            "xss": "Cross-Site Scripting (XSS)",
            "sensitive_logging": "Sensitive Data Logged",
        }
        description_map = {
            "sqli": "User-controlled input reaches a SQL execution sink without parameterization.",
            "command_injection": "User-controlled input reaches a shell execution sink.",
            "path_traversal": "User-controlled input reaches a file access sink without path normalization.",
            "insecure_deserialization": "Untrusted data reaches an unsafe deserialization sink.",
            "xss": "User-controlled input is rendered into an output sink without escaping.",
            "sensitive_logging": "Sensitive or user-controlled data is written to logs.",
        }
        impact_map = {
            "sqli": "An attacker can read or modify database records through crafted input.",
            "command_injection": "An attacker can execute arbitrary OS commands on the host.",
            "path_traversal": "An attacker can access arbitrary files on the server.",
            "insecure_deserialization": "An attacker may trigger code execution or object corruption.",
            "xss": "An attacker can run script in a victim's browser session.",
            "sensitive_logging": "Logs may expose credentials or tokens to anyone with log access.",
        }
        technique_map = {
            "sqli": ("T1190", "Initial Access"),
            "command_injection": ("T1059", "Execution"),
            "path_traversal": ("T1083", "Discovery"),
            "insecure_deserialization": ("T1190", "Initial Access"),
            "xss": ("T1059.007", "Execution"),
            "sensitive_logging": ("T1552", "Credential Access"),
        }
        technique, tactic = technique_map.get(vuln_type, (None, None))

        self._add_finding(
            FindingRecord(
                vuln_type=vuln_type,
                severity=severity,
                title=title_map[vuln_type],
                description=description_map[vuln_type],
                plain_impact=impact_map[vuln_type],
                file_path=self.file_path,
                line_number=line_number,
                function_name=function_name,
                vulnerable_code=vulnerable_code.strip(),
                mitre_technique=technique,
                mitre_tactic=tactic,
                extra={
                    "call": _full_name(call_node.func),
                    "tainted_args": any(self._expr_tainted(arg, env, scope_name, []) for arg in call_node.args),
                },
            )
        )

    def _add_finding(self, finding: FindingRecord) -> None:
        key = (finding.vuln_type, finding.file_path, finding.line_number, finding.function_name)
        for existing in self.findings:
            existing_key = (existing.vuln_type, existing.file_path, existing.line_number, existing.function_name)
            if existing_key == key:
                return
        self.findings.append(finding)

    def _merge_env(self, env: Dict[str, bool], branch_env: Dict[str, bool]) -> None:
        for key, value in branch_env.items():
            env[key] = env.get(key, False) or value

    def _line_for(self, line_number: int) -> str:
        if 1 <= line_number <= len(self.lines):
            return self.lines[line_number - 1]
        return ""

    def _detect_high_entropy_strings(self) -> None:
        import re

        for index, line in enumerate(self.lines, start=1):
            for candidate in re.findall(r"['\"]([a-zA-Z0-9+/=_\-]{20,})['\"]", line):
                if _entropy(candidate) > 4.5:
                    self._add_finding(
                        FindingRecord(
                            vuln_type="high_entropy_secret",
                            severity="high",
                            title="Possible Hardcoded Secret (high entropy)",
                            description="High-entropy string detected that may be a secret or key.",
                            plain_impact="This string may be a credential or key embedded in code.",
                            file_path=self.file_path,
                            line_number=index,
                            function_name=None,
                            vulnerable_code=line.strip(),
                            mitre_technique="T1552.001",
                            mitre_tactic="Credential Access",
                        )
                    )

    def _detect_missing_auth_routes(self) -> None:
        class RouteVisitor(ast.NodeVisitor):
            def __init__(self, engine: "PythonTaintEngine"):
                self.engine = engine

            def visit_FunctionDef(self, node: ast.FunctionDef):
                self._inspect(node)
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
                self._inspect(node)
                self.generic_visit(node)

            def _inspect(self, node: ast.AST) -> None:
                decorator_names = [self.engine._decorator_name(item) for item in getattr(node, "decorator_list", [])]
                route_like = any(
                    name and any(token in name for token in ("route", "get", "post", "put", "delete", "patch"))
                    for name in decorator_names
                )
                if not route_like:
                    return

                protected = any(
                    name and any(token in name for token in ("auth", "login_required", "jwt_required", "permission", "csrf"))
                    for name in decorator_names
                )
                if protected:
                    return

                methods = self.engine._route_methods(node)
                if not methods or methods.isdisjoint({"post", "put", "patch", "delete"}):
                    return

                self.engine._add_finding(
                    FindingRecord(
                        vuln_type="missing_auth",
                        severity="high",
                        title="Potentially Unprotected Route",
                        description="A state-changing route appears to be missing authentication checks.",
                        plain_impact="Unauthenticated users might be able to perform privileged actions.",
                        file_path=self.engine.file_path,
                        line_number=getattr(node, "lineno", 1),
                        function_name=getattr(node, "name", None),
                        vulnerable_code=self.engine._line_for(getattr(node, "lineno", 1)).strip(),
                        mitre_technique="T1078",
                        mitre_tactic="Defense Evasion",
                    )
                )

        RouteVisitor(self).visit(self.tree)

    def _decorator_name(self, decorator: ast.AST) -> str:
        if isinstance(decorator, ast.Call):
            return _full_name(decorator.func)
        return _full_name(decorator)

    def _route_methods(self, node: ast.AST) -> Set[str]:
        methods: Set[str] = set()
        for decorator in getattr(node, "decorator_list", []):
            if not isinstance(decorator, ast.Call):
                continue
            decorator_name = self._decorator_name(decorator).lower()
            for token in ("post", "put", "patch", "delete", "get"):
                if token in decorator_name:
                    methods.add(token)
            for keyword in decorator.keywords:
                if keyword.arg == "methods" and isinstance(keyword.value, (ast.List, ast.Tuple, ast.Set)):
                    for element in keyword.value.elts:
                        if isinstance(element, ast.Constant) and isinstance(element.value, str):
                            methods.add(element.value.lower())
        return methods


def scan_python_file(file_info: Dict) -> List[Dict]:
    try:
        return PythonTaintEngine(file_info).analyze()
    except SyntaxError as exc:
        log.warning("Skipping Python file with syntax errors", path=file_info.get("path"), error=str(exc))
        return []
    except Exception as exc:
        log.warning("Python taint analysis failed", path=file_info.get("path"), error=str(exc))
        return []
