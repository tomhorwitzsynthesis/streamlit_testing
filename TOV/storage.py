"""
storage.py — lightweight JSON storage with export/import for the Streamlit LLM Copy POC.

No external deps. Single file persistence with a clear, documented schema.

Schema (v1):
{
  "schema_version": 1,
  "guidelines": {"content": str, "version": int, "updated_at": iso8601},
  "projects": {
      "<project_name>": {
          "generations": [
              {
                "id": uuid4 str,
                "source": str,
                "instr": str|null,
                "tone": int,            # 0..3
                "length": "short|medium|long",
                "out": str,
                "liked": bool,
                "ts": iso8601
              }
          ]
      }
  },
  "current_project": str
}

Export format (v1):
{
  "type": "project_export",
  "schema_version": 1,
  "exported_at": iso8601,
  "project_name": str,
  "guidelines_snapshot": {"content": str, "version": int, "updated_at": iso8601},
  "project": { ... same as state["projects"][name] ... }
}
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import uuid

DATA_PATH = Path("data.json")
SCHEMA_VERSION = 1

# -------------------------
# Helpers
# -------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_state() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "guidelines": {"content": "", "version": 0, "updated_at": _now_iso()},
        "product_description": {"content": "", "version": 0, "updated_at": _now_iso()},
        "projects": {"Default": {"generations": []}},
        "current_project": "Default",
    }


# -------------------------
# Core load/save
# -------------------------

def ensure_store(path: Path = DATA_PATH) -> None:
    if not path.exists():
        save_state(_default_state(), path)


def load_state(path: Path = DATA_PATH) -> Dict[str, Any]:
    ensure_store(path)
    with path.open("r", encoding="utf-8") as f:
        state = json.load(f)
    if state.get("schema_version") != SCHEMA_VERSION:
        # For POC: naive forward-only handling — reset if incompatible
        # In production, add real migrations.
        return _default_state()
    return state


def save_state(state: Dict[str, Any], path: Path = DATA_PATH) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


# -------------------------
# Guidelines
# -------------------------

def get_guidelines(state: Dict[str, Any]) -> Tuple[str, int, str]:
    g = state.get("guidelines", {})
    return g.get("content", ""), int(g.get("version", 0)), g.get("updated_at", _now_iso())


def update_guidelines(state: Dict[str, Any], content: str) -> Dict[str, Any]:
    # Bump version if content changes
    cur = state.get("guidelines", {})
    if content.strip() != cur.get("content", "").strip():
        new_version = int(cur.get("version", 0)) + 1
        state["guidelines"] = {
            "content": content,
            "version": new_version,
            "updated_at": _now_iso(),
        }
    return state


def get_product_description(state: Dict[str, Any]) -> Tuple[str, int, str]:
    pd = state.get("product_description", {})
    return pd.get("content", ""), int(pd.get("version", 0)), pd.get("updated_at", _now_iso())


def update_product_description(state: Dict[str, Any], content: str) -> Dict[str, Any]:
    # Bump version if content changes
    cur = state.get("product_description", {})
    if content.strip() != cur.get("content", "").strip():
        new_version = int(cur.get("version", 0)) + 1
        state["product_description"] = {
            "content": content,
            "version": new_version,
            "updated_at": _now_iso(),
        }
    return state


# -------------------------
# Projects
# -------------------------

def list_projects(state: Dict[str, Any]) -> List[str]:
    return sorted(state.get("projects", {}).keys())


def ensure_project(state: Dict[str, Any], name: str) -> Dict[str, Any]:
    state.setdefault("projects", {})
    if name not in state["projects"]:
        state["projects"][name] = {"generations": []}
    return state


def create_project(state: Dict[str, Any], name: str, switch: bool = True) -> Dict[str, Any]:
    name = name.strip() or "Untitled"
    ensure_project(state, name)
    if switch:
        state["current_project"] = name
    return state


def rename_project(state: Dict[str, Any], old: str, new: str) -> Dict[str, Any]:
    new = new.strip()
    if not new or old not in state.get("projects", {}):
        return state
    if new in state["projects"]:
        # refuse overwrite for POC
        return state
    state["projects"][new] = state["projects"].pop(old)
    if state.get("current_project") == old:
        state["current_project"] = new
    return state


def delete_project(state: Dict[str, Any], name: str) -> Dict[str, Any]:
    # POC safety: do not allow deleting the last project
    if name in state.get("projects", {}) and len(state["projects"]) > 1:
        state["projects"].pop(name, None)
        if state.get("current_project") == name:
            state["current_project"] = next(iter(state["projects"].keys()))
    return state


def get_current_project(state: Dict[str, Any]) -> str:
    cur = state.get("current_project")
    if not cur or cur not in state.get("projects", {}):
        # self-heal
        cur = list(state.get("projects", {"Default": {}}).keys())[0]
        state["current_project"] = cur
    return cur


def set_current_project(state: Dict[str, Any], name: str) -> Dict[str, Any]:
    if name in state.get("projects", {}):
        state["current_project"] = name
    return state


# -------------------------
# Generations & Likes
# -------------------------

def _project_ref(state: Dict[str, Any], name: Optional[str] = None) -> Dict[str, Any]:
    if name is None:
        name = get_current_project(state)
    return state["projects"][name]


def add_generation(
    state: Dict[str, Any],
    *,
    source: str,
    instr: Optional[str],
    tone: int,
    length: str,
    out: str,
    project: Optional[str] = None,
) -> Dict[str, Any]:
    if project is None:
        project = get_current_project(state)
    ensure_project(state, project)
    gen = {
        "id": str(uuid.uuid4()),
        "source": source or "",
        "instr": instr or "",
        "tone": int(tone),
        "length": str(length),
        "out": out or "",
        "liked": False,
        "ts": _now_iso(),
    }
    _project_ref(state, project).setdefault("generations", []).append(gen)
    return state


def list_generations(state: Dict[str, Any], project: Optional[str] = None) -> List[Dict[str, Any]]:
    if project is None:
        project = get_current_project(state)
    return list(_project_ref(state, project).get("generations", []))


def get_generation(state: Dict[str, Any], gen_id: str, project: Optional[str] = None) -> Optional[Dict[str, Any]]:
    gens = list_generations(state, project)
    for g in gens:
        if g.get("id") == gen_id:
            return g
    return None


def set_like(state: Dict[str, Any], gen_id: str, liked: bool, project: Optional[str] = None) -> Dict[str, Any]:
    if project is None:
        project = get_current_project(state)
    gens = _project_ref(state, project).get("generations", [])
    for g in gens:
        if g.get("id") == gen_id:
            g["liked"] = bool(liked)
            break
    return state


def toggle_like(state: Dict[str, Any], gen_id: str, project: Optional[str] = None) -> Dict[str, Any]:
    g = get_generation(state, gen_id, project)
    if g is not None:
        g["liked"] = not bool(g.get("liked", False))
    return state


def list_liked(state: Dict[str, Any], project: Optional[str] = None) -> List[Dict[str, Any]]:
    return [g for g in list_generations(state, project) if g.get("liked")]


# -------------------------
# Export / Import
# -------------------------

def export_project_dict(state: Dict[str, Any], project_name: Optional[str] = None) -> Dict[str, Any]:
    name = project_name or get_current_project(state)
    if name not in state.get("projects", {}):
        raise ValueError(f"Unknown project: {name}")
    g_content, g_ver, g_updated = get_guidelines(state)
    payload = {
        "type": "project_export",
        "schema_version": SCHEMA_VERSION,
        "exported_at": _now_iso(),
        "project_name": name,
        "guidelines_snapshot": {
            "content": g_content,
            "version": g_ver,
            "updated_at": g_updated,
        },
        "project": state["projects"][name],
    }
    return payload


def export_project_to_file(state: Dict[str, Any], filepath: Path, project_name: Optional[str] = None) -> Path:
    payload = export_project_dict(state, project_name)
    filepath = Path(filepath)
    filepath.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return filepath


def _validate_import_payload(data: Dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ValueError("Import payload must be an object")
    if data.get("type") != "project_export":
        raise ValueError("Not a project_export payload")
    if int(data.get("schema_version", -1)) != SCHEMA_VERSION:
        raise ValueError("Schema version mismatch for POC")
    if "project" not in data or "project_name" not in data:
        raise ValueError("Missing project or project_name in payload")


def import_project_from_dict(state: Dict[str, Any], data: Dict[str, Any], *, rename_on_conflict: bool = True) -> Tuple[Dict[str, Any], str]:
    _validate_import_payload(data)
    base_name = str(data["project_name"]).strip() or "Imported"
    name = base_name
    if name in state.get("projects", {}) and rename_on_conflict:
        i = 2
        while f"{base_name} ({i})" in state["projects"]:
            i += 1
        name = f"{base_name} ({i})"
    # Deep copy-like assignment but ensure generation IDs are valid strings
    project_block = {"generations": []}
    for g in data.get("project", {}).get("generations", []):
        project_block["generations"].append({
            "id": str(g.get("id") or uuid.uuid4()),
            "source": g.get("source", ""),
            "instr": g.get("instr", ""),
            "tone": int(g.get("tone", 0)),
            "length": g.get("length", "short"),
            "out": g.get("out", ""),
            "liked": bool(g.get("liked", False)),
            "ts": g.get("ts", _now_iso()),
        })
    ensure_project(state, name)
    state["projects"][name] = project_block
    return state, name


def import_project_from_file(state: Dict[str, Any], filepath: Path, *, rename_on_conflict: bool = True) -> Tuple[Dict[str, Any], str]:
    payload = json.loads(Path(filepath).read_text(encoding="utf-8"))
    return import_project_from_dict(state, payload, rename_on_conflict=rename_on_conflict)


# -------------------------
# Convenience for Streamlit
# -------------------------

def persist_and_return(state: Dict[str, Any], path: Path = DATA_PATH) -> Dict[str, Any]:
    save_state(state, path)
    return load_state(path)
