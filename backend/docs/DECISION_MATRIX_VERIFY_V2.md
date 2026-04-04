# Decision Matrix cho xác minh giấy tờ (AI Integration) - Ver 2

Tài liệu này quy định các quy tắc xử lý tự động và bán tự động trong quá trình xác minh danh tính người dùng (eKYC) có tích hợp AI.

## 1. Mục tiêu và Nhóm kiểm tra

Hệ thống AI sẽ kiểm tra 4 nhóm tiêu chí chính:
1. **Chất lượng ảnh:** Tính đúng chuẩn, rõ nét của ảnh giấy tờ.
2. **Tính hợp lệ của dữ liệu:** Kiểm tra format số giấy tờ (CCCD/CMND).
3. **Thời hạn sử dụng:** Kiểm tra ngày hết hạn của giấy tờ.
4. **Xác thực sinh trắc học:** Độ khớp giữa ảnh giấy tờ và ảnh selfie (Face Match) và tính sống của thực thể (Liveness).

## 2. Quy tắc xử lý (Operational Guidelines)

- **Chặn tại trạm (Strict Block):** Nếu lỗi thuộc nhóm chất lượng ảnh / sai loại giấy tờ / sai mặt / mờ / lóa / mất góc / OCR không đọc được => **Yêu cầu người dùng chụp lại ngay**, không cho phép gửi hồ sơ về Admin.
- **Duyệt thủ công (Admin Review):** Nếu chất lượng ảnh đạt yêu cầu nhưng các kết quả OCR, Face Match hoặc Liveness không đạt ngưỡng tin cậy tuyệt đối => Chuyển trạng thái **Processing** và gửi thông báo "Hồ sơ đang được kiểm tra thêm".
- **Duyệt tự động (Auto Approve):** Chỉ tự động duyệt khi cả 4 nhóm kiểm tra đều **Pass** và các điểm số (confidence score) đạt ngưỡng cấu hình (Threshold).

## 3. Cấu hình ngưỡng (Thresholds)

Các thông số này phải được lưu trong cấu hình hệ thống (Config/Env), không được hard-code:
- `OCR_CONFIDENCE_THRESHOLD`: >= 90%
- `FACE_MATCH_THRESHOLD`: >= 85%
- `LIVENESS_THRESHOLD`: >= 85%

*Hệ thống bắt buộc phải lưu kết quả của từng hạng mục kiểm tra vàoLog/Audit Trail để hỗ trợ quá trình hậu kiểm và Admin review.*

## 4. Decision Matrix

### 4.1. Ma trận xử lý mức cao

| Nhóm check | Điều kiện | Hành động (Action) | Trạng thái Verification | Phản hồi cho người dùng |
| :--- | :--- | :--- | :--- | :--- |
| **A. Chất lượng ảnh & Loại giấy tờ** | Thiếu file, sai loại, sai mặt, mờ, lóa, mất góc, OCR không đọc được | Chụp lại ngay | `draft` hoặc chặn submit | "Vui lòng chụp lại giấy tờ rõ hơn/đúng mặt/đủ khung." |
| **B. Số giấy tờ** | Ảnh đủ dùng nhưng số giấy tờ sai format hoặc OCR confidence thấp | Chuyển Admin review | `processing` | "Hồ sơ đang được kiểm tra thêm." |
| **C. Thời hạn giấy tờ** | Có dấu hiệu hết hạn hoặc OCR không chắc chắn | Chuyển Admin review | `processing` | "Hồ sơ đang được kiểm tra thêm." |
| **D. Face match / Liveness** | Điểm khớp thấp hoặc không chắc chắn | Chuyển Admin review | `processing` | "Hồ sơ đang được kiểm tra thêm." |
| **TẤT CẢ ĐỀU ĐẠT (A+B+C+D)** | Tất cả hợp lệ và vượt ngưỡng | Tự động duyệt (Auto Approve) | `approved` | "Xác minh thành công." |

### 4.2. Ma trận chi tiết và Mapping Database

| Check | Điều kiện cụ thể | Kết quả | Hành động Backend | Trạng thái (`status`) | DB/Log Mapping |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Missing files** | Thiếu id_front, id_back, selfie | Fail | Trả lỗi 422 | `draft` | Ghi log vào `user_identity_verification_logs` với `error_code: missing_required_files` |
| **Wrong doc type** | AI phân loại không đúng CCCD | Fail | Yêu cầu chụp lại | `draft` | Log `error_code: wrong_document_type`. Lưu kết quả phân loại vào `response_payload_json`. |
| **Wrong side** | Upload nhầm mặt trước/sau | Fail | Yêu cầu chụp lại | `draft` | Log `error_code: wrong_document_side`. |
| **Quality issue** | Ảnh mờ, lóa, mất góc | Fail | Yêu cầu chụp lại | `draft` | Log `error_code: image_quality_failed`. Chi tiết lỗi (blur/glare) lưu trong payload. |
| **OCR Unreadable** | OCR không đọc được | Fail | Yêu cầu chụp lại | `draft` | Log `error_code: ocr_unreadable`. |
| **Invalid Doc Num** | Số giấy tờ sai format | Suspicious | Chuyển Admin review | `processing` | Cập nhật `user_identity_verifications.status = processing`. Ghi log `status: failed`, `error_code: document_number_invalid`. |
| **Expiry invalid** | Hết hạn hoặc không rõ | Suspicious | Chuyển Admin review | `processing` | Cập nhật `status = processing`. Log `error_code: document_expiry_invalid`. |
| **Face match low** | Điểm khớp < Threshold | Suspicious | Chuyển Admin review | `processing` | Cập nhật `status = processing`, `face_match_score = score`. Log `status: failed`. |
| **Liveness low** | Điểm liveness < Threshold | Suspicious | Chuyển Admin review | `processing` | Cập nhật `status = processing`, `liveness_score = score`. Log `status: failed`. |
| **All Passed** | Tất cả >= Threshold | Pass | Auto approve | `approved` | Cập nhật `status = approved`, `review_mode = auto`. User status -> `verified`. |

## 5. Lưu ý triển khai (Technical implementation)

1.  **Sử dụng `user_identity_verification_logs`:** Mọi kết quả từ AI Vendor (OCR, Face Match, Liveness) phải được lưu toàn bộ vào `request_payload_json` và `response_payload_json` để phục vụ đối soát.
2.  **Thông báo cho Frontend:**
    *   Nếu hành động là **"Chụp lại ngay"**: Backend trả về mã lỗi (ví dụ: 400 hoặc 422) kèm theo `error_code` chi tiết để App hiển thị đúng thông điệp (ví dụ: "Ảnh bị mờ, vui lòng chụp lại").
    *   Nếu hành động là **"Chuyển Admin duyệt"**: Backend trả về success với trạng thái `processing`.
3.  **Hậu kiểm:** Admin khi review ở màn hình `processing` sẽ nhìn thấy các điểm số AI đã được lưu sẵn trong record `user_identity_verifications` để đưa ra quyết định nhanh hơn.
