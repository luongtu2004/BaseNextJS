import hashlib
import hmac
import urllib.parse
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.core.config import get_settings


class VNPAYService:
    """Service tích hợp VNPAY (Sandbox & Production)."""

    @staticmethod
    def generate_payment_url(
        order_id: str,
        amount: float,
        order_desc: str,
        ip_addr: str,
        locale: str = "vn",
    ) -> str:
        """Tạo URL thanh toán hướng người dùng sang cổng VNPAY.

        Args:
            order_id: Mã giao dịch (thường là PaymentTransaction.id).
            amount: Số tiền thanh toán (VND).
            order_desc: Nội dung thanh toán.
            ip_addr: IP của máy khách.
            locale: Ngôn ngữ giao diện (vn/en).

        Returns:
            str: URL redirect sang VNPAY.
        """
        settings = get_settings()
        
        # VNPAY amount format: multiply by 100 (use Decimal to avoid float rounding)
        vnp_amount = int(Decimal(str(amount)) * 100)
        
        # Use timezone 'Asia/Ho_Chi_Minh' for VNPAY timestamps
        tz = ZoneInfo("Asia/Ho_Chi_Minh")
        created_date = datetime.now(tz).strftime("%Y%m%d%H%M%S")
        vnp_expire_date = (datetime.now(tz) + timedelta(minutes=15)).strftime("%Y%m%d%H%M%S")

        input_data = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": settings.vnpay_tmn_code,
            "vnp_Amount": str(vnp_amount),
            "vnp_CurrCode": "VND",
            "vnp_TxnRef": order_id,
            "vnp_OrderInfo": order_desc,
            "vnp_OrderType": "other",
            "vnp_Locale": locale,
            "vnp_ReturnUrl": settings.vnpay_return_url,
            "vnp_IpAddr": ip_addr,
            "vnp_CreateDate": created_date,
            "vnp_ExpireDate": vnp_expire_date,
        }

        # Sắp xếp các tham số theo tên (alphabetical order) để tạo chuỗi dữ liệu ký
        # Filter out empty/None values
        input_data = {k: v for k, v in input_data.items() if v}
        
        # Hash signature
        payment_url = settings.vnpay_payment_url
        hash_secret = settings.vnpay_hash_secret.encode("utf-8")
        
        query_string = urllib.parse.urlencode(sorted(input_data.items()))
        
        # VNPAY requires securely hashing the query_string
        hash_value = hmac.new(hash_secret, query_string.encode("utf-8"), hashlib.sha512).hexdigest()
        
        return f"{payment_url}?{query_string}&vnp_SecureHash={hash_value}"

    @staticmethod
    def validate_callback(query_params: dict) -> bool:
        """Kiểm tra tính hợp lệ của callback IPN từ VNPAY qua Secure Hash.

        Args:
            query_params: Tất cả các tham số query do VNPAY gửi đến.

        Returns:
            bool: True nếu khớp chữ ký, False nếu có thay đổi gian lận.
        """
        settings = get_settings()
        
        # Loại bỏ cấu trúc hash ra khỏi dữ liệu để build signature
        vnp_secure_hash = query_params.get("vnp_SecureHash")
        if not vnp_secure_hash:
            return False

        input_data = {
            k: v for k, v in query_params.items() 
            if k not in ("vnp_SecureHash", "vnp_SecureHashType")
        }
        
        query_string = ""
        seq = 0
        for key, val in sorted(input_data.items()):
            if seq == 1:
                query_string = query_string + "&" + key + "=" + urllib.parse.quote_plus(str(val))
            else:
                seq = 1
                query_string = key + "=" + urllib.parse.quote_plus(str(val))

        hash_secret = settings.vnpay_hash_secret.encode("utf-8")
        hash_value = hmac.new(hash_secret, query_string.encode("utf-8"), hashlib.sha512).hexdigest()

        return hmac.compare_digest(vnp_secure_hash, hash_value)
