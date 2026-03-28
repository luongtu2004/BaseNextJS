# Tài liệu tóm tắt dự án Sàn Dịch Vụ

## 1) Mục tiêu hệ thống

Đây là ứng dụng web Next.js (App Router) dùng để:
- Giới thiệu hệ sinh thái dịch vụ `Sàn Dịch Vụ 24/7`.
- Tổ chức danh mục theo **5 trụ cột dịch vụ** và các **ngành con** bên trong.
- Cung cấp chatbot tư vấn tiếng Việt có ngữ cảnh nghiệp vụ và bộ nhớ hội thoại ngắn hạn.

Hệ thống tập trung vào 2 giá trị chính:
- **Trải nghiệm người dùng/marketing**: trang chủ, danh mục, bài viết, hiệu ứng tương tác.
- **Tư vấn tự động bằng AI**: tiếp nhận nhu cầu, phản hồi theo kiến thức nghiệp vụ đã cấu hình.

---

## 2) Kiến trúc tổng thể (theo lớp)

### Lớp giao diện (Presentation Layer)
- `app/page.tsx`: trang chủ, ghép các section chính (`Hero`, `CoreServices`, `Impact`, `News`, ...).
- `components/*`: các khối UI tái sử dụng, animation và tương tác (navbar mega-menu, chatbot modal, particle background, typing effect).
- `app/danh-muc/[slug]/page.tsx`: trang danh mục động theo slug (trụ cột hoặc ngành con).
- `app/bai-viet/[slug]/page.tsx`: trang bài viết chi tiết động theo slug.

### Lớp ứng dụng/API (Application Layer)
- `app/api/chat/route.ts`: route chính gọi AI server, bơm system prompt + knowledge base, làm sạch nội dung "thinking".
- `app/api/memory/route.ts`: route trích xuất hồ sơ ngắn của người dùng từ hội thoại.
- `app/api/chat/health/route.ts`: route kiểm tra sức khỏe kết nối tới AI backend.

### Lớp dữ liệu nghiệp vụ (Domain/Data Layer)
- `lib/constants.ts`: nguồn dữ liệu trụ cột và ngành con (dataset lõi của hệ thống dịch vụ).
- `setup/KNOWLEDGE.md`: knowledge base dùng để định hướng trả lời chatbot.
- `lib/utils.ts`: tiện ích chuẩn hóa slug, ghép class.

### Lớp cấu hình hạ tầng (Infrastructure/Config Layer)
- `next.config.ts`: cấu hình build/runtime, remote image hosts, timeout và behavior dev.
- `.env`/biến môi trường: `AI_BASE_URL`, `AI_API_KEY`, `AI_MODEL` phục vụ kết nối AI backend.

---

## 3) Trụ cột nghiệp vụ và các ngành bên trong

Hệ thống mô hình hóa dịch vụ theo cấu trúc:
**Trụ cột (pillar) -> Danh sách ngành (industries)**.

### Trụ cột 1: Vận tải & Di chuyển
- Taxi (4,7 chỗ)/ Xe hợp đồng / Xe du lịch (4-7-16-29-45 chỗ)
- Xe tiện chuyến / Xe ghép / Xe Limousine (4-7-12 chỗ)
- Xe khách chạy tuyến cố định (Liên tỉnh)
- Xe tải vận chuyển hàng hóa, xe công (từ 0,5 tấn đến 20 tấn)
- Xe cẩu, xe nâng, máy xúc
- Cứu hộ giao thông (Cẩu kéo ô tô)
- Sửa xe ô tô lưu động (Vá lốp, sửa nhanh)
- Lái xe ô tô hộ (Bạn uống say - Tôi lái)
- Lái xe máy hộ
- Lái xe theo ngày, lái xe theo chuyến
- Xe ôm công nghệ (Xe máy cá nhân)

### Trụ cột 2: Xây dựng, Nội thất và Kỹ thuật
- Sửa chữa Điện nước (Xử lý sự cố 24/7)
- Thợ Nề / Xây dựng (Xây mới, sửa chữa, phá dỡ)
- Sơn bả / Chống thấm
- Trần thạch cao (Thi công vách, trần)
- Nhôm kính / Cửa cuốn (Lắp đặt, sửa chữa)
- Cơ khí / Hàn xì (Hàng rào, cổng sắt)
- Thợ Mộc (Sửa chữa lắp đặt đồ gỗ)
- Thông tắc cống / Hút bể phốt
- Sửa chữa, bảo dưỡng Điều hòa
- Sửa chữa, lắp đặt Máy giặt / Máy sấy
- Sửa chữa, lắp đặt Tủ lạnh / Tủ đông
- Thay lõi Máy lọc nước
- Sửa chữa Bếp từ / Bếp ga / Đồ gia dụng
- Thợ Khóa (Mở khóa, đánh chìa, khóa thông minh)
- Lắp đặt & Sửa chữa Camera / An ninh
- Sửa chữa thiết bị văn phòng (Máy tính, máy in)

### Trụ cột 3: Giúp việc, Chăm sóc & Làm đẹp
- Giúp việc theo giờ / ngày / tháng
- Trông giữ trẻ em tại nhà
- Chăm sóc người thân tại nhà
- Nuôi bệnh tại bệnh viện
- Dịch vụ Nấu cỗ tại nhà
- Vệ sinh công nghiệp, vệ sinh trọn gói
- Vệ sinh theo ngày, theo giờ
- Cắt tóc / Làm tóc tại nhà
- Làm móng (Nails) tại nhà
- Trang điểm (Makeup) tại nhà
- Massage trị liệu tại nhà
- Chăm sóc da mặt tại nhà

### Trụ cột 4: Y tế & Giáo dục
- Điều dưỡng tại nhà (Tiêm, truyền, vật lý trị liệu)
- Lấy mẫu máu xét nghiệm tại nhà
- Gia sư văn hóa (Toán, Văn, Anh...)
- Gia sư năng khiếu (Đàn, họa, võ, bơi)

### Trụ cột 5: Du lịch, Khách sạn và Bảo hiểm
- Đặt vé máy bay nội địa / quốc tế
- Đặt phòng khách sạn, homestay, resort
- Đặt tour ghép / tour riêng theo nhu cầu
- Thuê xe tự lái / xe du lịch có tài xế
- Đưa đón sân bay 2 chiều
- Hỗ trợ visa, hộ chiếu và lịch trình
- Hướng dẫn viên du lịch theo điểm đến
- Combo du lịch trọn gói (vé + phòng + xe)
- Bảo hiểm du lịch
- Dịch vụ SIM / eSIM du lịch

---

## 4) Luồng vận hành chatbot (điểm kỹ thuật chính)

1. Người dùng mở `Chatbot` trong giao diện.
2. Client gửi hội thoại tới `POST /api/chat`.
3. Server nạp `setup/KNOWLEDGE.md`, ghép vào system prompt và gửi sang AI backend.
4. Server nhận stream đầu ra, gom toàn bộ nội dung, lọc bỏ "reasoning/thinking", trả về câu trả lời sạch.
5. Sau phản hồi, client gọi `POST /api/memory` để rút trích hồ sơ người dùng và lưu `localStorage`.

Kết quả: chatbot vừa trả lời theo tri thức nghiệp vụ, vừa ghi nhớ ngữ cảnh ngắn để tư vấn nhất quán hơn.

---

## 5) Đặc điểm kỹ thuật nổi bật

- Stack: `Next.js 15`, `React 19`, `TypeScript`, `Tailwind CSS`.
- Kiến trúc App Router rõ ràng: page động theo slug + API routes.
- Tối ưu trải nghiệm cảm giác "premium": motion animation, smooth scroll, hero effects.
- Dữ liệu trụ cột tập trung tại `lib/constants.ts`, dễ mở rộng theo ngành mới.
- Có cơ chế health-check AI backend và timeout/abort cho các request dài.

---

## 6) Kết luận ngắn

Dự án được tổ chức tốt theo hướng **website giới thiệu + hệ tư vấn AI theo tri thức ngành**.  
Phần cốt lõi nghiệp vụ nằm ở mô hình **5 trụ cột dịch vụ** và danh sách ngành con, còn phần giá trị kỹ thuật nằm ở luồng chatbot có kiểm soát prompt, lọc reasoning và ghi nhớ hồ sơ khách hàng.
