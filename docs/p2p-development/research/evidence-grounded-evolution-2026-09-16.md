# Evidence-Grounded Evolution — research adoption note

Date: 2026-09-16
Status: OWNER_SELECTED_IMPLEMENTATION
Canonical adoption record: `RA-EXT-071`

## Question

How can P2P agents improve from repeated work without turning raw chat history, model self-reflection, or an external memory framework into a second authority?

## Cross-source synthesis

The useful convergence across recent agent research and practitioner reports is not “let the model rewrite itself after every run”. It is an evidence-bound loop:

`DO -> OBSERVE -> VERIFY -> DIAGNOSE -> DISTILL -> TEST -> PROMOTE -> REUSE -> MEASURE -> REFINE/QUARANTINE`

Representative research directions reviewed include:

- Reflexion / CRITIC: feedback and external/tool-grounded critique are stronger than ungrounded self-correction.
- ExpeL / MUSE: successful and failed trajectories can be distilled into reusable experience rather than replaying raw history.
- ReMe: memory needs refinement, conflict handling and pruning/supersession rather than passive accumulation.
- MUSE-Autoskill: reusable skills benefit from explicit create/use/evaluate/refine lifecycle and tests.
- ADAS / AgentSquare / AFlow: workflow variants can be evaluated empirically instead of being promoted by narrative confidence.
- Darwin Gödel Machine: archive/champion-challenger style selection is safer than overwriting the only working agent.

Primary public references reviewed during the research pass:

- https://aclanthology.org/2026.findings-acl.2069/
- https://aclanthology.org/2026.findings-acl.1522/
- https://aclanthology.org/2026.findings-acl.829/
- https://openreview.net/forum?id=IkmD3fKBPQ
- https://proceedings.iclr.cc/paper_files/paper/2024/hash/fef126561bbf9d4467dbb8d27334b8fe-Abstract-Conference.html
- https://ojs.aaai.org/index.php/AAAI/article/view/29936
- https://proceedings.iclr.cc/paper_files/paper/2025/hash/36b7acf6f6010652b3f2a433774a66fe-Abstract-Conference.html
- https://proceedings.iclr.cc/paper_files/paper/2025/hash/0ae94013da7cd459402fd77874e09ee3-Abstract-Conference.html
- https://proceedings.iclr.cc/paper_files/paper/2025/hash/5492ecbce4439401798dcd2c90be94cd-Abstract-Conference.html
- https://arxiv.org/abs/2505.22954
- https://sakana.ai/dgm/

Community/practitioner sources were sampled across English, Chinese, Russian, Japanese and Brazilian Portuguese forums. Those reports repeatedly highlighted stale/conflicting memory, tool-use failure hidden by plausible final text, and the value of converting stable repeated workflows into deterministic procedures.

## P2P translation

Adopt the pattern, not an external control plane.

The first bounded slice is `p2p-experience-evolution/1`:

- durable storage reuses `.p2p/state/execution-ledger.jsonl` (`p2p-execution-event/1`);
- experience kinds are `STRATEGIC`, `PROCEDURAL`, and `TOOL`;
- lifecycle is `CANDIDATE -> VERIFIED -> ACTIVE -> SUPERSEDED | QUARANTINED`;
- agent/model self-report cannot establish candidate proof or verification proof;
- `VERIFIED` requires `BEHAVIOR_PROOF + REGRESSION_PROOF + CHALLENGE_PROOF`;
- only `ACTIVE` experience may be retrieved for a future task;
- retrieval is trigger-scoped and bounded; no full history preload;
- retrieved experience is `NON_AUTHORITATIVE_VERIFIED_EXPERIENCE` and must be checked against current law, task contract and current project state;
- use outcomes (`HELPED | NEUTRAL | HARMED`) are recorded as utility evidence;
- one harmful use recommends review but does not automatically erase history;
- quarantine and supersession are append-only logical state changes, not destructive deletion.

## Explicit non-goals

This slice does **not** create:

- a new agent identity, supervisor, router, control plane, truth store, vector database, daemon, or external memory service;
- automatic edits to Supreme Law, skills, prompts, capability registry, source code, deployment, permissions, secrets, or provider choice;
- acceptance authority from experience reuse;
- automatic architectural self-modification or champion/challenger mutation.

Those broader self-evolution directions remain future candidates and require a demonstrated native gap plus their own evidence and authority gates.

## Activation contract

Installed agents discover the runtime through `P2P-AGENTS-INSTALL.md` and the shipped `.p2p/system/p2p_capabilities/experience_evolution.py` helper.

Before a non-trivial task, the helper's read-only `retrieve` command may supply at most a small set of ACTIVE, trigger-matched experiences. `NO_MATCH` means normal P2P execution.

After a task, create an experience candidate only when the run produced a material/repeated failure lesson or a clearly reusable correction with independent evidence. Routine success is not a reason to manufacture memory.

A candidate remains inert until verification proves behavior, regression safety and an independent challenge. Activation changes only the eligibility of that lesson as bounded context. It never changes law, permissions or acceptance.

## Anti-overengineering verdict

`OE_VERDICT=DO_IT`

Reason: this closes a concrete lifecycle gap using the existing execution ledger and installed runtime path. It adds no second memory database, router, provider, daemon or external dependency. Broader self-modifying-agent work is deliberately deferred until a measured gap appears.
