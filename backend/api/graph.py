"""Build DAG graph structure (from the live DAG files) and render it to a
Mermaid flowchart that the dashboard draws, optionally colored by task state.
"""

import os
from pathlib import Path

from backend.dag_engine.executor import topological_order
from backend.dag_engine.parser import DAGParser

STATE_CLASSES = {"success", "failed", "running", "queued", "skipped"}


def _parser():
    return DAGParser(dag_folder=os.getenv("DAG_FOLDER", "backend/dags"))


def get_structure(dag_id):
    """Return {'tasks': [ids in topo order], 'edges': [(up, down), ...]} or None."""
    dags = _parser().parse()
    dag = dags.get(dag_id)
    if dag is None:
        return None
    order = topological_order(dag)
    edges = [
        (tid, child.task_id)
        for tid in order
        for child in dag.tasks[tid].downstream
    ]
    return {"tasks": order, "edges": edges}


def get_source(dag_id):
    """Best-effort read of the DAG's source file."""
    folder = Path(os.getenv("DAG_FOLDER", "backend/dags"))
    candidate = folder / f"{dag_id}.py"
    if candidate.exists():
        return candidate.read_text(encoding="utf-8", errors="replace")
    # Fall back to scanning for the file that defines this dag_id.
    for path in folder.glob("*.py"):
        try:
            if f'"{dag_id}"' in path.read_text(encoding="utf-8") or \
               f"'{dag_id}'" in path.read_text(encoding="utf-8"):
                return path.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
    return "(source not found)"


def build_mermaid(structure, states=None):
    """Render a structure dict to a Mermaid flowchart definition."""
    states = states or {}
    ids = {t: f"n{i}" for i, t in enumerate(structure["tasks"])}

    lines = ["flowchart LR"]
    for t in structure["tasks"]:
        label = t.replace('"', "'")
        lines.append(f'  {ids[t]}["{label}"]')
    for up, down in structure["edges"]:
        lines.append(f"  {ids[up]} --> {ids[down]}")

    lines += [
        "  classDef success fill:#064e3b,stroke:#10b981,color:#d1fae5;",
        "  classDef failed fill:#7f1d1d,stroke:#ef4444,color:#fee2e2;",
        "  classDef running fill:#1e3a8a,stroke:#3b82f6,color:#dbeafe;",
        "  classDef queued fill:#374151,stroke:#9ca3af,color:#e5e7eb;",
        "  classDef skipped fill:#422006,stroke:#f59e0b,color:#fde68a;",
    ]
    for t, st in states.items():
        if t in ids and st in STATE_CLASSES:
            lines.append(f"  class {ids[t]} {st};")

    return "\n".join(lines)
