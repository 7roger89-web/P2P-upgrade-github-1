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

Tài liệu chính thức được kiểm tra ngày 2026-09-20 cho thấy:

- **Web Apps**: frontend React đa tệp, có file tools, shell, web/media và preview/deploy.
- **Full-Stack**: Web Apps + `propose_plan` + bộ công cụ Supabase cho database/auth/storage.
- **UI Component**: bề mặt chuyên cho component.
- **Data Visualization**: bề mặt chuyên cho biểu diễn dữ liệu; agentic tool set dùng nền Web Apps.
- **Image-to-App**: dựng app từ hình; agentic tool set dùng nền Web Apps.
- **Agent Mode + GitHub**: sandbox repo, diff, checks, commit/push và theo tài liệu hiện tại là một PR cho mỗi chat.

Nguồn chính thức:
- https://www.designarena.ai/methodology/agentic-harness
- https://help.arena.ai/articles/5701270322-arena-how-to-code-arena
- https://help.arena.ai/articles/1655691990-how-to-use-coding-in-agent-mode
- https://help.arena.ai/articles/5432423882-how-to-use-agent-mode
- https://notes.designarena.ai/fullstack-arena-methodology/

Đây là snapshot có ngày tháng, không phải bảo đảm vĩnh viễn. Khả năng chính thức mới hơn luôn thắng mẹo cũ.

## 3. Bảng chọn bề mặt

| Mục tiêu | Bề mặt ưu tiên | Lý do |
|---|---|---|
| App shell, nhiều trang, workflow responsive | **Web Apps** | Làm frontend đa tệp mà không ép kiến trúc database |
| Một widget khó, có khả năng tái sử dụng | **UI Component** | Cho nhiều phương án cùng đấu một bài |
| Timeline, comparison matrix, lineage, hiển thị phân tích dày | **Data Visualization** | Tập trung information geometry và tương tác |
| Đã có screenshot tham chiếu rất mạnh | **Image-to-App** | Ép implementation bám fidelity |
| Persistence/CRUD/auth/storage là acceptance thật | **Full-Stack** | Supabase là khả năng native của bề mặt này |
| Tích hợp bền vững vào repo GitHub hiện có | **Agent Mode + GitHub** | Branch/diff/check/PR |

Quy tắc mặc định:

```text
FRONTEND_KHÔNG_CẦN_PERSISTENCE => WEB_APPS_TRƯỚC
DATABASE_OR_AUTH_LÀ_ACCEPTANCE => FULL_STACK
TÍCH_HỢP_REPO_THẬT => AGENT_MODE_GITHUB
```

Không chọn Full-Stack chỉ vì sản phẩm được gọi là “full app”. Nếu database/auth/storage chưa phải acceptance, Supabase-first thường là `DEFER_UNTIL_NEEDED`.

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

## 11. Agent Mode + GitHub

Khi đưa winner vào repo thật:
- chọn đúng repo;
- một bounded branch/PR cho mỗi session theo giới hạn hiện tại;
- yêu cầu preview nếu acceptance có visual;
- xem diff/checks;
- bảo đảm mọi file cần thiết đã push trước khi PR đóng/merge;
- GitHub là durable checkpoint.

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
2. Web Apps dựng shell hoặc vertical slice
3. UI Component/Data Visualization chỉ cho chỗ thật sự khó
4. khóa winner
5. tích hợp qua lane có GitHub
6. verify workflow thật đại diện
7. lặp theo module khi cần
8. chỉ thêm Full-Stack persistence khi acceptance yêu cầu
```

Playbook này hướng dẫn chọn công cụ. Nó không thay thế kiến trúc riêng của dự án, product truth hay Supreme Law.
