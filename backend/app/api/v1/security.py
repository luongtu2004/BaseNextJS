from fastapi.security import OAuth2PasswordBearer

# Tạo OAuth2PasswordBearer với tokenUrl đúng
# FastAPI auto tạo OAuth2 authentication trong Swagger UI
# Khi bạn click vào ổ khóa -> chọn "Authorize" -> nhập phone, password
# Sau khi click "Authorize", Swagger sẽ tự động gọi /api/v1/auth/login/password
# và lưu token vào browser session

# Để customize login form (phone thay vì username), ta cần add custom endpoint
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login/password",
    description="Đăng nhập bằng số điện thoại và mật khẩu"
)