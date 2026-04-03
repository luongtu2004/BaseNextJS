# Sàn Dịch Vụ 24/7 (Service Marketplace)

## 1. Tổng Quan (Overview)
Dự án nền tảng kết nối người dùng có nhu cầu tìm kiếm dịch vụ sửa chữa (Customer) với các chuyên gia/nhà cung cấp dịch vụ độc lập (Provider/Partner). Giải pháp phần mềm bao gồm ứng dụng người dùng cuối và hệ thống quản trị trung tâm.

## 2. Công Nghệ Sử Dụng (Tech Stack)
- **Frontend**: Next.js (App Router), React, TailwindCSS, TypeScript. Điển hình cho kiến trúc SSR và Client rendering tốc độ cao.
- **Backend**: FastAPI, Python 3.10+, PostgreSQL, SQLAlchemy ORM. Cung cấp hệ thống RESTful API tĩnh ổn định và hiệu năng cao.
- **Security & Authorization**: Sử dụng JSON Web Tokens (JWT) với Access Token và Refresh Token cho hệ thống xác thực. Khóa mật khẩu được mã hóa an toàn bằng thuật toán BCrypt.

---

## 3. Hướng Dẫn Cài Đặt và Khởi Chạy (Setup & Run)

Môi trường phát triển cục bộ (Local Development) yêu cầu máy tính của bạn đã được cài đặt: **Node.js 18+**, **Python 3.10+**, và **PostgreSQL** (Ví dụ qua pgAdmin hoặc cài mặc định của PostgreSQL).

### 3.1 Khởi chạy Backend (FastAPI Services)

1. Mở phần mềm quản lý Database (PostgreSQL) và tiến hành tạo một Database mới với tên là `sandichvu`.
2. Mở trình dòng lệnh (Terminal/Command Prompt) trỏ vào thư mục `backend`:
   ```bash
   cd backend
   ```
3. Tạo và kích hoạt môi trường ảo (Virtual Environment) để cài đặt thư viện độc lập:
   ```bash
   # Tạo môi trường ảo (chỉ cần chạy lần đầu tiên)
   python -m venv venv

   # Kích hoạt trên Windows
   .\venv\Scripts\activate
   # Kích hoạt trên macOS/Linux shell
   source venv/bin/activate
   ```
4. Cài đặt toàn bộ thư viện cần thiết từ file requirements:
   ```bash
   pip install -r requirements.txt
   ```
5. Đổi tên file cấu hình từ `.env.example` thành `.env` (hoặc tạo file mới mang tên `.env`) và thiết lập các biến kết nối trong thư mục `backend`:
   ```env
   # Thay thế pass_cua_ban bằng Mật khẩu PostgreSQL của máy tính của bạn
   DATABASE_URL=postgresql://postgres:pass_cua_ban@localhost:5432/sandichvu
   JWT_ACCESS_SECRET=your_super_secret_access_key
   JWT_REFRESH_SECRET=your_super_secret_refresh_key
   OTP_LENGTH=6
   OTP_TTL_SECONDS=300
   OTP_MAX_ATTEMPTS=5
   CORS_ORIGINS=http://localhost:3000
   ```
6. Khởi chạy máy chủ Backend ở chế độ Development (tự động load lại khi file thay đổi):
   ```bash
   uvicorn app.main:app --reload
   ```
   > **Lưu ý**: Server FastAPI sẽ lắng nghe tại địa chỉ `http://localhost:8000`. Bạn nên truy cập vào API Documentation tương tác tại URL `http://localhost:8000/docs` (Swagger UI). Với tính năng giả lập hiện tại của mã OTP, mã xác thực này sẽ được in trực tiếp ra ở màn hình Terminal Backend khi có Request.

### 3.2 Khởi chạy Frontend (Next.js Application)

1. Khởi tạo một cửa sổ Terminal mới và trỏ đến thư mục gốc của dự án (nơi có chứa `package.json`).
   ```bash
   # Di chuyển vào thư mục dự án
   cd sandichvu
   ```
2. Tải và cài đặt các Packages/Dependencies của Node.js:
   ```bash
   npm install
   ```
3. Khởi tạo file biến số môi trường với tên `.env.local` ở ngay thư mục gốc của Frontend:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
4. Khởi chạy server Frontend:
   ```bash
   npm run dev
   ```
   > **Lý thuyết hoạt động**: Client Node.js server lúc này đã được cung cấp tại địa chỉ tĩnh Base URL là `http://localhost:3000`. Sử dụng trình duyệt để truy cập đường dẫn này và bạn có thể thử luồng luân chuyển đăng nhập Login/Register.

---

## 4. Tài Liệu Thiết Kế Kỹ Thuật (System Documentation)

Tài liệu thiết kế bao gồm định hướng trải nghiệm người dùng (UX/UI Design System), quy trình luân chuyển trạng thái qua các Màn hình Ứng dụng, bản đồ đối chiếu các API vào tính năng của Frontend, cũng như quy trình làm việc của Token & Security.
👉 Đọc tại đây: **[docs/TONG_HOP_TAI_LIEU.md](docs/TONG_HOP_TAI_LIEU.md)**.
