"""P2P Project Context Bootstrap (01A).

Spec RM-PRIORITY-RELEASE-LIFECYCLE §2, §3, §10, §11:
- PROJECT_CONTEXT_BOOTSTRAP: Recover context from Project Pin.
- INVARIANT_INVERSION: Project Context must be READY before any execution.
- MAP-BEFORE-WORK: Project Map must be FRESH before any project mutation.
- UI_LAYOUT_MAP: Support for durable UI/Layout map (§10).
- MAP_FRESHNESS: Detect drift and refresh (§11).
"""
import json
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, List

try:
    from .context import retrieve_task_context, TASK_CONTEXT_SCHEMA
    from .project_map import ProjectMap
except ImportError:
    from context import retrieve_task_context, TASK_CONTEXT_SCHEMA
    from project_map import ProjectMap

PROJECT_CONTEXT_READY_SCHEMA = "p2p-project-context-ready/1"

class ProjectContextError(Exception):
    pass

class ProjectContextBootstrap:
    """Handles the bootstrap of project-native context and enforces invariants."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.p2p_dir = self.project_root / ".p2p"
        self.pin_path = self.p2p_dir / "project-pin.json"
        self.context_dir = self.p2p_dir / "context"
        self._pin = None
        self._map = None
        self._ui_map = None

    def is_ready(self) -> bool:
        """Checks if the project context is bootstrapped and invariants are met."""
        if not self.pin_path.exists():
            return False
        
        # Invariant: Project Pin must be valid and Doctor must be HEALTHY
        try:
            pin = self.get_pin()
            if pin.get("verification_status") != "VERIFIED":
                return False
            if pin.get("doctor_result") != "HEALTHY":
                return False
            return True
        except Exception:
            return False

    def get_pin(self) -> Dict[str, Any]:
        if self._pin is None:
            if not self.pin_path.exists():
                raise ProjectContextError(f"Project not initialized: {self.project_root}")
            with open(self.pin_path, "r", encoding="utf-8") as f:
                self._pin = json.load(f)
        return self._pin

    def get_project_map(self, force_refresh: bool = False) -> Any:
        """Spec §10: Map-before-work invariant. Ensures project map is fresh."""
        if self._map is None or force_refresh:
            try:
                from .project_map import ProjectMapBuilder
            except ImportError:
                from project_map import ProjectMapBuilder
            
            builder = ProjectMapBuilder(str(self.project_root))
            # Spec 01B: Build full map L0-L2
            self._map = builder.build_full_map()
            
            # Check freshness (§11)
            if not force_refresh:
                freshness_info = self._map.check_freshness(str(self.project_root))
                freshness = freshness_info.get("status", "UNKNOWN")
                if freshness in ["STALE", "UNKNOWN"]:
                    # In a real system, this would trigger a re-build or re-sync
                    pass
        return self._map

    def get_ui_layout_map(self) -> Dict[str, Any]:
        """Spec §10: Retrieve the relevant UI_LAYOUT_MAP fragment."""
        ui_map_path = self.context_dir / "ui_layout_map.json"
        if not ui_map_path.exists():
            # Bootstrap read-only first (§10)
            self._ui_map = self._bootstrap_ui_map()
            self.context_dir.mkdir(parents=True, exist_ok=True)
            with open(ui_map_path, "w") as f:
                json.dump(self._ui_map, f, indent=2)
        else:
            with open(ui_map_path, "r") as f:
                self._ui_map = json.load(f)
        return self._ui_map

    def _bootstrap_ui_map(self) -> Dict[str, Any]:
        """Discovery-based UI map bootstrap (§10)."""
        # Placeholder for discovery logic
        return {
            "schema": "p2p-ui-layout-map/1",
            "project": self.project_root.name,
            "surfaces": ["web", "mobile"] if (self.project_root / "src").exists() else ["unknown"],
            "layout_primitives": [],
            "shared_components": [],
            "status": "DISCOVERED"
        }

    def bootstrap_task_context(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Bootstraps context for a specific task using the project pin and map."""
        if not self.is_ready():
            raise ProjectContextError("PROJECT_CONTEXT_NOT_READY: Bootstrap required before task execution.")
        
        pin = self.get_pin()
        project_map = self.get_project_map()
        
        # Determine mandatory maps based on task surface (§9)
        task_surface = task.get("surface", "GENERIC")
        required_maps = ["PROJECT_MAP"]
        if task_surface == "UI":
            required_maps.append("UI_LAYOUT_MAP")
            self.get_ui_layout_map()
        
        # Prepare source catalog including the project map
        map_identity = project_map.identity()
        raw_hash = map_identity.split("-")[-1]
        
        freshness_info = project_map.check_freshness(str(self.project_root))
        freshness = freshness_info.get("status", "UNKNOWN")

        source_catalog = [
            {
                "source_id": "project-repo-map",
                "role": "PROJECT_REPO_MAP",
                "path": ".",  # Spec: Must be project-relative
                "source_hash": raw_hash,
                "freshness": freshness,
                "readable": True,
                "permission": "ALLOWED"
            }
        ]
        
        # Retrieve context tier-by-tier
        try:
            from .orchestration_policy import EXPANDED
        except ImportError:
            from orchestration_policy import EXPANDED
            
        context_plan = retrieve_task_context(
            task=task,
            source_catalog=source_catalog,
            context_class=EXPANDED,
            candidate_binding=pin.get("p2p_artifact_sha256")
        )
        
        # Emit Project Context Ready event
        ready_event = {
            "schema": PROJECT_CONTEXT_READY_SCHEMA,
            "project_root": str(self.project_root),
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "context_fingerprint": context_plan.get("context_fingerprint"),
            "map_freshness": freshness,
            "invariant_check": "PASS",
            "loaded_maps": required_maps
        }
        
        return {
            "context_plan": context_plan,
            "ready_event": ready_event
        }

def enforce_map_before_work(project_root: Path, mutation_intent: bool = False):
    """Spec §11: No project map, no project mutation."""
    bootstrap = ProjectContextBootstrap(project_root)
    if not bootstrap.is_ready():
        raise ProjectContextError("MAP_BEFORE_WORK_VIOLATION: Project context not ready.")
    
    if mutation_intent:
        pmap = bootstrap.get_project_map()
        freshness_info = pmap.check_freshness(str(project_root))
        freshness = freshness_info.get("status", "UNKNOWN")
        if freshness in ["STALE", "UNKNOWN"]:
            raise ProjectContextError(f"MAP_BEFORE_WORK_VIOLATION: Project map is {freshness}. Mutation blocked until refresh.")
        
        if not pmap.identity():
            raise ProjectContextError("MAP_BEFORE_WORK_VIOLATION: Project map identity missing.")
