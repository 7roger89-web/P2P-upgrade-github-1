"""P2P Project Context Bootstrap (01B).

Spec RM-PRIORITY-RELEASE-LIFECYCLE-01B:
- §5: Full Project Context Model (Identity, Constitution, Architecture, UI/Data Maps, Goal Graph).
- §8: Map is NOT Project Truth (Derived not canonical).
- §9: Map-Before-Work Runtime Enforcement (Mutation Gate).
- §10: Minimum-Sufficient Map Context (Task-scoped loading).
"""
import json
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple
from dataclasses import dataclass, field

try:
    from .context import retrieve_task_context, TASK_CONTEXT_SCHEMA
    from .project_map import ProjectMap
    from .project_pin import PROJECT_PIN_V2_SCHEMA, PROJECTION_ONLY, ProjectPinError, validate_pin
except ImportError:
    from context import retrieve_task_context, TASK_CONTEXT_SCHEMA
    from project_map import ProjectMap
    from project_pin import PROJECT_PIN_V2_SCHEMA, PROJECTION_ONLY, ProjectPinError, validate_pin

PROJECT_CONTEXT_READY_SCHEMA = "p2p-project-context-ready/2"

class ProjectContextError(Exception):
    pass

@dataclass
class ProjectContextModel:
    """Spec §5: Complete Project Context Model."""
    project_identity: Dict[str, Any]
    product_model: Dict[str, Any]
    constitution: Dict[str, Any]
    project_map: Any  # ProjectMap instance
    architecture_map: Dict[str, Any]
    ui_layout_map: Optional[Dict[str, Any]] = None
    data_map: Optional[Dict[str, Any]] = None
    decision_ledger: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    goal_graph: Dict[str, Any] = field(default_factory=dict)
    fingerprint: str = ""

class ProjectContextBootstrap:
    """Handles the bootstrap of project-native context and enforces invariants."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.p2p_dir = self.project_root / ".p2p"
        self.pin_path = self.p2p_dir / "project-pin.json"
        self.context_dir = self.p2p_dir / "context"
        self.map_path = self.context_dir / "project_map.json"
        self._pin = None
        self._map = None
        self._model = None

    def is_ready(self) -> bool:
        """Checks if the project context is bootstrapped and invariants are met."""
        if not self.pin_path.exists():
            return False
        try:
            pin = json.loads(self.pin_path.read_text(encoding="utf-8"))
            if pin.get("schema") == PROJECT_PIN_V2_SCHEMA and pin.get("mode") == PROJECTION_ONLY:
                # Projection-only readiness is deliberately independent from
                # packaged metadata and Doctor.  The v2 validator checks the
                # bound plan, files, policy/context, and NOT_INSTALLED claim.
                validate_pin(self.project_root)
            else:
                # Preserve the existing v1 packaged-runtime path verbatim.
                validate_pin(self.project_root, metadata_root=self.p2p_dir / "system")
            return True
        except (OSError, ProjectPinError, ValueError, TypeError, json.JSONDecodeError):
            return False

    def get_pin(self) -> Dict[str, Any]:
        if self._pin is None:
            if not self.pin_path.exists():
                raise ProjectContextError(f"Project not initialized: {self.project_root}")
            with open(self.pin_path, "r", encoding="utf-8") as f:
                self._pin = json.load(f)
        return self._pin

    def get_full_model(self, task_type: str = "GENERIC") -> ProjectContextModel:
        """Spec §5, §10: Minimum-sufficient loading of the project model."""
        pin = self.get_pin()
        
        # 1. Project Map (Mandatory)
        project_map = self.get_project_map()
        
        # 2. Architecture Map (Mandatory)
        arch_path = self.context_dir / "architecture_map.json"
        architecture = self._load_json_or_default(arch_path, {"schema": "p2p-architecture/1", "components": [], "status": "PROPOSED"})
        
        # 3. Task-specific maps (§10)
        ui_map = None
        if task_type == "UI":
            ui_map = self._load_json_or_default(self.context_dir / "ui_layout_map.json", {"schema": "p2p-ui-layout/1", "status": "PROPOSED"})
            
        data_map = None
        if task_type == "DATA":
            data_map = self._load_json_or_default(self.context_dir / "data_map.json", {"schema": "p2p-data-model/1", "status": "PROPOSED"})

        # 4. Constitution & Identity
        identity = {
            "name": pin.get("project_name", self.project_root.name),
            "version": pin.get("project_version", "0.0.1"),
            "fingerprint": pin.get("project_fingerprint", "")
        }
        
        constitution = self._load_json_or_default(self.context_dir / "constitution.json", {"rules": [], "principles": []})
        
        model = ProjectContextModel(
            project_identity=identity,
            product_model=pin.get("product_model", {}),
            constitution=constitution,
            project_map=project_map,
            architecture_map=architecture,
            ui_layout_map=ui_map,
            data_map=data_map,
            decision_ledger=self._load_json_or_default(self.context_dir / "decision_ledger.json", []),
            constraints=self._load_json_or_default(self.context_dir / "constraints.json", []),
            goal_graph=self._load_json_or_default(self.context_dir / "goal_graph.json", {})
        )
        
        # Compute fingerprint (§5)
        model.fingerprint = self._compute_model_fingerprint(model)
        self._model = model
        return model

    def _load_json_or_default(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    def _compute_model_fingerprint(self, model: ProjectContextModel) -> str:
        data = f"{model.project_identity.get('fingerprint')}-{model.project_map.identity()}"
        return hashlib.sha256(data.encode()).hexdigest()

    def get_project_map(self, force_refresh: bool = False) -> Any:
        """Spec §8: Map is derived, not canonical truth."""
        if self._map is None and not force_refresh and self.map_path.is_file():
            try:
                from .project_map import ProjectMap
            except ImportError:
                from project_map import ProjectMap
            try:
                self._map = ProjectMap.from_dict(
                    json.loads(self.map_path.read_text(encoding="utf-8")))
            except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                raise ProjectContextError(
                    f"PROJECT_MAP_INVALID: {self.map_path}: {exc}") from exc
        if self._map is None:
            try:
                from .project_map import ProjectMapBuilder
            except ImportError:
                from project_map import ProjectMapBuilder
            
            builder = ProjectMapBuilder(str(self.project_root))
            self._map = builder.build_full_map()
            
            # Check freshness (§8)
            freshness_info = self._map.check_freshness(str(self.project_root))
            if freshness_info.get("status") == "STALE":
                # In 01B, we enforce refresh before mutation
                pass
        return self._map

    def save_project_map(self, project_map: Any | None = None) -> Any:
        """Persist a derived map explicitly; this does not make it truth."""
        pmap = project_map if project_map is not None else self.get_project_map()
        if not hasattr(pmap, "to_dict"):
            raise ProjectContextError("PROJECT_MAP_NOT_SERIALIZABLE")
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self.map_path.write_text(
            json.dumps(pmap.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8")
        return pmap

    def bootstrap_new_project(self, intent: str):
        """Spec §6: Bootstrap zero-code fixture."""
        self.p2p_dir.mkdir(parents=True, exist_ok=True)
        self.context_dir.mkdir(parents=True, exist_ok=True)
        
        # Bootstrap is proposal-only.  It must never mint a canonical project
        # pin or claim readiness without a normal packaged installation.
        proposal = {
            "schema": "p2p-project-bootstrap-proposal/1",
            "intent": intent,
            "status": "PROPOSED",
            "product_model": {"status": "PROPOSED"},
        }
        with open(self.context_dir / "project-bootstrap-proposal.json", "w", encoding="utf-8") as f:
            json.dump(proposal, f, indent=2)
            
        # Create Proposed Maps (§6)
        proposed_maps = {
            "architecture_map.json": {"status": "PROPOSED", "components": []},
            "constitution.json": {"status": "PROPOSED", "rules": []},
            "goal_graph.json": {"status": "PROPOSED", "nodes": []}
        }
        for name, content in proposed_maps.items():
            with open(self.context_dir / name, "w") as f:
                json.dump(content, f, indent=2)

def enforce_map_before_work(
        project_root: Path,
        mutation_intent: bool = False,
        *,
        permission_granted: bool = True):
    """Spec §9: Real dispatch/mutation path enforcement."""
    bootstrap = ProjectContextBootstrap(project_root)
    if not bootstrap.is_ready():
        raise ProjectContextError("MAP_BEFORE_WORK_VIOLATION: Project context not ready.")
    
    if mutation_intent and not permission_granted:
        raise ProjectContextError(
            "MAP_BEFORE_WORK_VIOLATION: project permission denied.")
    if mutation_intent and not bootstrap.map_path.is_file():
        raise ProjectContextError(
            "MAP_BEFORE_WORK_VIOLATION: NO_PROJECT_MAP. Mutation blocked.")

    # Spec §8: Map is NOT project truth. Evidence wins.
    pmap = bootstrap.get_project_map(force_refresh=False)
    freshness_info = pmap.check_freshness(str(project_root))
    if freshness_info.get("status") == "STALE":
        # Mutation blocked on stale map (§9)
        if mutation_intent:
            raise ProjectContextError(f"MAP_BEFORE_WORK_VIOLATION: Project map is STALE. Mutation blocked. Drift: {freshness_info.get('drift_count')} files.")
    
    return True
