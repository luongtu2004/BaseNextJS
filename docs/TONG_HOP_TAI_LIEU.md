# Tài Liệu Hệ Thống Tổng Hợp - Sàn Dịch Vụ 24/7

Tài liệu này tổng hợp Hệ thống Thiết kế (Design System), Đặc tả Giao diện Mobile (Mobile UI Specification), và Hướng dẫn Tích hợp Xác thực (Authentication) thành một bản tham chiếu hợp nhất duy nhất cho nền tảng "Sàn Dịch Vụ".

---

## PHẦN 1: HỆ THỐNG THIẾT KẾ & TRIẾT LÝ (DESIGN SYSTEM & PHILOSOPHY)

### 1.1 Tổng Quan & Định Hướng Sáng Tạo

Hệ thống thiết kế này được tạo ra nhằm xóa nhòa ranh giới giữa thiết kế web chuẩn Editorial cao cấp và sự mạch lạc tự nhiên của iOS 26. Kim chỉ nam sáng tạo của hệ thống là **"Phong cách Biên tập Xuyên thấu" (The Translucent Editorial).**

Thiết kế từ bỏ các khuôn mẫu cứng nhắc, dạng lưới hộp của các ứng dụng di động thông thường để hướng tới một trải nghiệm mượt mà và phân tầng. Bằng cách tận dụng các khoảng trắng rộng rãi và nghệ thuật Typography đậm nét, giao diện trở nên thanh thoát và sống động hơn. Điểm nhấn thị giác được tạo nên từ sự bất đối xứng có chủ ý — đặt nội dung lệch tâm hoặc xếp chồng các hình khối — cùng ưu tiên về chiều sâu không gian thay vì sử dụng viền kẻ cố định.

### 1.2 Triết Lý về Màu Sắc & Bề Mặt (Colors & Surface)

Bảng màu được phát triển dựa trên sự giao thoa tinh tế giữa sắc Xanh Rừng Sâu (Deep Forest Green) cùng với màu Xanh Navy sắc nét, được tùy chỉnh tối ưu cho nền tảng Mobile-first.

- **Màu chủ đạo (Primary)**: #00523b (Deep Forest Green)
- **Màu nền (Background)**: #f9f9fe (Crisp Surface - Bề mặt sáng)
- **Màu khối nền (Container)**: #f3f3f8 (Secondary Tonal Shift)

**Quy tắc "Không Viền" (The "No-Line" Rule)**
Để duy trì cảm giác cao cấp, **tránh việc sử dụng đường viền (border) 1px để phân chia nội dung.** Sự tách biệt không gian phải được thiết lập thông qua thay đổi sắc độ màu nền. Ví dụ: một khối nền `surface-container-low` nên được đặt trên một nền `surface` tổng. Trong trường hợp cần gia tăng khoảng cách, hãy dùng khoảng trắng (`spacing-4` hoặc cao hơn) để thay thế đường mảnh.

**Phân Bậc & Lồng Ghép Bề Mặt (Surface Hierarchy & Nesting)**
Các thành phần giao diện (UI Components) được phân lớp rõ rệt theo mức độ tương tác:

- **Lớp Nền (Base Layer):** `surface` (#f9f9fe) - Phần khung cố định nền.
- **Lớp Thứ Cấp (Secondary Level):** `surface-container-low` (#f3f3f8) - Dành cho nội dung khối thụt lề hoặc các thẻ danh sách.
- **Lớp Tương Tác (Interactive Level):** `surface-container-lowest` (#ffffff) - Các thẻ (cards) nổi cần điểm chạm và tương tác lớn.
- **Lớp Phủ (Overlay Level):** Áp dụng hiệu ứng nửa trong suốt `surface-bright` kết hợp kỹ thuật Backdrop Blur từ 20-30px.

**Quy Tắc Kính Mờ (Glassmorphism) & Gradient**
Các thành phần hiển thị nổi (Navigation Bars, Action Sheets) bắt buộc áp dụng **Glassmorphism**. Sử dụng lớp màu `surface-tint` với opacity 10-15% đè trên hiệu ứng Blur nền mờ ảo. Đối với Nút Gọi Hành Động chính (CTAs - Call to Action), sử dụng phổ màu chuyển (linear gradient) từ `primary` (#00523b) đến `primary-container` (#1a6b51) ở góc 135 độ để gia tăng chiều sâu cho nút bấm.

### 1.3 Nghệ Thuật Chữ (Typography)

Dự án sử dụng font chữ **SF Pro** (hoặc Inter khi trên web) để mô phỏng hình dáng của ứng dụng iOS 26 chuẩn kết hợp khả năng thay đổi tỷ lệ tương phản linh hoạt.

- **Tiêu Điểm (Display):** Sử dụng dạng `display-lg` (3.5rem) cho các phần Hero Header. Phong cách này mang dáng dấp của kích thước Large Title trên iOS nhưng chủ động thu hẹp lại khoảng cách chữ (letter spacing -0.02em) tạo thiết kế độc quyền.
- **Tiêu Đề (Headline):** Cỡ chữ `headline-lg` (2rem) đóng vai trò cho việc mở đầu mỗi phân mục.
- **Nội Dung Cuốn (Body Copy):** `body-lg` (1rem) dùng cho thông tin hiển thị bao hàm. Ưu tiên hàng đầu cho việc dễ đọc (khoảng cách line-height 1.5).
- **Nhãn Thông Tin (Labels):** Dùng `label-md` (0.75rem) kết hợp tông màu `on-surface-variant` (#3f4944) cho nội dung bổ trợ. Tránh việc tranh giành sự chú ý của câu chuyện chính.

**Hệ thống phân cấp Typography:** Cải thiện phân biệt sắc thái, kết hợp tiêu đề siêu lớn `display` đứng cạnh các nội dung `label` tạo một cảm giác sang trọng và phân phối không gian.

### 1.4 Độ Cao & Chiều Sâu (Elevation & Depth)

Chiều sâu không gian là một công cụ giúp tạo phân cấp thị giác rõ nét hơn, không chỉ đơn thuần là trang trí rườm rà.

- **Nguyên Lý Layer (Layering Principle):** Tránh làm đổ bóng viền khi việc thay đổi màu sắc độ Background đã đủ cho ranh giới.
- **Đổ Bóng Khuếch Tán Diện Rộng (Ambient Shadows):** Chỉ các yếu tố thật sự đứng tách biệt hẳn (Ví dụ: Thể chứa Action trôi nổi) thì mới cần tạo Ambient Shadow:
  - *Độ Lệch Trục (Offset):* 0px 10px
  - *Góc Mờ (Blur):* 40px
  - *Màu Sắc (Color):* Màu `on-surface` (#1a1c1f) ở mức 6% opacity.
- **Viền Phụ (Ghost Border):** Nếu cần thêm có đường viền cạnh đáp ứng Accessiblity, dùng mảng Ghost Border định dạng: `outline-variant` (#bec9c2) với 15% opacity. Tuyệt đối không dùng 100% border dạng nét đứt đen tuyền.
- **Hiệu Ứng Kính Mờ (Glassmorphism):** Thanh điều hướng dưới cùng dùng màu nền `surface` tổng bằng độ đục 80% kèm hiệu ứng lọc `blur(20px)`.

### 1.5 Thành Phần Giao Diện (Components)

- **Thẻ Thông Tin & Danh Sách (Cards & Lists):** Định dạng bo góc nhất quán sử dụng hình khuyết góc lớn như `lg` (32px) hoặc `xl` (48px) đồng bộ thống nhất theo hướng mềm mại (organic curves).
  - **Chia tách:** Hạn chế đường phân cách (divider) mảnh. Sử dụng thuộc tính `spacing-3` (1rem) hoặc đẩy sắc độ mảng hiển thị màu.

- **Nút Bấm (Buttons):**
  - **Nút chính (Primary):** Thiết kế bo góc hình viên thuốc hoàn chỉnh dạng pill, phối Gradient chuyển hướng từ `primary`, đi sát nền với text sáng nổi bật `on-primary`.
  - **Nút phụ (Secondary):** Nền Background tráng lớp `surface-container-highest` đẩy nổi lên bề mặt và text màu `primary`. Không viền mảng.
- **Hộp Văn Bản Nhập Liệu (Input Fields):** Dạng thuốc con nhộng mềm mại hình viên thuốc (`rounded-full`) hoặc khối cong hộp viền (`rounded-lg`) dùng chất liệu `surface-container-low`.
  - **Đang lấy nét nhấp nhập liệu (Focus State):** Kết hợp "Viền Phụ Ghost" 2px dùng màu `primary` opacity 40%.

### 1.6 Quy Tắc Áp Dụng (Do's and Don'ts)

- **Việc NÊN (Do)**
  - Tái sử dụng `primary-fixed-dim` (#8ad6b6) lút ở Background cho cấu phần trang trí Icon biểu đạt tính năng Native chuẩn mực cho iOS.
  - Kết hợp bố cục bất đối xứng phá cách. Ví dụ như headline kéo ở lề trái, text content đẩy mạnh ra biên độ giữa để tạo cấu trúc.

- **Việc ĐỪNG (Don't)**
  - Không sử dụng mã màu đen nguyên bản (#000000) vào nền tảng đổ Shadow, bắt buộc thay thể bằng những dải pha màu khói `on-surface` ám.
  - Không dùng kẻ chỉ mảnh `divider` 1px chia ngang dọc các khối liên phân.
  - Hạn chế nhồi nhét text đè lên ảnh. Phải đảm bảo không gian trải đều Margin.

---

## PHẦN 2: THIẾT KẾ GIAO DIỆN MOBILE & KẾT NỐI API (MOBILE UI & API)

### 2.1 Đặc Trưng Thiết Kế Cơ Bản Mobile

- **Tính Liền Mạch (Editorial Fluidity)**: Tập trung gia tăng mảng khoảng trắng lớn có chủ ý, sử dụng Manrope Bold tại Header lớn và Inter mỏng vào các phần hiển thị văn bản chi tiết nhỏ gọn.
- **Backdrop Blur & Glassmorphism**: Đặc thù làm hiệu ứng Header trong mờ nhẹ vuốt khi cuộn trang nội dung.
- **Kiểu Dáng Dòng Chảy (Organic Shapes)**: Giữ các cạnh bo góc lớn bo cong từ góc siêu dài 32px lên tận 48px trên mọi bề mặt Container chính mảng.

### 2.2 Đặc Tả Thao Tác Trực Quan (Interactions)

- **Kéo để làm mới (Pull to Refresh)**
  - Tích hợp động năng khi thực hiện lướt vượt quá trên thanh cuộn (overscroll) trả về một "Spring" mô phỏng đàn hồi như bản chất Native Core của nhà táo iOS. Tác dụng sẽ tự động Refresh gửi lại điểm API dạng Restful `GET` và reload thông tin trong trang nội bộ, làm mới Cache Storage hiện tại.
- **Màn Hình Lướt Ẩn/Hiện Chắn (Bottom Sheets)**
  - Tái sử dụng liên tọi khi người dùng đưa ra xác nhận đặc biệt, cấu trúc Filter tra soát lọc thông tin nặng. Đổ dạng cong lớn đẩy nền lướt có Radius siêu bự ***48px***, mờ sau 25px Shadow bao bọc toàn không gian.

### 2.3 Cấu Trúc Flow và Triển Khai Gọi API Endpoints

#### 2.3.1 Quy Trình Khởi Động & Xác Thực (Login/Auth Flow)

- **Màn Hình Khởi Động (Splash Screen)**
  - Hiển thị nhận diện thương hiệu. Kiểm tra trạng thái mã Token đăng nhập (Session) ngay lập tức. Nếu tìm thấy và còn sống thì nhảy thẳng luồng, nếu lỗi và sạch thì ném qua luồng SignIn.
  - Các Rest APIs: `GET /health` (Ping rà hệ thống), `GET /api/v1/common/me` (Truy tìm thẻ cước Validation Authentication).
- **Màn Hình Đăng Nhập (Login Screen)**
  - Cấu hình trang với các hộp lấy thông tin Input bo góc mềm hình trụ mảnh láng mịn cực độ vòng bo 24px.
  - Điểm API tiếp nhận Request: `POST /api/v1/auth/login/password`.
- **Màn Hình Đăng Ký (Register Screen)**
  - Quy trình hai bước (Báo số điện thoại + Điền Thông Tín Profile) được tích hợp trực diện trên một lớp Frame mượt mà tránh Reload Refresh.
  - Điểm API tiếp nhận Request: `POST /api/v1/auth/register`.
- **Luồng Xác Thực Kép (OTP Verification)**
  - Form UI Input rời rạc 6 mục rỗng đễ điển chuỗi mã xác nhận (6 con số). Liên kết một hàm Auto Count giảm ngược Countdown 60s thời gian sống.
  - Điểm API móc vào: Xin cấp gửi qua máy `POST /api/v1/auth/otp/send` và Trả mã Check Verify đối chất cho Database `POST /api/v1/auth/otp/verify`.

#### 2.3.2 Khám Phá Trang Chủ (Home Screen)

- Nơi chốn truy cập đầu tiên để phân tải lượng danh mục ngành nghề cần giải quyết, có sự cuộn tự do ngang/dọc đa tuyến mượt mà.
- **Mốc Dữ liệu Fetch:**
  - Cụm Tin tức / Bảng giá (News / Promo Feed): Trỏ vào `GET /api/v1/common/posts`. Chi tiết hiển thị gọi theo mã Slug ở `GET /api/v1/common/posts/{slug}`.
  - Cụm Ngành Lõi Công Nghiệp Nền (Industry Pillars): Gọi Rest API `GET /api/v1/customer/industry-categories`.

#### 2.3.3 Khám Phá Kỹ Lưỡng & Tra Tìm kiếm Trực Quan (Discovery & Search)

- **Mục Xem Tiểu Ngành Nhanh (Category Browser)**
  - Phân tích cặn kẽ chia lớp chuyên môn để User bọc xuống lớp ngành dọc bên trong. Setup hệ Giao diện Lưới Bảng List rập khung lưới 2 trục hai mặt đẽo thẻ 48px đỉnh cao. Hứng từ Data Backend theo link `GET /api/v1/customer/industry-categories/{id}/service-categories`.
- **Máy Soát Tìm Thông Minh Cấp Tốc (AI Search Bar)**
  - Nơi tra cứu từ khóa chuỗi chữ bằng yêu cầu con người qua hàm kết nối `GET /api/v1/customer/search`.
  - Hiển thị list thẻ thông tin Thợ cung ứng theo dạng khung Card viền cạnh lớn, kèm Avatars ảnh chân dung và nhãn uy tín của Rate Sao (Stars Rating), Tổng số Booking Của Thợ, Câu Caption ngắn quảng cáo nghề nghiệp Profile gốc tự viết.
  - Các mốc Filter điền từ Logic của FrontEnd Client cho mảng: Mức tính phí (Price), Đo lường giới hạn cây số đường di dời xa gần (Distance Radius), Dấu mốc bình duyệt qua Rating đánh chấm.

#### 2.3.4 Xem Màn Thông Tin Detail Khách Nhà Bán (Provider Details Profile)

- **Chuỗi Nhãn Đánh Giá Chuyên Nghiệp (Expertise Tags)**: Mục lục các khả năng ưu nhược điểm cốt lõi do họ trình diễn thông qua Backend `GET /api/v1/customer/providers/{id}`.
- **Tiện Ích Hành Động Gọi Tức Tối (Fast Contact Action)**: Dựa trên thanh Nút bấm trôi FAB gắn cố định lề màn hình - Thực thi một Click để Call hoặc văng thẳng sang WhatsApp / Zalo Message App. Lộ trình Booking Jobs nằm ở endpoint phụ `GET /api/v1/customer/providers/{id}/services`.

#### 2.3.5 Chuyển Kênh Môi Trường Hành Nghề Của Thợ (Partner / Provider Workspace)

Truy xuất nhanh lẹ thông qua một switch bar On/Off "Đổi sang Thợ Nghề" lằm lững trong Option Settings.

- **Bàn Nhạc Thao Tác Công Năng (Partner Dashboard)**: Toggle tắt trạng thái cày cúp: Sẵn_Sàng_Bây_Giờ (Online) / Đang_Nghỉ_Ngơi (Offline) được Push thông báo qua API `PUT /api/v1/provider/profile`. Lấy list theo dõi chỉ số biểu đồ của chính họ nằm lại gốc `GET /api/v1/provider/profile`.
- **Đăng Bán & Xin Đăng Tuyển Các Loại Phân Dịch Vụ**: Kiểm định bảng thông báo xem mình đang nắm danh sách Job báo giá bằng `GET /api/v1/provider/services` . Ấn mảng thêm nhiệm vụ mở rộng gói thông qua API `POST /api/v1/provider/services` qua Widget Wizards (Tạo đơn Setup góc 48px các nút form).

#### 2.3.6 Cấu Cấu Trúc Khung Profile Và Ra Lệnh Đăng Xuất (Settings Profile Dashboard)

- **Menu Settings**: Khung avatar rập tròn lấy Profile người có ở `GET /api/v1/common/me`. Tính năng ghi đề thay áo Update `PUT`.
- **Ấn Đăng Xuất (Logout Button Trigger)**: Nhấn nhẹ nổi hộp Bottom Sheets xác minh cảnh báo đe dọa truyển tín hiệu Logout tàn phá token Refresh đi API `POST /api/v1/auth/logout`.

---

## PHẦN 3: TÍCH HỢP HỆ THỐNG XÁC THỰC HIỆN ĐẠI (AUTHENTICATION INTEGRATION)

### 3.1 Nhận Định Tổng Phân Mô Hình Logic Cơ Sở

Hệ thống vận tải nền hỗ trợ chặt chẽ 3 giải pháp an ninh truy cập đa quyền:

1. **Flow Đăng Ký (Register Flow)**: Định dạnh Số di động cá nhân gốc + Đối sánh SMS xác thực OTP + Khóa mật khẩu vững chải.
2. **Luồng Cổng Đăng Nhập Cũ Bằng Pass (Email/Phone + Pass)**
3. **Luồng Siêu Tốc Xác Minh Nhanh Gửi OTP Thẳng Tắp Biến Tấu Đăng Nhập Mới** (Sử dụng luân phiên làm Reset Quên mật mã Password Bypass Security).

### 3.2 Bộ Cảng Endpoint Xử Lý Lõi Token

**1. Xin Xuống Mã SMS Viết Mã Token (OTP Generator) (`POST /api/v1/auth/otp/send`)**

- Data cõng nạp Server JSON: `{ "phone": "0912345678" }`
- Backend hồi trả phiên hoạt động OTP (Thường cho đếm ngược chạy 300s sống):
`{ "otp_session_id": "uuid-fce3-4s5t...", "expired_in": 300 }`
*(DEV-NOTE: Cấu hình lúc thiết kế System Dev-Enviroment mã OTP thô (Raw) có in đùng vào Log Output của terminal trên máy Local).*

**2. Góp Đơn Chốt Khai Khẩn Tài Khoản Bảng User Mới (`POST /api/v1/auth/register`)**

- Yêu cầu Submit: `{ "phone": "099090...", "full_name": "Phan Ho", "password": "passcode", "otp_code": "098909", "otp_session_id": "uuid-fce3..." }`
- Thu Về Mã Khóa JWT Cấu Trúc Đủ (Access Token và Refresh Storage): Trả lại mã role ban đầu đóng vào User là nhãn Khách hàng phổ thông (`customer`).

**3. Khớp Kênh Truyển Vào Của Thao Tác Vào (Login Trực Diện)**
Đi kèm gọi `POST /api/v1/auth/login/password` đính Mật Khẩu ngầm mã hóa, Hoặc Gọi `POST /api/v1/auth/login/otp`. Cả 2 đều sinh lại bộ cấp JWT giống y Đăng kí Auth Register cấp nạp lại vào máy.

**4. Dịch Vụ Cấp Làm Trẻ Tuổi Token Hết Thời Hiệu Lực Sinh (Xoay Vòng Refresh) (`POST /api/v1/auth/refresh`)**
Access Token JWT đã bay hơi do hết ngưỡng tối đa chạy ngầm cấp 15p. Front App gửi cầu cứ lên API chứa Payload Refresh có tuổi thọ 30 ngày: `{ "refresh_token": "abc..." }`. Backend đổi mã VIP mới toanh hoàn lại.

**5. Luồng Hủy Diệt Phiên Session Kết Thúc Đóng Hành Trình Cửa Sổ Thông Báo (`POST /api/v1/auth/logout`)**
Viết truy vấn phá sập Refresh ghi trong Database khóa đường vào bằng cách trả `{ "success": true }`.

### 3.3 Hướng Dẫn Tích Hợp Frontend Lõi Client Đầu Điểm (Next.js App Router Setup)

**Giải Pháp Nắm Quản Trị Cấp Context Root Tổng Khởi (Global AuthContext)**
App chặn dứt không cho chĩa lệnh ngó Token cục bộ lụn vụn ở code Page rời. Sử dụng `useAuth()` Global Hook Provider cho bao phủ rễ.

- Gọi thông tin định danh toàn cục mảng Auth: `const { user, isAuthenticated, login, logout } = useAuth();`

**Hành Vi Khởi Nghiệp Trạng Thái Đăng Ký và Kiểm Tra Token**
Nhồi data Form Formik thẳng qua hàm API lõi: `await register({...})` - Trả kết qua hoàn mãn.
Bộ API tự bọc Token đút nhét trong mảng Cookies kín mít an toàn rồi cho trang tự đẩy đi Home nhanh lẹ thông qua Route React `router.replace('/')` . Không xài lệnh trỏ mốc quay lui `router.push('/...')` .

**Xây Cổng Bảo Vệ Ngay Mép Nextjs Middleware Security (Edge Route Protection)**
File khóa van an ninh đễ tại góc rễ Tree là File Lõi Middleware (`middleware.ts`).

- Trục xuất khách trôi lơ lứng dỏm, cưỡng chế Redirect đi sang `/login` dứt khoát nếu có tham vọng vào mảng riêng `/admin` hay `/profile` bằng thanh Location.
- Móc đọc nhanh tệp Cookies của trình duyệt tại không gian Next JS Edge Server Runtime nhằm trả API cho Client xịn tuyệt cú xử lý bẫy chống gián đoạn chớp nháy Layout Shifts FOUC.

### 3.4 Sơ Đồ Thiết Kế Điện Tử An Ninh Đường Nhập Xuất (Security Core Flow Architecture)

```
┌────────────────┐      ┌────────────────┐      ┌────────────────┐      ┌────────────────┐
│  Form Đăng Ký  │ ──►  │ Gửi SMS Cấp Mã │ ──►  │ Xác Minh Mã OTP│ ──►  │ Lưu vào Database│
└────────────────┘      └────────────────┘      └────────────────┘      └────────────────┘
                          (Test Log Xem)          (Kèm Mật Khẩu)          (Role Cơ Sở Mới)
                                                                                  │
┌────────────────┐      ┌────────────────┐      ┌────────────────┐                ▼
│ Form Đăng Nhập │ ──►  │ Xác Minh  Pass │ ──►  │ Trả Phiên Token│ ◄──────────────┘
└────────────────┘      └────────────────┘      └────────────────┘
```

**Tính Năng Phòng Vệ Hệ Thống Không Kẽ Hở Rò Rỉ**

1. **Mã Hóa Mật Khẩu Kiên Cố Hashing BCrypt**: Gây rập che giấu toàn tập các chuỗi Pass gốc của nền CSDL Server.
2. **Kẹp Liên Minh Token Đôi (JWT Multi-layered)**: Vé vé đi đường ngắn 15p Access nhét Cache, vé khôi phục hỏa tốc bằng Refresh ẩn 30 ngày hạn kỳ.
3. **Rate Limiting DDOS Anti-Spam (Luật Bảo Tiền):** Khoảng đạn bắn Timeout OTP là 5 phút kẹt sống cứng ngắt. Siết chặt ổ xoay max 5 sai vòng gõ hỏng số (Khóa Cấm Limit API đặng tốn ngân sách API Call SMS).
4. **Vòng Rào CORS (Cross Origin Requests Firewall)**: Backend bảo mật không chia sẻ giao dịch Request Data ngoại lai trừ khi domain đăng ký trùng mảng URL localhost chuẩn đét quy định của Frontend.

### 3.5 Cấu Hình Môi Trường Cục Bộ Phục Vụ Máy Local và Kiểm Tra Bắt Lỗi

**Thiết Định Thông Số File Gốc `.env` cho BE (Cấu hình Server)**

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/sandichvu
JWT_ACCESS_SECRET=chuoi_mat_ma_so_huu_chong_hack_1
JWT_REFRESH_SECRET=chuoi_mat_ma_so_huu_chong_hack_2
OTP_LENGTH=6
OTP_TTL_SECONDS=300
OTP_MAX_ATTEMPTS=5
CORS_ORIGINS=http://localhost:3000
```

*Lưu vực Môi trường Thiết Định URL Dành Cho Màn App Front (`.env.local`): `NEXT_PUBLIC_API_URL=http://localhost:8000`*

**Tìm Soạn Vết Lỗi & Bắt Lỗi Lớn Kẹt Trong Luồng Test (Troubleshooting Fix)**

- **API Rút Chặn Thông Báo "Invalid OTP"**: Kẹt vì OTP nhảy hạn đếm hết 5 phút sống của nó. Số vòng gọi nhập sai OTP 5 phát. Copy & Lấy mã Check Verify Sai nhầm ở Terminal Debug của Backend.
- **Dội Đứt Vì Sai Tài Khoản "Invalid credentials"**: Rò rỉ sự cố ấn mảng phím caps-lock ghi hình chữ sai, thiếu số di động tài khoản khi truy cập mật mã Đăng Nhập.
- **Số Bị Giam Hiện Mảng Báo Trùng Lặp "Phone already registered"**: Account của Số Viễn thông đó đã khởi cắm gốc DB rồi. Nhảy tọt qua Form Đăng nhập thay vì Cố ấn Submit Form Formik Đăng Ký cho Nhanh gọn.

---
*Kết Thúc Bộ Tài Liệu Quy Chiếu Phát Triển Nền Tảng Trọng Tâm*
