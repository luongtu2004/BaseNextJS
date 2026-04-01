# Tài Liệu Hệ Thống Tổng Hợp - Sàn Dịch Vụ 24/7

Tài liệu này tổng hợp Hệ thống Thiết kế (Design System), Đặc tả Giao diện Mobile (Mobile UI Specification), và Hướng dẫn Tích hợp Xác thực (Authentication) thành một bản tham chiếu hợp nhất duy nhất cho nền tảng "Sàn Dịch Vụ".

---

## PHẦN 1: HỆ THỐNG THIẾT KẾ & TRIẾT LÝ (DESIGN SYSTEM & PHILOSOPHY)

### 1.1 Tổng quan & Định hướng Sáng tạo
Hệ thống thiết kế này được tạo ra nhằm xóa nhòa ranh giới giữa thiết kế web chuẩn biên tập cao cấp (high-end editorial) và sự gần gũi tự nhiên của iOS 17. Kim chỉ nam sáng tạo của chúng ta là **"Phong cách Biên tập Xuyên thấu" (The Translucent Editorial).**

Chúng ta sẽ từ bỏ các khuôn mẫu cứng nhắc, dạng lưới của các ứng dụng di động thông thường để hướng tới một trải nghiệm mượt mà, phân tầng. Bằng cách tận dụng các khoảng trắng rộng rãi và nghệ thuật chữ đậm nét, hệ thống UI này như được "tràn đầy sức sống". Nét đặc trưng được tạo nên từ sự bất đối xứng có chủ ý—đặt nội dung lệch tâm hoặc xếp chồng các hình khối—cùng với sự ưu tiên về chiều sâu không gian thay vì kẻ viền. Đây không chỉ là một giao diện, mà còn là một bề mặt kỹ thuật số mang lại cảm giác chân thực giống như một trang giấy mịn và hiện đại như một tấm kính cường lực.

### 1.2 Triết lý về Màu sắc & Bề mặt (Colors & Surface)
Bảng màu được phát triển dựa trên sự giao thoa tinh tế giữa sắc Xanh Rừng Sâu (Deep Forest Green) cùng với màu Xanh Navy sắc nét, được tùy chỉnh tối ưu cho giao diện thiết bị di động.
- **Màu chủ đạo (Primary)**: #00523b (Deep Forest Green)
- **Màu nền (Background)**: #f9f9fe (Crisp Surface - Bề mặt sáng)
- **Màu khối nền (Container)**: #f3f3f8 (Secondary Tonal Shift)

**Quy tắc "Không Viền" (The "No-Line" Rule)**
Để duy trì cảm giác cao cấp, **nghiêm cấm việc sử dụng đường viền khối 1px để chia cắt các phần.** Sự tách biệt phải được thiết lập thông qua sự chuyển đổi dải màu. Ví dụ: một khối nền `surface-container-low` nên được đặt trên một lớp nền `surface` tổng. Nếu thực sự thấy cần khoảng cách, hãy dùng khoảng trắng (`spacing-4` hoặc cao hơn) để thay thế cho đường kẻ.

**Sự phân bậc & Lồng ghép bề mặt (Surface Hierarchy & Nesting)**
Mỗi UI đều được phân lớp rõ rệt theo thứ tự ưu tiên:
- **Lớp Đáy (Base Layer):** `surface` (#f9f9fe) - Phần khung canvas.
- **Lớp Cấp Hai (Secondary Level):** `surface-container-low` (#f3f3f8) - Dành cho nội dung thụt lề hoặc các nhóm danh sách.
- **Lớp Tương tác (Interactive Level):** `surface-container-lowest` (#ffffff) - Các thẻ (cards) có độ tương phản cao để kích thích thao tác chạm.
- **Lớp Nổi (Overlay Level):** Sử dụng các phiên bản nửa trong suốt của `surface-bright` kết hợp với hiệu ứng Backdrop Blur mờ 20-30px.

**Quy tắc Kính cường lực & Chuyển màu Gradient**
Các phần tử trôi nổi trên màn hình (Thanh điều hướng - Navigation Bars, Bảng thao tác - Action Sheets) bắt buộc áp dụng **Glassmorphism**. Sử dụng lớp màu `surface-tint` với độ đục 10-15% đè trên lớp viền mờ ảo. Đối với các Nút kêu gọi hành động (CTA), sử dụng bộ chuyển màu sắc mượt mà (linear gradient) từ `primary` (#00523b) đến `primary-container` (#1a6b51) ở góc 135 độ để tạo chiều sâu và linh hồn cho nút bấm.

### 1.3 Cấu trúc Chữ (Typography): Tiếng nói của Hệ thống
Chúng ta sử dụng font chữ **SF Pro** (hoặc Inter cho web) để mô phỏng hình dáng của iOS 17 nhưng kết hợp với khả năng thay đổi tỷ lệ tương phản cao.
*   **Tiêu đề Lớn (Display):** Sử dụng `display-lg` (3.5rem) cho các phần Hero Header. Phong cách này bắt chước thẻ tiêu đề siêu lớn của iOS nhưng thu hẹp lại khoảng cách các tự (-0.02em) nhằm tạo nét đặc thù mang tính biên tập.
*   **Tiêu đề mục (Headline):** Cỡ chữ `headline-lg` (2rem) đóng vai trò cho việc bắt đầu mỗi đoạn nội dung. Dày nét và uy lực.
*   **Nội dung cơ bản (Body Copy):** `body-lg` (1rem) là trụ cột chính. Ưu tiên hàng đầu cho việc dễ đọc (khoảng cách dòng 1.5).
*   **Nhãn phụ (Labels):** Dùng `label-md` (0.75rem) kết hợp tông màu `on-surface-variant` (#3f4944) cho nội dung bổ trợ. Tránh việc tranh giành sự chú ý của câu chuyện chính.

**Hệ thống phân cấp:** Thông điệp nhận diện của thương hiệu đến từ sự chênh lệch kích thước—giữa các tiêu đề siêu lớn `display` đứng cạnh các nội dung `label` mỏng manh—tạo một cảm giác sang trọng, rộng không gian.

### 1.4 Độ cao & Chiều sâu (Elevation & Depth)
Chiều sâu trong thiết kế là một công cụ giúp tập trung hiển thị chứ không phải chỉ dùng để trang trí tạo bóng.
*   **Nguyên lý Xếp lớp:** Tránh làm đổ bóng viền khi mà thay đổi màu sắc background đã đủ để phân rõ ranh giới. 
*   **Ánh sáng Không gian (Ambient Shadows):** Chỉ các yếu tố thật sự đứng tách biệt hẳn (VD như thẻ nút bấm hành động) thì mới cần tạo một "bóng đổ khuyếch tán diện rộng" (extra-diffused):
    *   *Độ lệch (Offset):* 0px 10px
    *   *Mờ góc (Blur):* 40px
    *   *Màu sắc:* `on-surface` (#1a1c1f) ở mức 6% opacity.
*   **Viền Bóng Ma (Ghost Border):** Nếu bắt buộc phải có đường viền cạnh để đáp ứng chuẩn khả năng tiếp cận (accessibility), sử dụng kiểu Ghost Border: `outline-variant` (#bec9c2) với 15% opacity. Tuyệt đối không dùng 100% border đen đậm.
*   **Hiệu ứng Kính mờ (Glassmorphism):** Thanh điều hướng dưới cùng dùng màu nền `surface` tổng bằng độ đục 80% kèm hiệu ứng lọc `blur(20px)`.

### 1.5 Các Thành phần Cấu tạo (Components)
*   **Các Thẻ (Cards) & Danh Sách (Lists):** Bắt buộc sử dụng bán kính bo góc siêu lớn như `lg` (32px) hoặc `xl` (48px) đồng bộ thống nhất theo hướng mềm mại (organic).
    *   **Chia tách:** Không dùng dây divider 1px mỏng manh. Sử dụng khoảng cách `spacing-3` (1rem) hoặc chuyển tông màu để phân cách.
*   **Nút bấm (Buttons):**
    *   **Nút chính (Primary):** Đổ bóng chuyển viền Gradient của `primary`, bo tròn hoàn toàn dạng viên thuốc, chữ `on-primary`.
    *   **Nút phụ (Secondary):** Nền Background `surface-container-highest` đẩy nổi bề mặt kèm chữ màu `primary`. Không bo viền kẻ.
*   **Khung nhập (Input Fields):** Dạng thuốc con nhộng mềm mại (`rounded-full`) hoặc khối cong lớn (`rounded-lg`) với mảng nền `surface-container-low`.
    *   **Lúc đang Focus:** Gắn một "Ghost Border" viền mờ 2px màu `primary` độ phân giải 40% opacity.

### 1.6 Điều nên làm và không nên làm (Do's and Don'ts)
*   **Việc NÊN (Do)**
    *   *Do* sử dụng `primary-fixed-dim` (#8ad6b6) lót màu sau lưng các Icon làm cho chúng mang đặc tính của iOS chuẩn native app.
    *   *Do* dũng cảm bố trí phá vỡ tính đối xứng. Nếu chữ lớn dóng phía bên trái, bài text minh họa có thể nhô thêm một xíu sang phải.
*   **Việc ĐỪNG (Don't)**
    *   *Don't* Không sử dụng mã đen nguyên bản (#000000) đổ bóng shadow. Hãy dùng lớp shadow pha xám đã ám màu của `on-surface`.
    *   *Don't* Không dùng dải kẻ divider phân ô ngang bằng cỡ ngón xíu. Hãy tăng không gian chuyển bậc `surface` tách mạch chúng ra.
    *   *Don't* Không xài các dạng "Drop Shadows" đổ bóng cũ kĩ tiêu chuẩn cơ bản. Thiết kế mới cần "Ánh sáng không gian lan tỏa".

---

## PHẦN 2: THIẾT KẾ GIAO DIỆN MOBILE & LIÊN KẾT API (MOBILE UI & API)

### 2.1 Nguyên Tắc Thiết Kế Chi Tiết Mobile
- **Tính Xuyên Suốt Mượt Mà (Editorial Fluidity)**: Tập trung vào khoảng trắng rộng, hiển thị phong cách nghệ thuật đọc Font Manrope đậm và Font Inter mỏng cơ bản.
- **Glassmorphism**: Áp dụng triệt để độ mờ Backdrop Blur làm xuyên viền đối với Header vuốt qua.
- **Organic Shapes (Hình hài tự nhiên)**: Luôn giữ bo góc uốn 32px –> 48px đỉnh cao cho các vùng khối container vuốt chìm xuống.

### 2.2 Đặc Tả Tương Tác Hành Động
- **Kéo để làm mới (Pull to Refresh)**
  - Hành vi vuốt kéo căng khung chứa trên màn hình trồi ra nhịp độ nảy 'Spring' xịn xò của Apple. Yêu cầu tải gọi lại API `GET` mới nhất nạp chồng lên bộ nhớ ảo cache cũ.
- **Cửa sổ trượt từ dưới lên (Bottom Sheets)**
  - Mục đích cho hành vi nhấn mạnh, hoặc xác nhận chốt thoát người dùng trơn tru, màn filter bộ lọc phức tạp. Thiết kế dạng vuốt cong khổng lồ **48px**, có lớp sương mờ dính đáy tối (Blur 25px).

### 2.3 Cấu trúc Ứng dụng & Luồng Màn hình

#### 2.3.1 Luồng Khởi động và Xác Thực
- **Màn Hình Chờ (Splash Screen)**
  - Biểu lộ hình ảnh và bản sắc thương hiệu lúc đầu, có check nhúng Session ngầm lập tức. Dùng các điểm đỗ API: `GET /health` và phiên check token `GET /api/v1/common/me`.
- **Màn Hình Đăng Nhập (Login Screen)**
  - Các input nạp giá trị bo khung bán kính mềm 24px láng mượt. Gọi trực diện hàm cấp vé vào cổng API: `POST /api/v1/auth/login/password`.
- **Màn Hình Đăng Ký (Register Screen)**
  - Tuy là 2 luồng quy trình bước nhưng thiết kế tích hợp lướt trượt siêu gọn 1 trang khung. Gọi API: `POST /api/v1/auth/register`.
- **Nhập Mã Phê Chuẩn (OTP Verification)**
  - Lưới hiển thị rời rạc 6 con số đếm, tự động có cục Count đếm giờ chạy nhảy (Khoảng 60s chờ để ấn tiếp). Hoạt động nhờ API `POST /api/v1/auth/otp/send` và API đối soát xác tín `POST /api/v1/auth/otp/verify`.

#### 2.3.2 Màn Hình Chính (Home Screen / Explore)
- **Nơi chốn Khám phá, Trải nghiệm Tin tức Dịch vụ ngang – nằm dọc cuốn tự nhiên.**
- **Hiển thị lấy data qua API**:
    - Khu Bài viết ưu đãi (News / Promo Feed): `GET /api/v1/common/posts`.
    - Khu Nhóm Ngành Mũi Nhọn (Industry Pillars): Gọi API qua bảng danh sách tĩnh dọc `GET /api/v1/customer/industry-categories`.

#### 2.3.3 Màn Khám Phá & Tìm kiếm Thợ (Discovery & Search)
- **Trình Duyệt Danh Mục Con (Category Browser)**
  - Cho user chọn dịch vụ ngách, xuyên thấu các lớp ngành sâu bên trong (ví dụ Điện Lạnh -> Bơm Ga Máy Lạnh). Setup giao diện hiển thị vạch 2 ô theo lưới, hình nổi khổng lồ 48px. Dòng mã Data API: `GET /api/v1/customer/industry-categories/{id}/service-categories`.
- **Thanh Công Cụ Tìm Thông Minh (AI Search Bar)**
  - Search engine tự nhận diện truy vấn câu hội thoại tự nhiên của con người thông qua GET: `GET /api/v1/customer/search`.
  - Hiển thị Lưới hồ sơ thợ sửa theo dạng thẻ bài (Card) kèm hình cá nhân uy tín vạch sao, khối số Job giao kèo cùng lời Tự Giới thiệu Profile.
  - Phụ thuộc thuật toán máy lọc: Giá (Price), Chặng đường (Distance), Dấu mốc bình duyệt (Rating).

#### 2.3.4 Chi Tiết Hồ Sơ Thợ Cung Cấp (Provider Details)
- **Tags Năng lực (Expertise Tags)**: Ghi chú đánh dấu danh nghề giỏi nhất, vinh danh của họ qua Endpoint `GET /api/v1/customer/providers/{id}`.
- **Liên hệ siêu tốc (Contact Action)**: Cái phao nổi lửng lơ trên app FAB nháy liên tục chốt bấm điện thoại trực tiếp hoặc qua Ứng dụng tin nhắn (Ví dụ Zalo / WhatsApp). Lộ trình công việc thợ show sẵn `GET /api/v1/customer/providers/{id}/services`.

#### 2.3.5 Chế Độ Chuyển Biến Làm Thợ (Partner Workspace)
Khởi động bằng việc bấm thanh lật gạt switch ở Profile User - Biến thành Không gian làm ăn.
- **Bảng điểu khiển (Partner Dashboard)**: Có nút chuyển chế độ cày thuê (Online hay Nghỉ ngơi Offline) chạy đến `PUT /api/v1/provider/profile`. Lấy xem dữ liệu doanh thu đơn bùng nổ `GET /api/v1/provider/profile`.
- **Tùy chỉnh Công Việc Đề xuất Của Bản Thân**: List sẵn sàng và Nạp thêm nghề chạy bằng API `POST /api/v1/provider/services` qua forms ma thuật khuyên trọn viền 48px radio button.

#### 2.3.6 Thiết Lập Danh Tính (Settings Screen)
- Hồ sơ hình đại diện bao la với thẻ bo lớn `GET /api/v1/common/me`. (Xem avatar, họ tên và định dạng người dùng Guest hay Admin).
- Nút kích Đăng xuất (Log Out Button) châm ngòi màn cảnh báo rút lui hộc dưới sàn `POST /api/v1/auth/logout`.

---

## PHẦN 3: TÍCH HỢP HỆ THỐNG XÁC THỰC BẢO MẬT (AUTHENTICATION INTEGRATION)

### 3.1 Tổng Quan Cơ Bản
Nền tảng của chúng ta có luồng an ninh tối cao chốt chặn, xử lý 3 cách thức làm mượt dòng User chui vô:
1. **Duyệt Đăng Ký**: Số điện thoại cầm tay + OTP mã hóa 1 chiều + Lên mật khẩu kiên cố vĩnh viễn.
2. **Truy Cập Đăng Nhập Cũ**: Tên số điện thoại + Pass.
3. **Đăng nhập Siêu tốc (OTP thẳng)**: Nhảy bỏ khâu nhớ pass dài dòng, xin lại mã tin nhắn SMS 6 con số nạp và bẻ khóa trực tiếp (Dành để thay đổi chức năng Quên mật mã kiểu hiện đại).

### 3.2 Đường dẫn API Chức Năng Cốt Lõi (API Endpoints)

**1. Gửi Mã Phê Chuẩn OTP (`POST /api/v1/auth/otp/send`)**
Giao tiếp gửi số theo JSON: `{ "phone": "0912345678" }`
Nhận lại Session và bộ định thì thời hạn khóa của OTP (Khoảng 300s):
`{ "otp_session_id": "uuid....", "expired_in": 300 }`
*(Châm chước tại thời kì local-dev sẽ log văng kết quả mã OTP vô bảng Backend terminal).*

**2. Đăng Ký Ấn Định Tạo Form (`POST /api/v1/auth/register`)**
Gửi đi bản thể: `{ "phone": "...", "full_name": "...", "password": "...", "otp_code": "123", "otp_session_id": "uuid" }`
Trả về giỏ quà bảo an: `{ "access_token": "...", "refresh_token": "...", "user": {...}, "roles": ["customer"] }`

**3. Khớp Cổng Bằng Pass Định Danh (`POST /api/v1/auth/login/password`) / Mật Cấp Cứu (`.../login/otp`)**
Một đường gửi Mật khẩu, một đường gửi lại OTP nhận. Hơi khớp liền hoàn trả cặp chứng thư JWT xịn.

**4. Dịch Vụ Cấp Cứu Trẻ Hóa Token Tàn (`POST /api/v1/auth/refresh`)**
Token hỏng sau 15p -> Vác vé Refresh 30 ngày chùi lên đổi lại thẻ VIP mới: `{ "refresh_token": "..." }`

**5. Huy Hủy Xác Nhận Nghỉ Chơi (`POST /api/v1/auth/logout`)**
Giật nổ bom giết tan đi Refresh đang cài cắm trong Database. Trả lại tín hiệu `{ "success": true }`.

### 3.3 Chuẩn Mực Sử Dụng Giao Diện Khách (Frontend Next.js App Router)

**Xài Context Quản lý Phiên (Global AuthContext)**
Giao diện tuyệt đối không bấu cấu cào xé file mảng Token thủ công, tất cả phó thác gọi `AuthContext`.
- Bất kì thẻ nào muốn bắt bẻ người ta chỉ dùng `const { user, isAuthenticated, login, logout } = useAuth();`. Chưa có vé đuổi khéo ngay lập tức không cho tải trang.

**Xử Lý Bước Login / Register ở Client**
Tiến hành hàm `await register({...})`.
Thành công ngon nghẻ, đút Data vô túi js-cookie tự nhét, và chuyển vội lệnh lật trang `router.replace('/')`. Không dùng `.push()` lùi lại rác cache.
Hành vi `logout()` tự gánh rạch nát vé Cookie, kêu API gạt trôi database và tống cổ user đứng ngắm ở `/login`.

**Người Gác Cổng Edge Server (Middleware)**
Một chốt kiểm được gài ngay ở mép vùng NextJS (`middleware.ts`).
- Chưa có visa -> Trục xuất khỏi trang quản lý `/admin`, hay trang thiết lập bản thân `/profile` quỳ về `/login`.
- Đã lỡ ghim visa thành tài -> Quét khỏi `/login` ép đi tiếp. Cầm token chọt móc thẳng api cookies siêu nhanh cấp server edge runtime.

### 3.4 Sơ Đồ Quy Trình An Ninh Lưới Di Chuyển (Security Flow Diagram)

```
┌────────────────┐      ┌────────────────┐      ┌────────────────┐      ┌────────────────┐
│  Register      │ ──►  │ Gửi SMS OTP    │ ──►  │ Thu nạp mã OTP │ ──►  │ In Database    │
└────────────────┘      └────────────────┘      └────────────────┘      └────────────────┘
                          (Mô phỏng gõ)          (Nhét Kèm Tên/Pass)     (Quyền Customer)
                                                                                  │
┌────────────────┐      ┌────────────────┐      ┌────────────────┐                ▼
│  Login         │ ──►  │ Check Pass cũ  │ ──►  │ In Mã Lệnh     │ ◄──────────────┘
└────────────────┘      └────────────────┘      └────────────────┘
```

**Tính Năng Vượt Trội Bảo Mật Triệt Để**
1. **Băm Vịn Pass (Password Hashing)**: Công cụ BCrypt hủy mọi vết tích kể cả khi có kẻ xé toạc server xem lén.
2. **Kẹp Miếng JWT Kép**: Vé đi lại bay nhảy Access 15p. Vé cứu hộ Refresh 30 ngày an bình.
3. **Giới Hạn Giảm Tải Ngôn Ngữ Máy OTP**: Có giờ chết 5 phút. Vặn ổ 5 sai lần là block luồng chặn DDoS tốn tiền SMS.
4. **CORS Rào Quây**: Endpoint trơ gan mặc kệ máy khách khác web `localhost:3000` réo gọi.

### 3.5 Cấu Hình Môi Trường Dev & Bắt Bệnh Gỡ Rối (Testing & Troubleshooting)

**File Chứa Điều Lệ Gắn Lên Máy Chủ (`.env`)**
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/sandichvu
JWT_ACCESS_SECRET=bo_ghi_chu_sieu_bi_mat_1
JWT_REFRESH_SECRET=bo_ghi_chu_sieu_bi_mat_2
OTP_LENGTH=6
OTP_TTL_SECONDS=300
OTP_MAX_ATTEMPTS=5
CORS_ORIGINS=http://localhost:3000
```
*Và cho màn frontend `.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8000`*

**Bắt Bệnh và Khám Rối (Troubleshooting)**
- **Bắt Mạch "Invalid OTP"**: Hoặc máy nháy trễ 5 phút tàn tạ mã, vuốt quá 5 lần tịt luồng, nhét khống bậy bạ sai con dâu.
- **Lỗi Mã Xác Bị Gắn mác "Invalid credentials"**: Đánh lệch tay phím hoa số điện thoại/Mật khẩu.
- **Chặn Ngang Việc Bắn "Phone already registered"**: Tồn tại rồi, gí sdt khác vô hoặc đi tới màn đăng nhập lại cho lẹ.

---
*Ghi Chú Nền Tảng Chấm Dứt File Thuật Ngữ Hệ Thống*
