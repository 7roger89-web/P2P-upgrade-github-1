# 03 — CASEBOOK / BLIND EVALUATION TEMPLATE

CASEBOOK_VERSION: `0.1`

## A. Case header

```text
CASE_ID:
SYSTEM: MH / LY / ZW
METHOD_LANE:
CASE_TYPE: BLIND_TEST / RETROSPECTIVE_STUDY / TEACHING_ONLY
CREATED_AT:
DATA_SOURCE:
OUTCOME_VISIBILITY_AT_START: HIDDEN / KNOWN
```

`RETROSPECTIVE_STUDY` không được tính như blind predictive evidence.

## B. Input lock

```text
QUESTION_OR_TOPICS:
RAW_INPUT:
TIME_CONTEXT:
LOCATION_CONTEXT_IF_RELEVANT:
INPUT_PRECISION:
MISSING_FIELDS:
UNCERTAINTIES:
INPUT_LOCK_HASH_OR_VERSION:
```

## C. Construction freeze

```text
ENGINE:
ENGINE_VERSION_OR_PINNED_SHA:
CONVENTIONS:
CONSTRUCTION_OUTPUT:
CONSTRUCTION_VERSION:
ALTERNATIVE_BRANCHES:
```

Không sửa construction sau outcome. Nếu phát hiện bug thật, tạo `CONSTRUCTION_VERSION+1`, giữ bản cũ và lý do.

## D. Method lock

```text
METHOD_LANE:
SCHOOL_OR_AUTHOR_SCOPE:
SOURCE_LAYER_LIMIT:
ALLOWED_RULE_IDS:
EXCLUDED_RULE_IDS:
METHOD_LOCKED_AT:
```

## E. Một quẻ đa đoạn / multi-topic section

Lặp block dưới đây cho từng việc:

```text
TOPIC_ID:
QUESTION:
OBJECT_OF_INQUIRY:
USE_GOD_OR_BINDING:
PALACE_LINE_BINDING:
ACTIVE_RULE_IDS:
STRUCTURAL_OBSERVATIONS:
APPLICATION:
CLAIM_ID:
CLAIM:
TEXTUAL_CONFIDENCE:
INTERPRETIVE_CONFIDENCE:
PREDICTIVE_CONFIDENCE:
UNSUPPORTED:
```

Không cho topic sau nhìn outcome của topic trước trong blind run.

## F. Claim cards

```text
CLAIM_ID:
CLAIM:
METHOD:
RULE_ID:
SOURCE:
SOURCE_LAYER:
TEXTUAL_BASIS:
APPLICATION:
INFERENCE:
ALTERNATIVE_INTERPRETATIONS:
TEXTUAL_CONFIDENCE:
INTERPRETIVE_CONFIDENCE:
PREDICTIVE_EVIDENCE:
UNSUPPORTED:
TIME_SCOPE:
FALSIFICATION_CRITERION:
```

Nếu `UNSUPPORTED != NO`, claim không được viết lại như sự thật chắc chắn trong phần kết luận.

## G. Prediction lock

```text
PREDICTION_LOCK_ID:
LOCKED_CLAIMS:
LOCKED_AT:
OUTCOME_STILL_HIDDEN: YES/NO
```

Sau khi lock, không sửa wording để tăng độ khớp. Có thể bổ sung analysis mới nhưng phải cấp prediction version mới và ghi rằng nó được tạo sau thông tin nào.

## H. Outcome reveal

```text
OUTCOME:
OUTCOME_SOURCE:
OUTCOME_PRECISION:
REVEALED_AT:
```

## I. Scoring

Mỗi claim:

- `EXACT_HIT`
- `PARTIAL_HIT`
- `VAGUE_HIT`
- `MISS`
- `CONTRADICTION`
- `UNSCORABLE`

Không cho câu mơ hồ được cùng điểm với dự đoán cụ thể đã khóa.

## J. Failure analysis

```text
FAILURE_CLASS:
- INPUT_ERROR
- CONSTRUCTION_ERROR
- CONVENTION_MISMATCH
- WRONG_METHOD_LANE
- RULE_PROVENANCE_FAILURE
- RULE_APPLICATION_ERROR
- SCHOOL_CONFLICT
- OVERINTERPRETATION
- HINDSIGHT_BIAS
- VAGUE_OUTCOME
- UNKNOWN

ROOT_CAUSE:
RULES_AFFECTED:
PROPOSED_CHANGE:
EVIDENCE_NEEDED_BEFORE_CHANGE:
```

Một case không đủ để sửa permanent rule trừ khi nó chứng minh lỗi deterministic rõ ràng.

## K. Safety note

Các claim liên quan sức khỏe, pháp lý, tài chính, tử vong, tai nạn hoặc hành vi người thứ ba phải được trình bày như nội dung truyền thống/nghiên cứu với uncertainty phù hợp; không thay thế tư vấn chuyên môn hay bằng chứng thực tế.
