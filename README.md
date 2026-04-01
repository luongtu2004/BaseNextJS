# Sàn Dịch Vụ 24/7 (Service Marketplace)

## Khái Quát (Overview)
Dự án nền tảng kết nối dịch vụ giữa Khách Hàng (Customer) đang có nhu cầu tìm kiếm thợ và các nhà cung cấp/thợ chuyên nghiệp (Provider). Dự án hỗ trợ cả giao diện người dùng tiêu chuẩn và bảng điều khiển quản trị tập trung.

## Công Nghệ Sử Dụng
- **Giao diện & Hệ Khách (Frontend)**: Nền tảng Next.js (App Router), React, TailwindCSS, TypeScript.
- **Hệ Thống API (Backend)**: Nền tảng tốc độ cao FastAPI, Python 3.10+, PostgreSQL, SQLAlchemy ORM.
- **Bảo Mật (Security)**: JWT Access/Refresh tokens đa tầng, mã hóa BCrypt.

---

## Hướng Dẫn Thiết Lập & Chạy Dự Án (Setup & Run)

Môi trường phát triển cục bộ (Local Development) cần yêu cầu máy tính của bạn đã cái đặt sẵn: **Node.js 18+**, **Python 3.10+**, và hệ quản trị cơ sở dữ liệu **PostgreSQL**.

### 1. Khởi chạy Hệ Thống Backend (FastAPI)

1. Mở phần mềm quản trị Database (VD: pgAdmin, DBeaver) và tạo một database PostgreSQL có tên là `sandichvu`.
2. Mở trình dòng lệnh (Terminal/Command Prompt) và đi vào thư mục `backend`:
   ```bash
   cd backend
   ```
3. Tạo và kích hoạt môi trường ảo (Virtual Environment) nhằm phân tách thư viện:
   ```bash
   # Tạo môi trường ảo (Chỉ chạy lần đầu)
   python -m venv venv

   # Kích hoạt trên Windows
   .\venv\Scripts\activate
   # Kích hoạt trên macOS/Linux
   source venv/bin/activate
   ```
4. Cài đặt các thư viện gói bổ trợ gốc được định nghĩa:
   ```bash
   pip install -r requirements.txt
   ```
5. Cấu hình biến môi trường bằng cách tạo một file tên là `.env` nằm trong thư mục `backend` chứa sơ đồ nguyên lí như sau:
   ```env
   # Nhớ thay đổi mat_khau với mật khẩu thật trên PostgreSQL của máy bạn
   DATABASE_URL=postgresql://postgres:mat_khau@localhost:5432/sandichvu
   JWT_ACCESS_SECRET=chuoi_ki_tu_ngau_nhien_bao_mat_cua_ban_1
   JWT_REFRESH_SECRET=chuoi_ki_tu_ngau_nhien_bao_mat_cua_ban_2
   OTP_LENGTH=6
   OTP_TTL_SECONDS=300
   OTP_MAX_ATTEMPTS=5
   CORS_ORIGINS=http://localhost:3000
   ```
6. Chạy máy chủ môi trường Dev liên tục để phản hồi API:
   ```bash
   uvicorn app.main:app --reload
   ```
   > **Lưu ý**: Endpoint cốt lõi của API tự hào sẽ được khởi chạy ở `http://localhost:8000`. Cấu trúc tài liệu Swagger API theo dõi trọn trạng thái ở link `http://localhost:8000/docs`. Bất kì mã OTP tĩnh ở môi trường Dev này sẽ được phóng in ra thẳng màn hình log terminal này.

### 2. Khởi chạy Hệ Thống Giao Diện (Next.js Frontend)

1. Mở một trình dòng lệnh (Terminal) mới và đứng nguyên ngay tại thư mục dự án gốc (Có chứa package.json).
2. Tải và cài đặt toàn bộ gói NPM:
   ```bash
   npm install
   ```
3. Khởi tạo file liên kết biến môi trường tên là `.env.local` ở ngay nơi này chặn đầu cầu nối gọi vào backend:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
   *(Ghi chú: Nếu hệ thống bạn gọi API ở port mạng khác, hãy điều chỉnh cho bằng phù hợp).*
4. Khởi chạy cỗ máy chủ Client phía frontend liên thông kết xuất trang web:
   ```bash
   npm run dev
   ```
   > **Lưu ý**: Giao diện ứng dụng Next.js giờ sẽ được truy xuất hoàn chỉnh, theo dõi nóng sự sửa đổi ở link: `http://localhost:3000`. Nút đăng kí, đăng nhập sẽ tự động gọi luồng dữ liệu về phía cục quản lí server chạy song song phía trên.

---

## Tài Liệu Tham Khảo Mở Rộng Hệ Thống (References)

Thông tin bản vẽ chuyên sâu, triết lí thiết kế hiển thị chuẩn mực quốc tế (Design System UX/UI), chi tiết cấu hình điểm nối APIs và nền móng kĩ thuật Auth Token: 
👉 Hãy theo dõi xuyên suốt trong tài liệu: **[docs/TONG_HOP_TAI_LIEU.md](docs/TONG_HOP_TAI_LIEU.md)**.
