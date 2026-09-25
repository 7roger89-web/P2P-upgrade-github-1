from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / ".p2p" / "system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from p2p_capabilities import owner_goal  # type: ignore


def test_arena_new_chat_packet_starts_with_human_task_title() -> None:
    with tempfile.TemporaryDirectory(prefix="p2p-arena-title-") as directory:
        handoff = owner_goal.build_arena_handoff(
            Path(directory),
            {
                "goal_id": "VNLAW_VBPL_OFFICIAL_WS_PROBE_01",
                "objective": "Official VBPL WebSocket Probe",
            },
            None,
            "ARENA",
        )

    lines = handoff["packet_text"].splitlines()
    title = handoff["chat_title"]

    assert title.endswith(" — Official VBPL WebSocket Probe")
    assert "\\n" not in title
    assert lines[0] == title
    assert " — " in title
    assert lines[1] == ""
    assert lines[2] == "GỬI CHO: ARENA AI"
    assert f"CHAT_TITLE={title}" in lines
    assert not lines[0].startswith(("GỬI CHO:", "DESTINATION=", "TASK_ID=", "```", "P2P "))


def test_title_first_rule_is_in_canonical_and_transport_docs() -> None:
    paths = (
        ROOT / "docs" / "p2p-development" / "P2P-OPERATIONS-NOTEBOOK.md",
        ROOT / "docs" / "ARENA_AGENT_MODE_PROTOCOL.md",
        ROOT / "docs" / "p2p-development" / "P2P-AGENTS-INSTALL.md",
        ROOT / "docs" / "p2p-development" / "CONTROL-TOWER-SESSION-HANDOFF.md",
        ROOT / "docs" / "p2p-development" / "P2P-PROJECT-BOOTSTRAP.md",
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "ARENA_CHAT_TITLE_FIRST_LINE_V1" in text or (
            "<PROJECT> — <bounded task/outcome>" in text and "CHAT_TITLE" in text
        )

    notebook = paths[0].read_text(encoding="utf-8")
    assert "NEW_CHAT_FIRST_NONBLANK_LINE=<PROJECT> — <bounded task/outcome>" in notebook
    assert "ROUTING_BOILERPLATE_FIRST_LINE=NO" in notebook
