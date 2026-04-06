import hashlib
import hmac


class ZaloPayService:
    @staticmethod
    def validate_callback(data_str: str, request_mac: str, key2: str) -> bool:
        """Kiểm tra tính hợp lệ của callback từ ZaloPay.

        ZaloPay callback payload có định dạng:
        {
            "data": "...",
            "mac": "..."
        }
        Trong đó mac = HMAC_SHA256(key2, data).

        Args:
            data_str: Chuỗi data nguyên bản từ ZaloPay callback payload.
            request_mac: Chữ ký mac từ payload.
            key2: Khóa bảo mật (ZALOPAY_KEY2).

        Returns:
            True nếu hợp lệ, False nếu không.
        """
        if not data_str or not request_mac or not key2:
            return False

        computed_mac = hmac.new(
            key2.encode("utf-8"),
            data_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(computed_mac, request_mac)
