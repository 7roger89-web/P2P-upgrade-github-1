# Cẩm nang thực thi DesignArena — P2P

Trạng thái: HƯỚNG DẪN THỰC THI CÓ THỂ TÁI SỬ DỤNG  
Áp dụng từ: 2026-09-20  
Thẩm quyền: cấp dưới của `P2P_SUPREME_OPERATING_LAW_V1`

Mục đích: dùng đúng bề mặt của DesignArena cho đúng loại việc, không biến DesignArena thành một control plane thứ hai của P2P.

## 1. Nguyên tắc cốt lõi

DesignArena là một công cụ thực thi có thể thay thế trong vòng lặp phát triển sản phẩm của P2P. Nó không phải thẩm quyền kiến trúc, thẩm quyền nghiệp vụ, thẩm quyền phát hành hay bộ điều phối mới.

```text
MỤC TIÊU OWNER
→ SỰ THẬT SẢN PHẨM TỐI THIỂU
→ CHỌN ĐÚNG BỀ MẶT DESIGNARENA
→ XÂY MỘT LÁT CẮT DỌC ĐẠI DIỆN
→ RENDER / TƯƠNG TÁC / SO SÁNH
→ KHÓA THAM CHIẾU SẢN PHẨM THẮNG
→ TÍCH HỢP VÀO DỰ ÁN BỀN VỮNG
→ XÁC MINH
→ DỪNG
```

P2P vẫn sở hữu task contract, scope, evidence, durable state, Owner Gate, routing executor và acceptance.

## 2. Ảnh chụp khả năng hiện tại của DesignArena

Tài liệu chính thức và ảnh chụp UI thực tế của Owner được kiểm tra ngày 2026-09-20 cho thấy DesignArena có **hai lớp lựa chọn khác nhau** cần phân biệt:

1. **Loại arena/bề mặt**: ví dụ Website, UI Component, Data Visualization, Mobile Apps và các arena chuyên biệt khác.
2. **Độ sâu build trong Website hiện tại**:
   - **Fast** — “One HTML file, no extras. The fastest way to see your idea.” → dùng để phác nhanh ý tưởng, không phải lựa chọn mặc định cho app nhiều module.
   - **Pro** — “Best for wireframes that you can reprompt and iterate on, built in React.” → phù hợp để xây/iterate frontend React có cấu trúc.
   - **Max** — “Fullstack with auth and a database. For sites that need to save and store.” → chỉ dùng khi persistence/auth/database là yêu cầu thật.

Ảnh chụp Owner hiện còn cho thấy **Website** là arena đang chọn. Không suy rộng rằng Fast/Pro/Max xuất hiện giống hệt ở mọi arena khác nếu chưa có bằng chứng trực tiếp.

Các arena chuyên biệt vẫn dùng khi bài toán cần chúng:
- **UI Component**: component/widget khó.
- **Data Visualization**: biểu diễn dữ liệu dày, timeline, comparison.
- **Image-to-App**: chỉ khi UI hiện tại thực sự cung cấp bề mặt này trong task cần fidelity từ ảnh.

DesignArena KHÔNG phải Arena AI Agent Mode.

- **DesignArena / designarena.ai**: tournament thiết kế nhiều model song song; mỗi model nhận cùng prompt, tạo phương án, rồi người dùng vote theo bracket.
- **Arena AI / arena.ai Agent Mode**: một sản phẩm/bề mặt khác, có workflow agentic, sandbox, GitHub và PR. Không được gọi Agent Mode là một "mode của DesignArena".

Nguồn chính thức:
- https://www.designarena.ai/about
- https://www.designarena.ai/methodology/agentic-harness
- https://help.arena.ai/articles/5432423882-how-to-use-agent-mode
- https://help.arena.ai/articles/1655691990-how-to-use-coding-in-agent-mode

Đây là snapshot có ngày tháng, không phải bảo đảm vĩnh viễn. Khả năng chính thức mới hơn luôn thắng mẹo cũ.

### 2.1. Ảnh UI thực tế của Owner — selector arena và framework

Ảnh chụp DesignArena ngày 2026-09-20 xác nhận trang tạo mới hiện có nhiều loại tác vụ/bề mặt song song, trong đó nhìn thấy trực tiếp: Website, Image, Game, 3D Asset, UI Component, Mobile App, Logo, Text-to-Speech, ASCII Art và Video. Tài liệu/leaderboard chính thức còn liệt kê Web Apps, Fullstack, Data Visualization, Android và các arena chuyên biệt khác.

Khi **Mobile App** được chọn, UI hiện có selector framework:
- **Auto** — DesignArena tự chọn framework phù hợp;
- **React Native** — cross-platform iOS + Android;
- **Android** — native Android app.

Điều này củng cố nguyên tắc hai tầng:

```text
CHỌN_LOẠI_BÀI / ARENA
→ NẾU BỀ_MẶT_CÓ_SELECTOR_THÌ_CHỌN_MODE_OR_FRAMEWORK
→ DÁN_PROMPT
```

Không giả định mọi arena có cùng selector. Chỉ hướng dẫn đúng các option đã được quan sát hoặc xác minh.

Quy tắc cho Mobile App:
- nếu Owner chỉ cần mobile app tốt nhất mà chưa khóa stack → **Auto**;
- nếu cần một codebase iOS + Android → **React Native**;
- nếu mục tiêu là Android native hoặc cần capability Android đặc thù → **Android**.

Không chọn Mobile App cho một web product chỉ vì người dùng truy cập bằng điện thoại.


Ảnh UI bổ sung của Owner cùng ngày xác nhận **Data Visualization** và **UI Component** là hai lựa chọn arena độc lập ngay trên màn hình tạo mới. Trong hai ảnh này không thấy selector phụ như Fast/Pro/Max hay Auto/React Native/Android, vì vậy hiện ghi nhận:

- `Data Visualization` → arena độc lập; chưa có bằng chứng cần chọn thêm mode/framework trước khi prompt.
- `UI Component` → arena độc lập; chưa có bằng chứng cần chọn thêm mode/framework trước khi prompt.

Không suy diễn option ẩn chưa quan sát.

## 3. Bảng chọn bề mặt

| Mục tiêu | Bề mặt ưu tiên | Lý do |
|---|---|---|
| App shell, nhiều trang, workflow responsive, cần iterate React | **Website → Pro** | React + reprompt/iterate; không kéo auth/database vào |
| Phác nhanh một ý tưởng rất nhỏ | **Website → Fast** | Một HTML file; chỉ dùng khi proof nhanh là đủ |
| Một widget khó, có khả năng tái sử dụng | **UI Component** | Cho nhiều phương án cùng đấu một bài |
| Timeline, comparison matrix, lineage, hiển thị phân tích dày | **Data Visualization** | Tập trung information geometry và tương tác |
| Đã có screenshot tham chiếu mạnh và UI có hỗ trợ | **Image-to-App** | Ép implementation bám fidelity khi thật sự cần |
| Persistence/auth/database là acceptance thật | **Website → Max** | Fullstack với auth + database; chỉ dùng khi cần lưu/giữ dữ liệu |
| Đưa winner vào repo thật | **Rời DesignArena → executor tích hợp riêng do P2P chọn** | DesignArena dùng để tạo/so sánh product reference; tích hợp GitHub là bước khác |

Quy tắc mặc định:

```text
PHÁC_NHANH_Ý_TƯỞNG_NHỎ => DESIGNARENA_WEBSITE_FAST
FRONTEND_REACT_CẦN_ITERATE_KHÔNG_PERSISTENCE => DESIGNARENA_WEBSITE_PRO
AUTH_OR_DATABASE_LÀ_ACCEPTANCE => DESIGNARENA_WEBSITE_MAX
WINNER_ĐÃ_CHỐT => THOÁT_DESIGNARENA_VÀ_CHỌN_EXECUTOR_TÍCH_HỢP_RIÊNG
```

Không chọn **Max** chỉ vì sản phẩm được gọi là “full app”. Nếu auth/database chưa phải acceptance, Max là `DEFER_UNTIL_NEEDED`.

**Default mới cho frontend app nhiều module nhưng chưa cần lưu dữ liệu: Website → Pro.**

## 4. Cách dùng tournament

Dùng DesignArena như đấu trường tuyển phương án, không coi một model là oracle.

1. Cho các model cùng một bounded product contract.
2. Giữ nguyên target user, dữ liệu thật, ngôn ngữ, responsive, interaction và acceptance.
3. Xem preview của cả hai bên trước khi vote.
4. Bấm thử workflow thật, không vote bằng ảnh.
5. Chọn winner theo:
   - đúng nghiệp vụ;
   - dễ dùng và hierarchy tốt;
   - responsive tốt;
   - đủ state;
   - khớp schema/dữ liệu thật;
   - không bịa chức năng.
6. Khóa product reference thắng trước khi mở rộng scope.

Preview đẹp nhưng interaction hỏng hoặc đòi dữ liệu engine không có thì không thắng.

## 5. Xây theo lát cắt dọc

Ưu tiên:

```text
MỘT MODULE
→ input thật
→ biểu diễn đúng domain
→ tương tác
→ loading/error/empty
→ mobile
→ dữ liệu đại diện
→ render verification
→ tích hợp bền vững
```

Tránh:

```text
làm toàn bộ UI
→ làm toàn bộ API
→ nối toàn bộ engine
→ cuối cùng mới sửa responsive
```

## 6. Reuse-first

Trước khi thiết kế module từ đầu:

1. đọc engine authority;
2. đọc schema output thật;
3. xem component/frontend đã ghép với engine đó;
4. reuse/wrap phần dùng được;
5. chỉ xây phần còn thiếu hoặc đã chứng minh không dùng được.

```text
AUTHORITATIVE_COMPONENT_CÓ_SẴN
→ CHỨNG MINH REUSE HOẶC UNUSABLE
→ SAU ĐÓ MỚI XÉT REBUILD
```

Frontend không tự tính lại fact đã thuộc engine trừ khi task contract nói rõ frontend là authority của phép tính đó.

## 7. Hợp đồng prompt cho DesignArena

Prompt đầu của mỗi lát cắt chỉ nên chứa phần delta cần thiết:

- người dùng mục tiêu và workflow chính;
- một câu visual thesis;
- ngôn ngữ người dùng nhìn thấy;
- data/schema thật;
- geometry/hierarchy bắt buộc;
- desktop + mobile;
- state tương tác;
- anti-pattern;
- acceptance + rendered proof;
- stop condition.

Không nhồi toàn bộ lịch sử dự án nếu durable docs đã giữ authority.

Dự án dài nên có một product/design/module contract nhỏ trong repo để các lượt sau đọc lại.

## 8. Hợp đồng ngôn ngữ

Mỗi task sản phẩm phải nói rõ ngôn ngữ người dùng nhìn thấy.

Với dự án chỉ dùng một ngôn ngữ, áp dụng cho:
- navigation;
- label/form/button;
- chart;
- luận giải/giải thích;
- lỗi/cảnh báo;
- empty/loading;
- tooltip/help;
- export/report;
- mọi text sinh ra cho người dùng.

Định danh máy không thể dịch mà không mất identity (repo, SHA, URL, filename, protocol key) chỉ được giữ nguyên trong vùng kỹ thuật khi contract dự án cho phép.

Không được coi “đã dịch UI” là đủ nếu phần luận giải vẫn ra ngôn ngữ khác.

## 9. Review kế hoạch Full-Stack

Chỉ dùng Full-Stack khi persistence/auth/storage thực sự nằm trong acceptance.

Khi Full-Stack trả `propose_plan`, kiểm tra trước khi cho chạy. Loại bỏ:
- persistence không cần;
- auth không cần;
- CRUD chung chung;
- deploy trước khi proof workflow đại diện;
- schema tự nhiên trở thành product architecture authority.

Ô thêm bước trong plan dùng để kéo executor trở về task contract thật.

## 10. Image-to-App

Chỉ dùng khi đã có visual winner và fidelity thực sự quan trọng:

```text
WINNING_RENDER
→ CHỤP MÀN HÌNH ĐẠI DIỆN
→ IMAGE-TO-APP
→ SO FIDELITY + INTERACTION
→ GIỮ NẾU TỐT HƠN VẬT CHẤT
```

Không biến thành nghi lễ bắt buộc.

## 11. Ranh giới sau DesignArena

DesignArena kết thúc vai trò khi đã có winner/product reference đủ tốt cho lát cắt hiện tại.

Sau đó Control Tower chọn executor tích hợp riêng theo capability thật của dự án. Ví dụ, Arena AI Agent Mode có thể là một executor GitHub phù hợp trong một số task, nhưng đó là **Arena AI**, không phải DesignArena.

Luồng đúng:

```text
DESIGNARENA_TOURNAMENT
→ WINNER / PRODUCT REFERENCE
→ CONTROL TOWER CHỌN EXECUTOR TÍCH HỢP
→ GITHUB / IMPLEMENTATION / VERIFY
```

Nếu artifact chỉ tồn tại ở preview, transport theo đường lossless được executor hỗ trợ và tuân Supreme Law #9.

## 12. Evidence

Self-report của DesignArena không phải acceptance evidence.

- visual claim → render thật;
- responsive claim → desktop + mobile thật;
- interaction claim → thao tác thật;
- repo claim → branch/PR/head thật;
- persistence claim → write/read thật;
- schema/engine compatibility → payload đại diện thật.

Không nâng mock/preview thành runtime/production PASS.

## 13. Cách tiếp nhận trick

Khi phát hiện mẹo mới, trước hết thảo luận và phân loại:

```text
QUIRK_MỘT_LẦN
TRICK_LẶP_LẠI_ĐƯỢC
THAY_ĐỔI_CAPABILITY_CỦA_PRODUCT
FAILURE_MODE_VẬT_CHẤT
```

Chỉ cập nhật playbook khi mẹo đó cải thiện outcome, recovery, fidelity hoặc effort một cách vật chất.

Không dựng framework/registry/benchmark chỉ để chứa mẹo.

## 14. OE Gate

Trước khi thêm một vòng DesignArena, hỏi đúng câu:

`Không bị over engineering chứ?`

Đánh giá:
- SIMPLER_PATH
- MATERIAL_PROGRESS
- NECESSITY
- CORE_BEFORE_SUPPORT
- SMALLER_VERIFIABLE_SLICE

Nếu UI Component battle, Image-to-App, Full-Stack backend, redesign lần hai hay reviewer thêm không cải thiện acceptance vật chất → `SKIP_IT` hoặc `DEFER_UNTIL_NEEDED`.

## 15. Mẫu áp dụng cho dự án P2P mới

```text
1. khóa product/language/visual contract
2. Website → Pro dựng shell hoặc vertical slice React
3. Website → Fast chỉ cho proof cực nhỏ; không dùng làm app nền
4. UI Component/Data Visualization chỉ cho chỗ thật sự khó
5. khóa winner
6. tích hợp qua executor riêng phù hợp
7. verify workflow thật đại diện
8. lặp theo module khi cần
9. chỉ chuyển Website → Max khi auth/database/persistence là acceptance thật
```

Playbook này hướng dẫn chọn công cụ. Nó không thay thế kiến trúc riêng của dự án, product truth hay Supreme Law.


## 16. Bài học khóa mục tiêu prompt từ các vòng DesignArena thực tế

Nguồn kinh nghiệm: các vòng DesignArena thực tế ngày 2026-09-20 trên Huyền Học Lab, gồm plan drift và Foundation candidate drift. Đây là kinh nghiệm thao tác, không phải authority cao hơn task contract hay Supreme Law.

Các failure pattern đã quan sát:

- **Visual drift dù đã có mood direction**: model vẫn tự kéo sản phẩm sang cosmic/dark/gold/gradient/glassmorphism nếu prompt chỉ nói “tránh” mà không khóa cả replacement target lẫn forbidden substitutions.
- **Typical-app scope creep**: model tự thêm sessions, localStorage, notification, progress, roadmap, persistence hoặc generic app semantics dù task chỉ yêu cầu Foundation.
- **Exact interaction drift**: mobile navigation hoặc nút “Thêm” bị đổi nghĩa khi prompt nói mục tiêu chung nhưng không khóa exact labels + exact behavior.
- **Truthfulness drift**: KPI, phần trăm tiến độ, “đã sẵn sàng”, notification và capability chưa tồn tại dễ được bịa để làm màn hình trông hoàn chỉnh.
- **Architecture invention**: model có xu hướng tạo universal/shared chart hoặc dependency order giữa module nếu prompt chỉ mô tả tương lai mà không cấm việc biến giả định thành architecture.
- **Required-item omission**: một module bắt buộc có thể bị bỏ sót nếu acceptance không kiểm lại exact inventory.

### Prompt-lock pattern

Với DesignArena prompt có rủi ro drift, ưu tiên cấu trúc khóa sau:

1. **PRIORITY_ORDER** — ghi rõ hard invariants outrank aesthetics và implementation freedom.
2. **EXACT_REQUIRED** — liệt kê chính xác route, label, interaction, state hoặc module bắt buộc.
3. **MUST_NOT_CREATE** — cấm các capability model hay tự thêm: auth, database, localStorage, sessions, fake KPI, notifications, roadmap, universal component, backend giả.
4. **REPLACEMENT_TARGET** — mỗi anti-pattern quan trọng phải có hướng thay thế cụ thể; “không cosmic” đi cùng palette/layout/mood phải dùng.
5. **TRUTHFUL_STATE_ONLY** — cấm progress/KPI/readiness/capability không có authority.
6. **CREATIVE_FREEDOM_ZONE** — chỉ cho model tự do ở spacing, typography, composition, microinteraction trong phạm vi contract; không tự do đổi information architecture hay product semantics.
7. **EXACT_ACCEPTANCE_REPLAY** — trước khi kết thúc, đối chiếu lại toàn bộ inventory bắt buộc và forbidden list.
8. **REVISE_IN_PLACE** — khi candidate có bộ xương dùng được, sửa candidate hiện tại thay vì restart để giữ phần đã đúng và giảm drift mới.

Mẫu ưu tiên:

```text
PRIORITY_ORDER:
1. HARD PRODUCT INVARIANTS
2. EXACT REQUIRED BEHAVIOR
3. TRUTHFUL STATE
4. VISUAL DIRECTION
5. CREATIVE FREEDOM

IF ANY DESIGN IDEA CONFLICTS WITH 1–3:
DO NOT IMPLEMENT THAT IDEA.
```

### Anti-pattern: chỉ dùng câu “không được”

Một danh sách cấm dài nhưng không đưa replacement target vẫn để model tự chọn một phong cách khác có thể lệch không kém.

Ưu tiên:

```text
FORBIDDEN: cosmic / neon / glass / gold fantasy
REQUIRED REPLACEMENT: warm ivory + warm white + ink black + stone gray + restrained cinnabar
```

### Anti-pattern: acceptance chung chung

“Responsive, đẹp, đúng tiếng Việt” là chưa đủ khi interaction quan trọng.

Khóa bằng exact behavior, ví dụ:

```text
MOBILE_BOTTOM_NAV_EXACT =
Tổng quan | Bát Tự | Tử Vi | Lục Hào | Thêm

THÊM_ACTION_EXACT =
mở sheet danh sách module; không tạo session; không có nút cộng trung tâm
```

### Kết nối Evidence-Grounded Evolution

Các bài học DesignArena chỉ nên trở thành kinh nghiệm P2P tự động tái sử dụng khi đi qua lifecycle hiện có:

```text
CANDIDATE → VERIFIED → ACTIVE → SUPERSEDED | QUARANTINED
```

Không tạo “DesignArena memory” riêng. Khi có helper/runtime phù hợp và evidence đủ, ghi bài học dạng `PROCEDURAL` qua `experience_evolution.py`; project playbook này vẫn là contract thao tác trực tiếp và source evidence cho candidate.

## 17. FOUNDATION_REPAIR_EVIDENCE_2026_09_21

Huyền Học Lab provided the first concrete evidence that the prompt-lock pattern reduces DesignArena drift.

Observed sequence:
- initial candidate drifted into cosmic/gold visual, fake KPI, session/localStorage semantics, wrong mobile navigation, and invented universal chart architecture;
- a locked replacement prompt produced a materially closer winner;
- two targeted SAME_CANDIDATE repairs corrected exact mobile navigation, truthful state, Vietnamese wording, decorative imagery, and product subtitle without restarting the React structure.

Reusable lesson:
- when the candidate skeleton is good, prefer REVISE_IN_PLACE + exact repair list over restart;
- exact literal interaction contracts outperform broad intent language for navigation;
- anti-patterns should pair with a required replacement target;
- platform-injected analytics/storage instrumentation must be distinguished from app-authored persistence before declaring scope drift.

This is evidence for the existing prompt-lock procedural candidate, not automatic ACTIVE experience by itself.


## 18. UI_COMPONENT_ONE_SHOT_OBSERVED

Owner UI evidence on 2026-09-21 shows the current DesignArena UI Component arena behaves as a one-shot tournament surface: generate/compare once, with no same-candidate reprompt loop like Website → Pro.

Operational consequence:
- use UI Component to discover/select a visual and interaction reference for one bounded component;
- do not plan a multi-turn repair loop inside UI Component;
- if the winner needs repair or product integration, move the selected reference/code into an iterative surface such as Website → Pro or into the chosen external integration executor;
- if the first tournament misses hard invariants badly, either rerun a new UI Component tournament with a stronger prompt or skip another tournament and continue from the best donor in Website → Pro.

Preferred flow:
```text
UI COMPONENT TOURNAMENT (ONE SHOT)
→ SELECT BEST DONOR
→ WEBSITE PRO / INTEGRATION EXECUTOR
→ ITERATE + VERIFY
```

Do not treat UI Component as the durable app workspace.

## 19. FOUR_MODELS_FIVE_VOTES_WINNER_EXPORT

Owner-observed DesignArena tournament behavior on 2026-09-21 matches the official tournament description:
- four distinct models are sampled for one prompt;
- the user makes five pairwise votes across initial, winner/loser and tie-breaker battles;
- the session yields a complete ranking;
- in the observed UI, only the selected/final winner was available for download/export; losing candidates were not exportable.

Operational rules:
- treat the tournament as a selection surface, not a persistent multi-candidate workspace;
- preserve the winning export immediately when it matters;
- never infer that a model is globally best from one prompt win; the result proves only that this model/design won this prompt/session under these votes;
- if only the winner is exportable, review hard invariants before voting whenever possible because losing implementation artifacts may be unrecoverable;
- for component tournaments, the exported winner is a donor/reference unless it also preserves the target app shell and contract.

Observed roster for one Huyền Học Lab Bát Tự tournament: GPT-6 Astra (xhigh/Max label in UI), Muse Spark 1.1, GPT-5.5, Nemotron 3 Ultra. Roster is stochastic and must not be hard-coded into prompts.


## 20. Quota-scarce tournament strategy

Owner-observed product behavior on 2026-09-21: a DesignArena account may only allow a small number of generation sessions per day, and many ordinary sessions present only a two-model head-to-head rather than the four-model/five-vote tournament documented for some categories/sessions.

Treat DesignArena generation quota as scarce design-search budget.

Default routing:
- DesignArena = high-uncertainty visual/product forks where parallel model comparison creates material value.
- iterative Website → Pro candidate = exploit the already-created winner for as much repair/polish as the current product UI permits before spending another new tournament.
- Arena AI Agent Mode or another GitHub-capable executor = long-context integration, repo surgery, engine wiring, tests, and repetitive correction.
- do not spend a new DesignArena tournament on routine forms, copy fixes, route wiring, dependency changes, build errors, or minor polish.

Two-model battles are valid evidence for a local preference decision but are weaker search coverage than a four-model tournament. Do not wait for four models as a prerequisite. If four models appear, reserve that richer search opportunity for the hardest visual/interaction decision.

Because losing DesignArena candidates may not be exportable, inspect critical constraints before voting and save the winning artifact immediately.

Arena AI note: no visible prompt-character cap should be interpreted as "literally unlimited context." Agent Mode still has session/context limits; its documented compaction reduces pressure but does not abolish finite context. Use long prompts when valuable, but keep task scope bounded.


## 21. Arena AI vs DesignArena — artifact-first routing

Fresh official evidence checked on 2026-09-21:

### DesignArena
- Blind design/product comparison surface.
- Model identity is hidden during evaluation to reduce brand bias.
- Exact number of models can differ by arena/category; the four-model/five-vote bracket is an example, not a universal guarantee.
- Use for search over competing visual/information-architecture options when comparison itself has material value.
- Treat the exported winner as an artifact/donor. Do not infer global model superiority from one win.
- If model identity is not shown, do not spend effort guessing it. Evaluate the artifact against the task contract.

### Arena AI Agent Mode
- Multi-step agentic execution surface with sandbox, web/file tools, uploads, coding, and optional GitHub integration.
- A new Agent Mode chat is routed to a dedicated orchestrator model; current official docs state the orchestrator is not revealed after feedback.
- The session may switch models automatically when a response is likely to fail and strand the session.
- Official Agent Arena currently includes recent orchestrators such as Claude Fable 5.1 (Max), GPT 6 Astra (Max), Claude Opus 5 and others. Therefore "model not visible" must not be interpreted as "only old models are available."
- Agent Mode has finite context/session limits; compaction lowers pressure but does not create infinite context.
- Use for long-context execution, file integration, repo surgery, tests, GitHub branch/PR work, and bounded multi-step completion.

### P2P routing rule

```text
NEED_PARALLEL_DESIGN_SEARCH
→ DESIGNARENA

HAVE_A_WINNER_OR_CLEAR_REFERENCE
+ NEED_LONG_ITERATIVE_IMPLEMENTATION
→ ARENA_AI_AGENT_MODE_OR_OTHER_GITHUB_EXECUTOR

MODEL_IDENTITY_UNKNOWN
→ DO_NOT_GUESS
→ JUDGE_ARTIFACT / EVIDENCE / TASK FIT
```

Do not route by model brand when the surface intentionally anonymizes or randomizes models. Route by task capability and artifact quality.
