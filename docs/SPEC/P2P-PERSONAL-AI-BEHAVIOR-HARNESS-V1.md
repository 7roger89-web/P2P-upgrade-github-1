# P2P PERSONAL AI BEHAVIOR HARNESS V1

Status: `CANDIDATE_UNPROMOTED`

Purpose: define the smallest behavior/style harness needed by the existing Personal AI Assistant direction without creating a second assistant platform, a simulated-human framework, or a new memory infrastructure.

## 1. Owner outcome

The personal assistant should remain recognizably consistent across model/provider changes while preserving factual correctness and adapting response behavior to the current task.

The behavior layer must support:

- stable communication preferences;
- explicit serious-mode override;
- pre-generation response decisions such as research/tool/answer/question;
- anti-slop checks for obvious generic chatbot language;
- memory learning as staged candidates rather than uncontrolled self-editing;
- future open-loop/agenda support using existing scheduler/storage capabilities when a real workflow requires it.

It must not change authoritative business facts, fabricate a human identity, or turn personality simulation into the main architecture.

## 2. Research provenance and clean-room boundary

A research review of `AnnenkovLabs/girl-agent` was performed against upstream commit:

`6e40d834c1ff1d614ca2c450c5d66285956c85e9` (`v0.4.12`, 2026-07-18).

Useful generic patterns observed included separation of behavioral state from response generation, a pre-response decision layer, memory categorization/retrieval, reflection, and agenda/open-loop behavior.

The upstream project uses a restrictive source-available Contribution-Only license. This P2P slice therefore follows a clean-room rule:

- no upstream source code is copied;
- no upstream prompts are copied;
- no character/relationship simulation model is copied;
- no names, schemas, storage layout, interaction mechanics, or distinctive persona behaviors are reused;
- the upstream repository remains research/reference only;
- P2P implementation is independently defined from P2P requirements and existing Personal AI Assistant architecture.

This file is not a claim of license compatibility for redistributing or commercializing upstream software. P2P does not vendor or depend on `girl-agent`.

## 3. Architecture

Existing direction remains authoritative:

```text
Telegram / Discord
    -> Hermes gateway
    -> STT when input is voice
    -> intent + context
    -> authoritative data / tools / documents
    -> fact lock
    -> behavior controller
    -> voice/style renderer
    -> anti-slop check
    -> text response and/or TTS
```

The behavior harness is deliberately thin. It does not replace Hermes, tools, retrieval, TTS, factual stores, cron, or platform memory.

### 3.1 Fact boundary

Canonical invariant:

```text
FACTS != STYLE
STYLE_MAY_CHANGE_WORDING
STYLE_MUST_NOT_CHANGE_LOCKED_FACTS
```

Amounts, currencies, units, routes, vehicle/container types, dates, effective periods, business conditions, IDs, and other authoritative values remain outside the style state.

The renderer receives locked facts as a separate payload. Any post-render verification may compare those values before/after rendering. The style checker itself does not rewrite factual payloads.

## 4. Voice profile

The voice profile is structured state, not one giant prose prompt.

Representative Owner profile:

```yaml
voice_profile:
  language: vi
  familiarity: high
  directness: 0.90
  humor: 0.45
  sarcasm: 0.65
  corporate_tolerance: 0.05
  mild_profanity: true
  fresh_vietnamese_association: true
  no_generic_offer_at_end: true
  no_sycophantic_opener: true
```

Interpretation:

- Vietnamese is the default conversational language.
- Directness is high; filler is low.
- Humor/sarcasm are allowed but subordinate to correctness.
- Mild profanity may be natural but must not target the Owner.
- A Vietnamese analogy/association should clarify the subject rather than decorate every paragraph.
- Do not merely mirror the Owner's metaphor.
- Explicit serious-mode requests override humor/sarcasm immediately for that response.

This profile is wording behavior only. It has no authority over task scope, safety, facts, tools, deployment, or P2P governance.

## 5. Response controller

Before generation, resolve a small response policy from task signals.

Current deterministic signals:

```text
explicit_serious
blocking_ambiguity
requires_fresh_information
requires_tool
user_requested_short
user_requested_deep
```

Decision shape:

```text
blocking ambiguity -> ASK_ONLY_IF_BLOCKING
otherwise:
  fresh information -> RESEARCH_FIRST
  required tool      -> USE_REQUIRED_TOOL
  neither            -> ANSWER_DIRECTLY
```

Depth is independently selected as `short | normal | deep`.

This controller does not attempt semantic mind-reading. Upstream task/router/tool logic is responsible for setting the signals.

### Why this exists

The model should not decide every response property implicitly in prose generation. A small deterministic policy keeps behaviors such as serious override, tool-first execution, and blocking-question suppression consistent across model families.

## 6. Anti-slop check

The first slice implements a conservative deterministic lint pass after generation.

It detects only strong markers such as:

- generic praise openers (`Câu hỏi rất hay`, `Ý tưởng rất hay`);
- generic understanding claims (`Tôi hoàn toàn hiểu`);
- generic completed-task follow-up offers (`Nếu bạn muốn, tôi có thể...`);
- customer-service filler (`Rất vui được hỗ trợ`, `Xin vui lòng cho biết`).

The linter intentionally does **not** attempt to regex-score whether a joke is funny, whether an analogy is culturally good, whether a sentence is sufficiently Vietnamese, or whether prose feels human. Those are semantic judgments and false-positive magnets.

Canonical rule:

```text
LINT_FINDING != FACT_REWRITE_AUTHORITY
```

V1 reports findings. A later model-assisted repair pass is deferred until a real runtime integration can prove it preserves fact-lock invariants.

## 7. Memory learning contract

Conversation reflection may create a `MemoryCandidate`; reflection itself does not write durable memory.

Required separation:

```text
conversation
   -> reflection/extraction
   -> memory candidate
      -> explicit owner instruction -> PROMOTE_ELIGIBLE
      -> uncertain inference         -> HOLD_UNCERTAIN
      -> repeated confirmed signal   -> REVIEW_ELIGIBLE
      -> otherwise                   -> CANDIDATE
   -> authorized memory system decides persistence
```

V1 deliberately does not implement a durable memory database.

### Memory categories for future use

When the actual assistant runtime needs durable memory, prefer a small useful taxonomy:

- stable owner preferences;
- confirmed facts;
- project/workflow decisions;
- episodic events;
- open loops/commitments;
- uncertain inferences.

`uncertain` must remain distinguishable from confirmed fact.

Do not create a parallel P2P memory framework if Hermes/platform memory already provides the required persistence and retrieval behavior.

## 8. Reflection promotion policy

Promotion rules should favor explicit user authority and evidence over model confidence theater.

Minimum policy:

```text
EXPLICIT_OWNER_MEMORY_INSTRUCTION -> eligible for immediate authorized persistence
UNCERTAIN_MODEL_INFERENCE         -> separate uncertain state, never fact
REPEATED_CONFIRMED_OBSERVATION    -> review eligible, not auto-fact
ONE_OFF_IMPRESSION                -> candidate only
```

Avoid pseudo-precision such as `confidence >= 0.873 means truth` unless an evidence-backed evaluator later demonstrates value.

## 9. Agenda/open-loop policy

Open loops are useful for a personal assistant, but V1 does not create a new scheduler.

When a concrete workflow needs follow-up, reuse existing durable mechanisms such as Hermes cron/task storage or another already-selected scheduler.

Representative open-loop types:

- pending PR review;
- customer quote deadline;
- shipment missing vehicle information;
- promised follow-up;
- watch condition.

Canonical principle:

```text
AGENDA_STATE != CHAT_HISTORY
BUT
NO_NEW_AGENDA_INFRASTRUCTURE_WITHOUT_A_REAL_WORKFLOW_TRIGGER
```

## 10. Human-likeness boundary

Natural communication is allowed; deceptive identity claims are not part of this harness.

The assistant may be conversational, playful, emotionally expressive, terse, sarcastic, or stylistically consistent. It must not require pretending to be a human or denying that it is an AI when directly relevant.

## 11. Runtime slice implemented now

Implementation:

`.p2p/system/p2p_capabilities/personal_ai_behavior.py`

It currently provides:

- `VoiceProfile`;
- `ResponseSignals`;
- `ResponsePolicy`;
- `select_response_policy()`;
- `lint_response()`;
- `MemoryCandidate` + `classify_memory_candidate()`;
- `build_render_packet()`;
- `locked_facts_unchanged()`.

No external dependency, model call, storage service, database, scheduler, or background process is introduced.

## 12. Acceptance

The slice is useful when all are true:

1. explicit serious mode disables humor;
2. fresh-information/tool needs are selected before normal answer generation;
3. non-blocking tasks do not trigger clarification ceremony;
4. strong generic chatbot filler is detected deterministically;
5. anti-slop checking does not rewrite facts;
6. uncertain memory remains separate from confirmed memory;
7. explicit owner memory instructions are distinguishable from model inference;
8. locked factual values remain byte/value-equivalent across the render packet boundary;
9. no upstream `girl-agent` code/prompts are vendored or required.

Focused tests:

`tests/test_p2p_personal_ai_behavior.py`

## 13. Deferred, not required for V1

`DEFERRED_NOT_REQUIRED`:

- automatic LLM style-repair pass;
- embedding/vector memory store;
- relationship scores;
- simulated sleep/presence/hormone state;
- romantic/conflict mechanics;
- autonomous proactive messaging;
- new scheduler/daemon;
- cross-provider benchmark suite;
- TTS persona switching implementation;
- automatic durable memory mutation.

These may be reconsidered only when a concrete assistant workflow or repeated failure demonstrates need.

## 14. Stop condition

Stop this slice after code + focused tests + vision integration are reviewable and required validation is sufficient.

Do not broaden this task into full Hermes integration or production deployment.
