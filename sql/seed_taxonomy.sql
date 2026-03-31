-- SQL SEED SCRIPT FOR PGADMIN 4 (VER 2.0 - 53 INDUSTRIES)
-- Project: Sandichvu Taxonomy (Dynamic)
-- Autor: Antigravity

-- 1. CẬP NHẬT CẤU TRÚC BẢNG (MẶC ĐỊNH LÀ ĐÃ CÓ NHƯNG CHẠY LẠI CHO CHẮC)
ALTER TABLE industry_categories ADD COLUMN IF NOT EXISTS icon_url VARCHAR(255);
ALTER TABLE industry_categories ADD COLUMN IF NOT EXISTS slug VARCHAR(255) UNIQUE;
ALTER TABLE service_categories ADD COLUMN IF NOT EXISTS icon_url VARCHAR(255);
ALTER TABLE service_categories ADD COLUMN IF NOT EXISTS slug VARCHAR(255);

-- 2. DỮ LIỆU TRỤ CỘT (5 TRỤ CỘT)
INSERT INTO industry_categories (id, code, name, slug, description, icon_url, is_active)
VALUES 
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'vantaidichuyen', 'VẬN TẢI & DI CHUYỂN', 'van-tai-di-chuyen', 'Ô tô & xe máy với 11 ngành nghề đa dạng.', '/pillar_transportation_1773647657871.png', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'xaydungnoithat', 'XÂY DỰNG, NỘI THẤT VÀ KỸ THUẬT', 'xay-dung-noi-that-ky-thuat', 'Thi công, sửa chữa nhà cửa và điện máy gia dụng tại nhà.', '/pillar_construction_1773647692104.png', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'giupvieclamdep', 'GIÚP VIỆC, CHĂM SÓC & LÀM ĐẸP', 'giup-viec-cham-soc-lam-dep', 'Dịch vụ chăm sóc gia đình, vệ sinh và làm đẹp tại nhà.', '/pillar_housekeeping_1773647750012.png', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'ytegioduc', 'Y TẾ & GIÁO DỤC', 'y-te-giao-duc', 'Chăm sóc sức khỏe và đào tạo tại nhà.', '/pillar_education_medical_1773647770773.png', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'dulichbaohiem', 'DU LỊCH, KHÁCH SẠN VÀ BẢO HIỂM', 'du-lich-khach-san-bao-hiem', 'Dịch vụ tiện ích du lịch, lưu trú và bảo hiểm trọn gói.', '/pillar_transportation_1773647657871.png', true)
ON CONFLICT (code) DO UPDATE SET 
    name = EXCLUDED.name,
    slug = EXCLUDED.slug,
    description = EXCLUDED.description,
    icon_url = EXCLUDED.icon_url;

-- 3. ĐẢM BẢO RÀNG BUỘC DUY NHẤT
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_service_slug_per_industry') THEN
        ALTER TABLE service_categories ADD CONSTRAINT uq_service_slug_per_industry UNIQUE (industry_category_id, name);
    END IF;
END $$;

-- 4. DỮ LIỆU NGÀNH NGHỀ CHI TIẾT (53 NGÀNH)
INSERT INTO service_categories (industry_category_id, code, name, slug, description, is_active)
VALUES 
-- VẬN TẢI & DI CHUYỂN (11)
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'taxi_47_cho', 'Taxi (4,7 chỗ)/ Xe hợp đồng / Xe du lịch (4-7-16-29-45 chỗ)', 'taxi-47-cho', 'Dịch vụ vận tải hành khách chuyên nghiệp', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'xe_tien_chuyen', 'Xe tiện chuyến / Xe ghép / Xe Limousine (4-7-12 chỗ)', 'xe-tien-chuyen', 'Dịch vụ xe ghép, limousine cao cấp', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'xe_khach', 'Xe khách chạy tuyến cố định (Liên tỉnh)', 'xe-khach', 'Vận tải hành khách tuyến cố định', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'xe_tai', 'Xe tải vận chuyển hàng hóa, xe công (từ 0,5 tấn đến 20 tấn)', 'xe-tai', 'Vận chuyển hàng hóa đa trọng tải', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'xe_cau_nang', 'Xe cẩu, xe nâng, máy xúc', 'xe-cau-nang', 'Thiết bị công trình và vận chuyển đặc biệt', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'cuu_ho', 'Cứu hộ giao thông (Cẩu kéo ô tô)', 'cuu-ho-giao-thong', 'Hỗ trợ sự cố giao thông 24/7', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'sua_xe_luu_dong', 'Sửa xe ô tô lưu động (Vá lốp, sửa nhanh)', 'sua-xe-luu-dong', 'Sửa chữa ô tô tận nơi', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'lai_xe_ho_o_to', 'Lái xe ô tô hộ (Bạn uống say - Tôi lái)', 'lai-xe-ho-o-to', 'Dịch vụ lái xe hộ an toàn', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'lai_xe_ho_xe_may', 'Lái xe máy hộ', 'lai-xe-ho-xe-may', 'Hỗ trợ di chuyển bằng xe máy', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'lai_xe_theo_ngay', 'Lái xe theo ngày, lái xe theo chuyến', 'lai-xe-theo-ngay', 'Tài xế riêng theo yêu cầu', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'xe_om_cong_nghe', 'Xe ôm công nghệ (Xe máy cá nhân)', 'xe-om-cong-nghe', 'Vận chuyển hành khách bằng xe máy', true),

-- XÂY DỰNG, NỘI THẤT VÀ KỸ THUẬT (16)
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'sua_dien_nuoc', 'Sửa chữa Điện nước (Xử lý sự cố 24/7)', 'sua-dien-nuoc', 'Khắc phục sự cố điện nước gia đình', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'tho_ne', 'Thợ Nề / Xây dựng (Xây mới, sửa chữa, phá dỡ)', 'tho-ne-xay-dung', 'Thi công xây dựng và sửa chữa nề', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'son_ba', 'Sơn bả / Chống thấm', 'son-ba-chong-tham', 'Dịch vụ hoàn thiện nhà cửa', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'tran_thach_cao', 'Trần thạch cao (Thi công vách, trần)', 'tran-thach-cao', 'Thi công nội thất thạch cao', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'nhom_kinh', 'Nhôm kính / Cửa cuốn (Lắp đặt, sửa chữa)', 'nhom-kinh-cua-cuon', 'Cung cấp và lắp đặt cửa các loại', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'co_khi', 'Cơ khí / Hàn xì (Hàng rào, cổng sắt)', 'co-khi-han-xi', 'Gia công cơ khí dân dụng', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'tho_moc', 'Thợ Mộc (Sửa chữa lắp đặt đồ gỗ)', 'tho-moc', 'Sửa chữa và sản xuất đồ gỗ', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'thong_tac', 'Thông tắc cống / Hút bể phốt', 'thong-tac-hut-be-phot', 'Vệ sinh môi trường đô thị', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'sua_dieu_hoa', 'Sửa chữa, bảo dưỡng Điều hòa', 'sua-dieu-hoa', 'Dịch vụ điện lạnh chuyên nghiệp', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'sua_may_giat', 'Sửa chữa, lắp đặt Máy giặt / Máy sấy', 'sua-may-giat', 'Bảo trì thiết bị giặt ủi', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'sua_tu_lanh', 'Sửa chữa, lắp đặt Tủ lạnh / Tủ đông', 'sua-tu-lanh', 'Sửa chữa thiết bị bảo quản thực phẩm', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'thay_loi_loc_nuoc', 'Thay lõi Máy lọc nước', 'thay-loi-loc-nuoc', 'Bảo trì nguồn nước sạch gia đình', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'sua_gia_dung', 'Sửa chữa Bếp từ / Bếp ga / Đồ gia dụng', 'sua-bep-do-gia-dung', 'Sửa chữa đồ dùng nhà bếp', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'tho_khoa', 'Thợ Khóa (Mở khóa, đánh chìa, khóa thông minh)', 'tho-khoa', 'Dịch vụ khóa cửa các loại', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'camera_an_ninh', 'Lắp đặt & Sửa chữa Camera / An ninh', 'camera-an-ninh', 'Hệ thống giám sát và báo động', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12', 'thiet_bi_van_phong', 'Sửa chữa thiết bị văn phòng (Máy tính, máy in)', 'thiet-bi-van-phong', 'Hỗ trợ kỹ thuật văn phòng', true),

-- GIÚP VIỆC, CHĂM SÓC & LÀM ĐẸP (12)
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'giup_viec', 'Giúp việc theo giờ / ngày / tháng', 'giup-viec', 'Dịch vụ vệ sinh nhà cửa', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'trong_tre', 'Trông giữ trẻ em tại nhà', 'trong-tre', 'Chăm sóc trẻ em tận tâm', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'cham_soc_nguoi_than', 'Chăm sóc người thân tại nhà', 'cham-soc-nguoi-than', 'Hỗ trợ sinh hoạt người cao tuổi', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'nuoi_benh', 'Nuôi bệnh tại bệnh viện', 'nuoi-benh', 'Dịch vụ chăm sóc y tế tại viện', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'nau_co', 'Dịch vụ Nấu cỗ tại nhà', 'nau-co-tai-nha', 'Ẩm thực phục vụ sự kiện', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 've_sinh_cong_nghiep', 'Vệ sinh công nghiệp, vệ sinh trọn gói', 've-sinh-cong-nghiep', 'Vệ sinh chuyên sâu cho công trình', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 've_sinh_theo_ngay', 'Vệ sinh theo ngày, theo giờ', 've-sinh-hang-ngay', 'Duy trì sạch sẽ không gian sống', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'cat_toc', 'Cắt tóc / Làm tóc tại nhà', 'cat-toc-lam-toc', 'Dịch vụ làm đẹp tóc tận nơi', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'nails', 'Làm móng (Nails) tại nhà', 'lam-mong-nails', 'Chăm sóc móng chuyên nghiệp', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'makeup', 'Trang điểm (Makeup) tại nhà', 'trang-diem-makeup', 'Trang điểm dự tiệc, sự kiện', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'massage', 'Massage trị liệu tại nhà', 'massage-tri-lieu', 'Thư giãn và hồi phục sức khỏe', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13', 'cham_soc_da', 'Chăm sóc da mặt tại nhà', 'cham_soc_da_mat', 'Dịch vụ spa mini tận nhà', true),

-- Y TẾ & GIÁO DỤC (4)
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'dieu_duong', 'Điều dưỡng tại nhà (Tiêm, truyền, vật lý trị liệu)', 'dieu-duong-tai-nha', 'Chăm sóc y tế gia đình', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'lay_mau_xet_nghiem', 'Lấy mẫu máu xét nghiệm tại nhà', 'lay-mau-xet-nghiem', 'Tiện ích y tế tại nhà', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'gia_su_van_hoa', 'Gia sư văn hóa (Toán, Văn, Anh...)', 'gia-su-van-hoa', 'Bồi dưỡng kiến thức văn hóa', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14', 'gia_su_nang_khieu', 'Gia sư năng khiếu (Đàn, họa, võ, bơi)', 'gia-su-nang-khieu', 'Phát triển năng khiếu nghệ thuật, thể thao', true),

-- DU LỊCH, KHÁCH SẠN VÀ BẢO HIỂM (10)
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 've_may_bay', 'Đặt vé máy bay nội địa / quốc tế', 'dat-ve-may-bay', 'Đại lý vé máy bay uy tín', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'khach_san', 'Đặt phòng khách sạn, homestay, resort', 'dat-phong-khach-san', 'Dịch vụ lưu trú toàn cầu', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'tour_du_lich', 'Đặt tour ghép / tour riêng theo nhu cầu', 'dat-tour-du-lich', 'Tổ chức tour du lịch chuyên nghiệp', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'thue_xe_tu_lai', 'Thuê xe tự lái / xe du lịch có tài xế', 'thue-xe-tu-lai', 'Dịch vụ xe du lịch đa dạng', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'dua_don_san_bay', 'Đưa đón sân bay 2 chiều', 'dua-don-san-bay', 'Vận chuyển sân bay đúng giờ', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'visa_ho_chieu', 'Hỗ trợ visa, hộ chiếu và lịch trình', 'visa-ho-chieu', 'Dịch vụ hồ sơ du lịch nhanh chóng', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'hdv_du_lich', 'Hướng dẫn viên du lịch theo điểm đến', 'hdv-du-lich', 'Đội ngũ HDV nhiệt tình, am hiểu', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'combo_du_lich', 'Combo du lịch trọn gói (vé + phòng + xe)', 'combo-du-lich', 'Tiết kiệm chi phí với combo trọn gói', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'bao_hiem_du_lich', 'Bảo hiểm du lịch', 'bao-hiem-du-lich', 'An tâm trên mọi cung đường', true),
('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15', 'sim_esim_du_lich', 'Dịch vụ SIM / eSIM du lịch', 'sim-esim-du-lich', 'Kết nối internet mọi nơi trên thế giới', true)
ON CONFLICT (industry_category_id, name) DO UPDATE SET
    slug = EXCLUDED.slug,
    description = EXCLUDED.description;

-- 5. KẾT THÚC
SELECT 'Dynamic 53-Industry Taxonomy successfully applied!' as info;
