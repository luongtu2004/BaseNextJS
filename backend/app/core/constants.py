PILLARS = [
    {
        "id": "transportation",
        "title": "VẬN TẢI & DI CHUYỂN",
        "description": "Ô tô & xe máy với 11 ngành nghề đa dạng.",
        "image": "/pillar_transportation_1773647657871.png",
        "industries": [
            "Taxi (4,7 chỗ)/ Xe hợp đồng / Xe du lịch (4-7-16-29-45 chỗ)",
            "Xe tiện chuyến / Xe ghép / Xe Limousine (4-7-12 chỗ)",
            "Xe khách chạy tuyến cố định (Liên tỉnh)",
            "Xe tải vận chuyển hàng hóa, xe công (từ 0,5 tấn đến 20 tấn)",
            "Xe cẩu, xe nâng, máy xúc",
            "Cứu hộ giao thông (Cẩu kéo ô tô)",
            "Sửa xe ô tô lưu động (Vá lốp, sửa nhanh)",
            "Lái xe ô tô hộ (Bạn uống say - Tôi lái)",
            "Lái xe máy hộ",
            "Lái xe theo ngày, lái xe theo chuyến",
            "Xe ôm công nghệ (Xe máy cá nhân)"
        ]
    },
    {
        "id": "construction_electronics",
        "title": "XÂY DỰNG, NỘI THẤT VÀ KỸ THUẬT",
        "description": "Thi công, sửa chữa nhà cửa và điện máy gia dụng tại nhà.",
        "image": "/pillar_construction_1773647692104.png",
        "industries": [
            "Sửa chữa Điện nước (Xử lý sự cố 24/7)",
            "Thợ Nề / Xây dựng (Xây mới, sửa chữa, phá dỡ)",
            "Sơn bả / Chống thấm",
            "Trần thạch cao (Thi công vách, trần)",
            "Nhôm kính / Cửa cuốn (Lắp đặt, sửa chữa)",
            "Cơ khí / Hàn xì (Hàng rào, cổng sắt)",
            "Thợ Mộc (Sửa chữa lắp đặt đồ gỗ)",
            "Thông tắc cống / Hút bể phốt",
            "Sửa chữa, bảo dưỡng Điều hòa",
            "Sửa chữa, lắp đặt Máy giặt / Máy sấy",
            "Sửa chữa, lắp đặt Tủ lạnh / Tủ đông",
            "Thay lõi Máy lọc nước",
            "Sửa chữa Bếp từ / Bếp ga / Đồ gia dụng",
            "Thợ Khóa (Mở khóa, đánh chìa, khóa thông minh)",
            "Lắp đặt & Sửa chữa Camera / An ninh",
            "Sửa chữa thiết bị văn phòng (Máy tính, máy in)"
        ]
    },
    {
        "id": "housekeeping_beauty",
        "title": "GIÚP VIỆC, CHĂM SÓC & LÀM ĐẸP",
        "description": "Dịch vụ chăm sóc gia đình, vệ sinh và làm đẹp tại nhà.",
        "image": "/pillar_housekeeping_1773647750012.png",
        "industries": [
            "Giúp việc theo giờ / ngày / tháng",
            "Trông giữ trẻ em tại nhà",
            "Chăm sóc người thân tại nhà",
            "Nuôi bệnh tại bệnh viện",
            "Dịch vụ Nấu cỗ tại nhà",
            "Vệ sinh công nghiệp, vệ sinh trọn gói",
            "Vệ sinh theo ngày, theo giờ",
            "Cắt tóc / Làm tóc tại nhà",
            "Làm móng (Nails) tại nhà",
            "Trang điểm (Makeup) tại nhà",
            "Massage trị liệu tại nhà",
            "Chăm sóc da mặt tại nhà"
        ]
    },
    {
        "id": "education",
        "title": "Y TẾ & GIÁO DỤC",
        "description": "Chăm sóc sức khỏe và đào tạo tại nhà.",
        "image": "/pillar_education_medical_1773647770773.png",
        "industries": [
            "Điều dưỡng tại nhà (Tiêm, truyền, vật lý trị liệu)",
            "Lấy mẫu máu xét nghiệm tại nhà",
            "Gia sư văn hóa (Toán, Văn, Anh...)",
            "Gia sư năng khiếu (Đàn, họa, võ, bơi)"
        ]
    },
    {
        "id": "travel",
        "title": "DU LỊCH, KHÁCH SẠN VÀ BẢO HIỂM",
        "description": "Dịch vụ tiện ích du lịch, lưu trú và bảo hiểm trọn gói.",
        "image": "/pillar_transportation_1773647657871.png",
        "industries": [
            "Đặt vé máy bay nội địa / quốc tế",
            "Đặt phòng khách sạn, homestay, resort",
            "Đặt tour ghép / tour riêng theo nhu cầu",
            "Thuê xe tự lái / xe du lịch có tài xế",
            "Đưa đón sân bay 2 chiều",
            "Hỗ trợ visa, hộ chiếu và lịch trình",
            "Hướng dẫn viên du lịch theo điểm đến",
            "Combo du lịch trọn gói (vé + phòng + xe)",
            "Bảo hiểm du lịch",
            "Dịch vụ SIM / eSIM du lịch"
        ]
    }
]


# ─────────────────────────────────────────────────────────────────────
# Phase 8 — Payment & Wallet Constants
# ─────────────────────────────────────────────────────────────────────

# Wallet transaction types (matches CHECK constraint in wallet_transactions)
WALLET_TXN_TYPES = (
    "topup", "payment", "refund", "withdrawal",
    "earning", "commission", "bonus", "penalty", "adjust",
)

# Payment methods (matches CHECK constraint in payment_transactions)
PAYMENT_METHODS = ("cash", "wallet", "vnpay", "momo", "zalopay")

# Promotion types (matches CHECK constraint in promotions)
PROMOTION_TYPES = ("percent", "fixed", "free_trip")

# Wallet negative floor limit (VND) — cho phep vi am khi settlement cash
# Driver can bu bang cashless rides hoac nap vi thu cong
WALLET_NEGATIVE_FLOOR = -500_000


# ─────────────────────────────────────────────────────────────────────
# Phase 9 — Rating, Notifications & Analytics Constants
# ─────────────────────────────────────────────────────────────────────

# Default platform commission rate (heuristic fallback khi chua co commission_configs table)
DEFAULT_COMMISSION_RATE = 0.15

# Valid notification types (used in settings and broadcast)
NOTIFICATION_TYPES = (
    "booking_updates", "review_received", "promotion",
    "admin_broadcast", "system",
)

# Review rating range
REVIEW_RATING_MIN = 1
REVIEW_RATING_MAX = 5
