-- SQL SEED SCRIPT FOR POSTS (TIN TỨC & KHUYẾN MÃI)
-- Project: Sandichvu CMS
-- Autor: Antigravity
-- 1. TẠO DANH MỤC BÀI VIẾT (POST CATEGORIES)
-- Sử dụng UUID cố định để dễ dàng tham chiếu
INSERT INTO post_categories (id, code, name, slug, is_active)
VALUES (
        'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380c01',
        'tintuc',
        'Tin tức',
        'tin-tuc',
        true
    ),
    (
        'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380c02',
        'khuyenmai',
        'Khuyến mãi',
        'khuyen-mai',
        true
    ),
    (
        'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380c03',
        'congdong',
        'Cộng đồng',
        'cong-dong',
        true
    ),
    (
        'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380c04',
        'congnghe',
        'Công nghệ',
        'cong-nghe',
        true
    ) ON CONFLICT (code) DO
UPDATE
SET name = EXCLUDED.name,
    slug = EXCLUDED.slug;
-- 2. TẠO BÀI VIẾT (POSTS)
INSERT INTO posts (
        category_id,
        title,
        slug,
        summary,
        content,
        cover_image_url,
        status,
        visibility,
        post_type,
        is_featured
    )
VALUES -- Bài viết 1: Tin tức
    (
        'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380c01',
        'Hệ sinh thái Sàn Dịch Vụ chính thức phủ sóng toàn quốc',
        'he-sinh-thai-san-dich-vu-chinh-thuc-phu-song-toan-quoc',
        'Chúng tôi tự hào mở rộng mạng lưới rất nhiều ngành nghề dịch vụ đến mọi miền tổ quốc, nâng tầm chất lượng sống người Việt.',
        'Nội dung chi tiết về việc mở rộng hệ sinh thái Sàn Dịch Vụ toàn quốc...',
        'https://lh3.googleusercontent.com/aida-public/AB6AXuBPsPSlnS35PI-XKZib3mcGm9qSTcEyr2h3rGd5h6TSFbO72E9rZeGMqFdZvLJrTCQy345Lqfs0wObZE-h2xbiyvzJzGzKVqzYDVoqU2rsuGG6H6MD1AYczMwwz4a7vGTJmlwVp9xFmHkV6lzMRb5b_RIr3AHfPwp3yygj1lqmN3kGa24R9FCugQ22qrd2b7SYadg6jKdTpBV_S0D46le-1dPgP_L0ZzGctvFra65z9UUb7VyyE6nw4JLUkiq_10-VJfuG6A73eIAqw',
        'published',
        'public',
        'article',
        true
    ),
    -- Bài viết 2: Khuyến mãi
    (
        'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380c02',
        'Siêu ưu đãi 50%: Trải nghiệm dịch vụ vệ sinh và y tế',
        'sieu-uu-dai-50-trai-nghiem-dich-vu-ve-sinh-va-y-te',
        'Duy nhất trong tháng này, giảm ngay 50% cho các gói dịch vụ vệ sinh công nghiệp và xét nghiệm tại nhà.',
        'Thông tin chi tiết về chương trình siêu ưu đãi 50%...',
        'https://lh3.googleusercontent.com/aida-public/AB6AXuAfn09_dSHT7LgbhPCfmkyDgLHwDxPkhEqzECkOXA5iOKjlbWcri5jWGvVvZ-Ij1c-UdIt9JUpts063225q80rbjLHYs_lR1nLduMJPtZi33WeRM34K4eZUo7-vFPJo07cQiLe5cQo6L355ESNCNolsZ8gcpz9bS2kGXMO09tfcfAC4Z-FPvW7bM1aLyQHZYcOZ3dVrThC5EKM-kkL2evXx9SoiUvioUz5j8un14yVDNS52RZDNsNrNfXOF2Mh6DGzk0OFo6I4S-FOs',
        'published',
        'public',
        'article',
        false
    ),
    -- Bài viết 3: Cộng đồng
    (
        'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380c03',
        'Hành trình kết nối: Vì một cuộc sống tiện nghi hơn',
        'hanh-trinh-ket-noi-vi-mot-cuoc-song-tien-nghi-hon',
        'Chia sẻ từ các đối tác chuyên nghiệp đã đồng hành cùng Sàn Dịch Vụ trong chặng đường vừa qua.',
        'Câu chuyện về hành trình kết nối cộng đồng của Sàn Dịch Vụ...',
        'https://lh3.googleusercontent.com/aida-public/AB6AXuDH0lgR5F7gW_rrBmiRpx518xygO1odn2ep9QJ-Hezk-y4ZMOnmqsOq7dZbUZene_FmGrvlTpNX_eYorasQ_q96WB0Nvqxy-K8BWIT5GIwZrvkaWpPGZqUkPcVLk3k9bkRUr1iM4c6DHi6fBBEU2qBnriWH1y5h_ZJCwggFsNwzCNpHtVCm1wQI1rpSvNeJ9jaa4lcGoWItsPCeKkDSi8wGADEvMBlkQ39qhaD3_2u6-UyzQqUbPP7bBBN49jqhcrqTcOUDVgBgHtkI',
        'published',
        'public',
        'article',
        false
    ),
    -- Bài viết 4: Công nghệ
    (
        'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380c04',
        'Nâng cấp AI hỗ trợ đặt lịch hẹn tức thì 24/7',
        'nang-cap-ai-ho-tro-dat-lich-hen-tuc-thi-24-7',
        'Trải nghiệm hệ thống đặt lịch thông minh mới, tự động kết nối đối tác gần nhất chỉ trong 30 giây.',
        'Khám phá những tính năng AI mới nhất được cập nhật trên nền tảng Sàn Dịch Vụ...',
        'https://lh3.googleusercontent.com/aida-public/AB6AXuBW3haVec5QFqxgRcHRrtO42MFgFxK85-13Pv_XrLFRRUCPZpu6QniGqYNhPZeE6_g7T5dsRso3_MCV0re8deNW4Qv4_HnkDVOYVyOvDLaKedsTAeNenVci0DFWoUauRzsziNQozgP2DYOr3Bv0WZ-1pTUb5kDZDoKh_n-gp8QARGfH-JDZVPwyuOP9uuN88dLJL46qqX7VTz4b5aVs_17aDyJi9nnZaPbwJnDYJNR6oG6S71KG9NRs6SttTrGXawuzSTSWzVwUZ2Rp',
        'published',
        'public',
        'article',
        false
    ) ON CONFLICT (slug) DO
UPDATE
SET title = EXCLUDED.title,
    summary = EXCLUDED.summary,
    content = EXCLUDED.content,
    cover_image_url = EXCLUDED.cover_image_url,
    status = EXCLUDED.status,
    visibility = EXCLUDED.visibility;
-- 3. KẾT THÚC
SELECT 'Post data successfully applied!' as info;