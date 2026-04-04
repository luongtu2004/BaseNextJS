import json
import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


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
        
        logger.info("Parsing search prompt - model=%s prompt='%s'", settings.local_ai_model, prompt[:80])

        try:
            headers = {}
            if settings.local_ai_api_key:
                headers["Authorization"] = f"Bearer {settings.local_ai_api_key}"

            async with httpx.AsyncClient(timeout=10.0) as client:
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
                    ai_response_text = data.get("response", "{}")
                    try:
                        parsed = json.loads(ai_response_text)
                        logger.info("AI parse success - keyword='%s' location='%s'", parsed.get("keyword"), parsed.get("location"))
                        return parsed
                    except (json.JSONDecodeError, TypeError) as parse_err:
                        logger.warning("AI returned non-JSON response - raw='%s' error=%s", ai_response_text[:200], parse_err)
                        return {"keyword": prompt, "location": None}
                else:
                    logger.error("AI request failed - status=%d body=%s", response.status_code, response.text[:200])

        except Exception as exc:
            logger.warning("AI service unavailable - %s: %s", type(exc).__name__, exc)

        return {"keyword": prompt, "location": None}

    @staticmethod
    async def verify_identity(files: dict[str, str]) -> dict:
        """
        Giả lập quy trình xác minh danh tính qua AI.
        Trong thực tế, method này sẽ gọi tới các bên thứ 3 (VNPT, FPT, AI local...)
        để thực hiện OCR, Face Match và Liveness check.
        
        files: {'id_front': 'url', 'id_back': 'url', 'selfie': 'url'}
        """
        # Giả lập kết quả trả về từ AI Vendor
        # Trong môi trường dev, ta sẽ trả về kết quả 'success' để test flow.
        logger.info("AI Identity Verification starting - files=%s", list(files.keys()))
        
        # MOCK: Giả định ảnh đẹp, OCR đọc tốt, Face match cao.
        return {
            "quality": {
                "status": "success",
                "is_blur": False,
                "is_glare": False,
                "is_cropped": False,
                "is_wrong_side": False,
                "doc_type": "cccd"
            },
            "ocr": {
                "status": "success",
                "confidence": 95.5,
                "data": {
                    "full_name": "NGUYEN VAN A",
                    "id_number": "012345678901",
                    "dob": "1990-01-01",
                    "gender": 0,
                    "address": "Hà Nội, Việt Nam",
                    "issue_date": "2020-01-01",
                    "expiry_date": "2035-01-01"
                }
            },
            "face_match": {
                "status": "success",
                "score": 92.0
            },
            "liveness": {
                "status": "success",
                "score": 90.0
            }
        }
