import json
import httpx
from app.core.config import get_settings

class AIService:
    @staticmethod
    async def parse_search_prompt(prompt: str) -> dict:
        """
        Bóc tách từ khóa dịch vụ và địa điểm từ prompt của khách hàng.
        Sử dụng AI local (vd: Ollama) để trích xuất thông tin có cấu trúc.
        """
        settings = get_settings()
        
        # Hướng dẫn AI cách bóc tách dữ liệu
        system_hint = (
            "Bạn là trợ lý ảo hỗ trợ tìm kiếm dịch vụ thợ. "
            "Hãy trích xuất 'keyword' (dịch vụ cần tìm) và 'location' (địa phương/thành phố) từ câu lệnh của người dùng. "
            "Trả về duy nhất một đối tượng JSON có dạng: {'keyword': 'từ khóa dịch vụ', 'location': 'tên thành phố hoặc Hà Nội/Sài Gòn...'}. "
            "Nếu không thấy địa điểm, để location là null. "
            "Lưu ý: Chỉ trả về JSON, không giải thích."
        )
        
        try:
            headers = {}
            if settings.local_ai_api_key:
                headers["Authorization"] = f"Bearer {settings.local_ai_api_key}"
                
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Gửi yêu cầu tới Ollama hoặc API AI khác của bạn
                response = await client.post(
                    settings.local_ai_url,
                    json={
                        "model": settings.local_ai_model,
                        "prompt": f"{system_hint}\n\nCâu lệnh người dùng: '{prompt}'",
                        "stream": False,
                        "format": "json"
                    },
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Phản hồi từ Ollama nằm trong trường 'response'
                    ai_response_text = data.get("response", "{}")
                    try:
                        # Parse JSON từ chuỗi kết quả của AI
                        return json.loads(ai_response_text)
                    except (json.JSONDecodeError, TypeError):
                        # Nếu AI không trả về JSON hợp lệ, coi cả câu prompt là keyword
                        return {"keyword": prompt, "location": None}
                
        except Exception as e:
            # Trường hợp AI không phản hồi (chưa bật local AI hoặc lỗi mạng)
            # Log lỗi và trả về dữ liệu thô để hệ thống tìm kiếm thông thường vẫn chạy được
            print(f"--- [AI Service Warning] ---: {str(e)}")
            
        return {"keyword": prompt, "location": None}
