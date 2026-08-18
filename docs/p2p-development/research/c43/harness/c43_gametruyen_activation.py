"""C43 Game Truyện P2P activation proof — dispatch via the INSTALLED P2P
manus_adapter (in the target's .p2p/system) so the package itself is
proven on the target. Read-only by prompt contract.

Evidence: /home/ubuntu/p2p-repo/docs/p2p-development/research/c43/evidence/
"""
import hashlib
import os
import sys

P2P_SYSTEM = "/home/ubuntu/game-truyen-production/.p2p/system"
sys.path.insert(0, P2P_SYSTEM)
from p2p_capabilities.manus_adapter import ManusAdapter  # noqa: E402

API_KEY_PATH = "/home/ubuntu/.secrets/manus_api_key_new"
EVIDENCE_DIR = "/home/ubuntu/p2p-repo/docs/p2p-development/research/c43/evidence"
REQUEST_ID = "c43-gametruyen-activation"


def build_prompt() -> str:
    paths = {
        "TASKS.md": "/home/ubuntu/game-truyen-production/TASKS.md",
        "README": "/home/ubuntu/game-truyen-production/README_V09818_NARRATIVE_SIMULATION.md",
    }
    budget = 24000
    total = 0
    files = []
    for name, path in paths.items():
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except FileNotFoundError:
            continue
        if total + len(text) > budget:
            text = text[: max(3000, budget - total)]
        total += len(text)
        files.append((name, text))
        if total >= budget:
            break
    sections = "\n\n".join(f"### {n}\n{t}" for n, t in files)
    prompt = (
        "P2P đã được cài đặt vào dự án game-truyen-github (Python narrative "
        "simulation game, app.py/engine/pages/ui). NHIỆM VỤ CỦA BẠN HOÀN TOÀN "
        "READ-ONLY — KHÔNG sửa/ghi bất kỳ file nào của dự án, KHÔNG commit, "
        "KHÔNG chạy app, KHÔNG gọi API bên ngoài dự án.\n\n"
        f"ĐỌC các tài liệu dự án sau:\n\n{sections}\n\n"
        "Trả lời theo đúng định dạng này:\n"
        "N-next: <một nhiệm vụ cụ thể, an toàn, dành cho người mới, tiếp theo "
        "của dự án dựa trên nội dung tài liệu trên>\n"
        "Lý do: <một câu>\n"
        "IMPORTANT: chỉ đề xuất, không thực hiện bất kỳ thay đổi nào."
    )
    assert len(prompt) <= 26000, len(prompt)
    return prompt


def main() -> None:
    key = open(API_KEY_PATH, encoding="utf-8").read().strip()
    prompt = build_prompt()
    adapter = ManusAdapter(api_key=key)
    result = adapter.execute(
        request_id=REQUEST_ID,
        request_fingerprint=hashlib.sha256(prompt.encode()).hexdigest(),
        task_id="game-truyen-production",
        goal_id="c43-activation",
        prompt=prompt,
        timeout_seconds=600,
        title="P2P-C43 activation Game Truyện",
        agent_profile="manus-1.6-lite",
        evidence_dir=EVIDENCE_DIR,
    )
    print(result.json(indent=2))
    if result.execution_status != "SUCCEEDED":
        sys.exit(1)


if __name__ == "__main__":
    main()
