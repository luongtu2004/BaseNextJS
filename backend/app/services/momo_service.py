import copy
import hashlib
import hmac


class MomoService:
    @staticmethod
    def validate_callback(payload: dict, secret_key: str) -> bool:
        """Kiểm tra tính hợp lệ của callback từ MoMo.

        Tạo chữ ký từ data theo chuẩn MoMo (HMAC SHA256).

        Args:
            payload: Dict chứa các trường MoMo gửi về (partnerCode, orderId, ...).
            secret_key: Khóa bí mật (MOMO_SECRET_KEY).

        Returns:
            True nếu signature khớp, False nếu không.
        """
        request_signature = payload.get("signature")
        if not request_signature:
            return False

        # Các trường dữ liệu MoMo yêu cầu trong rawHash (theo thứ tự alphabet)
        # accessKey, amount, extraData, message, orderId, orderInfo,
        # orderType, partnerCode, payType, requestId, responseTime,
        # resultCode, transId
        fields = [
            "accessKey", "amount", "extraData", "message", "orderId",
            "orderInfo", "orderType", "partnerCode", "payType", "requestId",
            "responseTime", "resultCode", "transId"
        ]

        raw_data = "&".join([f"{k}={payload.get(k, '')}" for k in fields])
        
        computed_signature = hmac.new(
            secret_key.encode("utf-8"),
            raw_data.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(computed_signature, request_signature)
