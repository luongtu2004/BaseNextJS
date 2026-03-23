# Tài liệu tóm tắt dự án Sàn Dịch Vụ

## 1) Mục tiêu hệ thống

Đây là ứng dụng web Next.js (App Router) dùng để:
- Giới thiệu hệ sinh thái dịch vụ `Sàn Dịch Vụ 24/7`.
- Tổ chức danh mục theo **6 trụ cột dịch vụ** và các **ngành con** bên trong.
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
- Taxi/xe hợp đồng/xe du lịch (4-45 chỗ)
- Xe tiện chuyến, xe ghép, limousine
- Xe khách tuyến cố định liên tỉnh
- Xe tải vận chuyển hàng hóa, xe công
- Xe cẩu, xe nâng, máy xúc
- Cứu hộ giao thông (cẩu kéo ô tô)
- Sửa xe ô tô lưu động
- Lái xe ô tô hộ
- Lái xe máy hộ
- Lái xe theo ngày/chuyến
- Xe ôm công nghệ

### Trụ cột 2: Xây dựng & Nội thất
- Sửa chữa điện nước
- Thợ nề/xây dựng
- Sơn bả/chống thấm
- Trần thạch cao
- Nhôm kính/cửa cuốn
- Cơ khí/hàn xì
- Thợ mộc
- Thông tắc cống/hút bể phốt

### Trụ cột 3: Điện máy & Gia dụng
- Sửa, bảo dưỡng điều hòa
- Sửa, lắp đặt máy giặt/máy sấy
- Sửa, lắp đặt tủ lạnh/tủ đông
- Thay lõi máy lọc nước
- Sửa bếp từ/bếp ga/đồ gia dụng
- Thợ khóa
- Lắp đặt/sửa camera an ninh
- Sửa thiết bị văn phòng (máy tính, máy in)

### Trụ cột 4: Giúp việc & Chăm sóc
- Giúp việc theo giờ/ngày/tháng
- Trông giữ trẻ em tại nhà
- Chăm sóc người thân tại nhà
- Nuôi bệnh tại bệnh viện
- Nấu cỗ tại nhà
- Vệ sinh công nghiệp/trọn gói
- Vệ sinh theo ngày/giờ

### Trụ cột 5: Y tế & Giáo dục
- Điều dưỡng tại nhà
- Lấy mẫu máu xét nghiệm tại nhà
- Gia sư văn hóa
- Gia sư năng khiếu

### Trụ cột 6: Làm đẹp & Spa
- Cắt tóc/làm tóc tại nhà
- Làm móng tại nhà
- Trang điểm tại nhà
- Massage trị liệu tại nhà
- Chăm sóc da mặt tại nhà

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
Phần cốt lõi nghiệp vụ nằm ở mô hình **6 trụ cột dịch vụ** và danh sách ngành con, còn phần giá trị kỹ thuật nằm ở luồng chatbot có kiểm soát prompt, lọc reasoning và ghi nhớ hồ sơ khách hàng.
