# Hướng Dẫn Đăng Nhập & Đăng Ký - Sàn Dịch Vụ 24/7

## Tổng Quan

Hệ thống đã được tích hợp đầy đủ chức năng đăng nhập và đăng ký với các phương thức:

1. **Đăng ký**: Số điện thoại + OTP + Mật khẩu
2. **Đăng nhập**: Số điện thoại + Mật khẩu
3. **Đăng nhập bằng OTP**: Số điện thoại + OTP (không cần mật khẩu)

## API Endpoints

### 1. Gửi OTP (`POST /api/v1/auth/otp/send`)

```json
{
  "phone": "0912345678"
}
```

**Response:**

```json
{
  "otp_session_id": "uuid-string",
  "expired_in": 300
}
```

**Lưu ý:** Trong giai đoạn development, OTP được in ra console backend để dễ dàng test.

### 2. Đăng ký (`POST /api/v1/auth/register`)

```json
{
  "phone": "0912345678",
  "full_name": "Nguyễn Văn A",
  "password": "password123",
  "otp_code": "123456",
  "otp_session_id": "uuid-string"
}
```

**Response:**

```json
{
  "access_token": "jwt-token",
  "refresh_token": "jwt-refresh-token",
  "user": {
    "id": "uuid",
    "phone": "0912345678",
    "full_name": "Nguyễn Văn A",
    "phone_verified": true,
    "status": "active"
  },
  "roles": ["customer"]
}
```

### 3. Đăng nhập bằng mật khẩu (`POST /api/v1/auth/login/password`)

```json
{
  "phone": "0912345678",
  "password": "password123"
}
```

**Response:** Giống đăng ký

### 4. Đăng nhập bằng OTP (`POST /api/v1/auth/login/otp`)

```json
{
  "phone": "0912345678",
  "otp_code": "123456",
  "otp_session_id": "uuid-string"
}
```

### 5. Làm mới token (`POST /api/v1/auth/refresh`)

```json
{
  "refresh_token": "jwt-refresh-token"
}
```

**Response:**

```json
{
  "access_token": "new-jwt-token"
}
```

### 6. Đăng xuất (`POST /api/v1/auth/logout`)

```json
{
  "refresh_token": "jwt-refresh-token"
}
```

**Response:**

```json
{
  "success": true
}
```

### 7. Lấy thông tin user hiện tại (`GET /api/v1/common/me`)

**Headers:**

```
Authorization: Bearer {access_token}
```

**Response:**

```json
{
  "id": "uuid",
  "phone": "0912345678",
  "full_name": "Nguyễn Văn A",
  "gender": "male",
  "dob": "1990-01-01",
  "avatar_url": "url-to-avatar",
  "roles": ["customer"],
  "profile": {
    "bio": "",
    "preferred_language": "vi",
    "timezone": "Asia/Ho_Chi_Minh"
  }
}
```

## Frontend Usage (Next.js App Router)

### Sử dụng AuthContext (Global Session)

Thay vì thao tác trực tiếp với token, toàn bộ ứng dụng sử dụng `AuthContext` để quản lý trạng thái đăng nhập.

```tsx
'use client';
import { useAuth } from '@/contexts/AuthContext';

export default function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuth();

  if (!isAuthenticated) return <p>Vui lòng đăng nhập</p>;

  return (
    <div>
      <p>Xin chào, {user?.full_name}</p>
      <button onClick={logout}>Đăng xuất</button>
    </div>
  );
}
```

### Đăng ký

```tsx
const { login } = useAuth(); // Import từ useAuth

// Bước 1: Gửi yêu cầu đăng ký (API trực tiếp, bỏ qua bước gửi OTP ở giao diện hiện tại)
const { data, error } = await register({
  phone,
  full_name,
  password,
  otp_code: "", // Có thể bypass ở chế độ dev nếu API cho phép
  otp_session_id: ""
});

// Bước 2: Cập nhật state Global (login function sẽ lo việc gọi /api/v1/common/me)
if (data?.access_token) {
  // api.ts sẽ tự động lưu token vào js-cookie vì HTTP response
  await login(data.access_token);
  router.replace('/'); // Dùng replace thay vì push để chống back-loop
}
```

### Đăng nhập bằng mật khẩu

```tsx
const { login } = useAuth();

const res = await loginApi(phone, password);

if (res.access_token) {
  await login(res.access_token); // Update AuthContext state
  // Middleware sẽ tự động direct về /admin hoặc / tùy thuộc vào roles ở lần tải trang sau.
  // Hoặc ta có thể check Role để replace route luôn.
  router.replace('/'); 
}
```

### Đăng xuất

Hàm `logout` trong `useAuth` tự động gọi API revoke token `/auth/logout`, xóa cookies và cập nhật UI.

```typescript
const { logout } = useAuth();

<button onClick={() => {
    logout();
    router.replace('/login');
}}>Đăng Xuất</button>
```

### Bảo vệ Route (Middleware)

Hệ thống Next.js được đặt một file `middleware.ts` ở thư mục gốc để bảo vệ route tại Server Side.

- Rediect user khách khỏi `/admin`, `/profile` về `/login`.
- Đẩy user đã Login khỏi `/login`, `/register` về `/`.
- Đọc token bằng API `cookies()` ngay tại rìa chạy Edge.

## Cấu hình Environment

### Backend (`.env`)

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/sandichvu
JWT_ACCESS_SECRET=your-secret-key-here
JWT_REFRESH_SECRET=your-refresh-secret-key-here
OTP_LENGTH=6
OTP_TTL_SECONDS=300
OTP_MAX_ATTEMPTS=5
CORS_ORIGINS=http://localhost:3000
```

### Frontend (`.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Flow Diagram

```
┌─────────────┐
│  Register   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Send OTP    │ → OTP in console (dev)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Verify OTP  │ + Full name + Password
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Create User │ + Assign "customer" role
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Return JWT  │
└─────────────┘

┌─────────────┐
│    Login    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Verify Pass │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Return JWT  │
└─────────────┘
```

## Security Features

1. **Password Hashing**: BCrypt
2. **JWT Tokens**: Access token (15 min) + Refresh token (30 days)
3. **OTP Verification**: 6 digits, 5 min expiry, 5 max attempts
4. **Rate Limiting**: Configurable per endpoint
5. **CORS Protection**: Configured origins only
6. **Token Revocation**: Refresh token can be revoked on logout

## Testing

### Test Register Flow

1. Chạy backend: `cd backend && uvicorn app.main:app --reload`
2. Chạy frontend: `npm run dev`
3. Truy cập: `http://localhost:3000/register`
4. Nhập số điện thoại → Check console backend để lấy OTP
5. Nhập OTP + thông tin → Hoàn tất đăng ký

### Test Login Flow

1. Truy cập: `http://localhost:3000/login`
2. Nhập số điện thoại + mật khẩu đã đăng ký
3. Click "Đăng nhập ngay"
4. Redirect về trang chủ hoặc admin panel (nếu có role admin)

## Troubleshooting

### Lỗi "Invalid OTP"

- Kiểm tra OTP đã hết hạn chưa (5 phút)
- Kiểm tra số lần thử quá 5 lần
- Check console backend để lấy OTP chính xác

### Lỗi "Invalid credentials"

- Kiểm tra số điện thoại và mật khẩu
- Đảm bảo user đã đăng ký trước đó

### Lỗi "Phone already registered"

- Số điện thoại đã tồn tại trong hệ thống
- Sử dụng số điện thoại khác hoặc đăng nhập

## Next Steps

1. **Email/SMS OTP**: Tích hợp SendGrid/Twilio để gửi OTP thật
2. **Forgot Password**: Thêm tính năng quên mật khẩu
3. **Social Login**: Google, Facebook login
4. **2FA**: Two-factor authentication
5. **Session Management**: Quản lý session đa thiết bị
