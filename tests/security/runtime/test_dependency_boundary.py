import ast
from pathlib import Path


def test_runtime_has_no_forbidden_imports_or_io_primitives() -> None:
    root = Path(__file__).resolve().parents[3] / "packages" / "runtime" / "src" / "lengeas_runtime"
    forbidden = {
        "fastapi",
        "pymongo",
        "valkey",
        "redis",
        "celery",
        "kafka",
        "boto3",
        "requests",
        "httpx",
        "socket",
        "urllib",
        "pathlib",
        "os",
        "subprocess",
        "random",
        "secrets",
    }
    for source in root.rglob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not ({alias.name.split(".")[0] for alias in node.names} & forbidden), source
            elif isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in forbidden, source
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec", "compile"}, source
                assert not (node.func.id == "now"), source
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {"now", "today", "utcnow", "urandom"}, source
