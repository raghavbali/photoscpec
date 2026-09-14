import ast
from pathlib import Path


def test_backend_has_no_frontend_dependencies():
    root = Path(__file__).resolve().parents[2] / "src" / "photoscpec"
    for area in ("core", "services", "config", "interfaces"):
        for path in (root / area).rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                names = []
                if isinstance(node, ast.Import):
                    names = [item.name for item in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                for name in names:
                    assert name.split(".")[0] not in {"streamlit", "frontend"}, path
