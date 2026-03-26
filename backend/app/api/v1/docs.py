import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.openapi.utils import get_openapi


def get_swagger_html():
    """Load custom swagger HTML file"""
    html_path = Path(__file__).parent / "swagger_custom.html"
    return html_path.read_text(encoding="utf-8")


def customize_swagger_docs(app: FastAPI) -> None:
    """
    Custom hóa Swagger UI docs để:
    1. Thành lập OAuth2 với tokenUrl cho endpoint riêng của Swagger
    2. Hiển thị hướng dẫn nhập token
    3. Giải thích client_id/client_secret không cần thiết cho Password Grant
    """
    original_get_openapi = app.openapi
    
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = original_get_openapi()
        
        # Update title and description
        openapi_schema["info"] = {
            **openapi_schema.get("info", {}),
            "title": "Sàn Dịch Vụ API - With Phone Authentication",
            "description": """
## Hướng dẫn Authentication

### 1. Đăng nhập qua OAuth2 Form (Khuyến nghị)

**Cách 1:** Click 🔒 ở API cần thử → Authorize → nhập phone/password → Authorize
- Username = Số điện thoại (ví dụ: 0912345678)
- Password = Mật khẩu
- Client ID/Secret = Để trống

**Cách 2:** Login qua API trực tiếp
- POST `/api/v1/auth/login/password` với `{ "phone": "...", "password": "..." }`

### 2. Manual Token Input

Ở đầu trang /docs có ô "Manual Token Input". Copy access_token từ response → Paste → Set Token.

### 3. Client ID / Secret không cần thiết

OAuth2 Password Grant Flow (password flow) **KHÔNG yêu cầu client_id/client_secret**.

### 4. Token Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {...},
  "roles": ["admin", "customer"]
}
```

### 5. Refresh Token

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
            """,
            "version": "0.1.0"
        }
        
        # Update security schemes - Point to the dedicated swagger login endpoint
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        if "securitySchemes" not in openapi_schema["components"]:
            openapi_schema["components"]["securitySchemes"] = {}
        
        openapi_schema["components"]["securitySchemes"]["OAuth2PasswordBearer"] = {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/swagger/login",  # Use dedicated endpoint for swagger UI
                    "scheme": "bearer",
                    "in": "header",
                    "scopes": {}
                }
            },
            "description": "Đăng nhập bằng số điện thoại và mật khẩu. Username field = Phone number. Client ID/Secret không cần thiết."
        }
        
        app.openapi_schema = openapi_schema
        return openapi_schema
    
    app.openapi = custom_openapi
