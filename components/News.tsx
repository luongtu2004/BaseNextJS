'use client';

import { ChevronRight } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { createSlug } from '@/lib/utils';
import { motion, useScroll, useTransform } from 'motion/react';
import { useRef } from 'react';

const newsItems = [
  {
    category: 'Tin tức',
    title: 'Hệ sinh thái Sàn Dịch Vụ chính thức phủ sóng toàn quốc',
    description: 'Chúng tôi tự hào mở rộng mạng lưới 45 ngành nghề dịch vụ đến mọi miền tổ quốc, nâng tầm chất lượng sống người Việt.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBPsPSlnS35PI-XKZib3mcGm9qSTcEyr2h3rGd5h6TSFbO72E9rZeGMqFdZvLJrTCQy345Lqfs0wObZE-h2xbiyvzJzGzKVqzYDVoqU2rsuGG6H6MD1AYczMwwz4a7vGTJmlwVp9xFmHkV6lzMRb5b_RIr3AHfPwp3yygj1lqmN3kGa24R9FCugQ22qrd2b7SYadg6jKdTpBV_S0D46le-1dPgP_L0ZzGctvFra65z9UUb7VyyE6nw4JLUkiq_10-VJfuG6A73eIAqw'
  },
  {
    category: 'Khuyến mãi',
    title: 'Siêu ưu đãi 50%: Trải nghiệm dịch vụ vệ sinh và y tế',
    description: 'Duy nhất trong tháng này, giảm ngay 50% cho các gói dịch vụ vệ sinh công nghiệp và xét nghiệm tại nhà.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAfn09_dSHT7LgbhPCfmkyDgLHwDxPkhEqzECkOXA5iOKjlbWcri5jWGvVvZ-Ij1c-UdIt9JUpts063225q80rbjLHYs_lR1nLduMJPtZi33WeRM34K4eZUo7-vFPJo07cQiLe5cQo6L355ESNCNolsZ8gcpz9bS2kGXMO09tfcfAC4Z-FPvW7bM1aLyQHZYcOZ3dVrThC5EKM-kkL2evXx9SoiUvioUz5j8un14yVDNS52RZDNsNrNfXOF2Mh6DGzk0OFo6I4S-FOs'
  },
  {
    category: 'Cộng đồng',
    title: 'Hành trình kết nối: Vì một cuộc sống tiện nghi hơn',
    description: 'Chia sẻ từ các đối tác chuyên nghiệp đã đồng hành cùng Sàn Dịch Vụ trong chặng đường vừa qua.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDH0lgR5F7gW_rrBmiRpx518xygO1odn2ep9QJ-Hezk-y4ZMOnmqsOq7dZbUZene_FmGrvlTpNX_eYorasQ_q96WB0Nvqxy-K8BWIT5GIwZrvkaWpPGZqUkPcVLk3k9bkRUr1iM4c6DHi6fBBEU2qBnriWH1y5h_ZJCwggFsNwzCNpHtVCm1wQI1rpSvNeJ9jaa4lcGoWItsPCeKkDSi8wGADEvMBlkQ39qhaD3_2u6-UyzQqUbPP7bBBN49jqhcrqTcOUDVgBgHtkI'
  },
  {
    category: 'Công nghệ',
    title: 'Nâng cấp AI hỗ trợ đặt lịch hẹn tức thì 24/7',
    description: 'Trải nghiệm hệ thống đặt lịch thông minh mới, tự động kết nối đối tác gần nhất chỉ trong 30 giây.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBW3haVec5QFqxgRcHRrtO42MFgFxK85-13Pv_XrLFRRUCPZpu6QniGqYNhPZeE6_g7T5dsRso3_MCV0re8deNW4Qv4_HnkDVOYVyOvDLaKedsTAeNenVci0DFWoUauRzsziNQozgP2DYOr3Bv0WZ-1pTUb5kDZDoKh_n-gp8QARGfH-JDZVPwyuOP9uuN88dLJL46qqX7VTz4b5aVs_17aDyJi9nnZaPbwJnDYJNR6oG6S71KG9NRs6SttTrGXawuzSTSWzVwUZ2Rp'
  }
];

export default function News() {
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"]
  });

  const scale = useTransform(scrollYProgress, [0, 0.4, 0.6, 1], [0.85, 1, 1, 0.85]);
  const y = useTransform(scrollYProgress, [0, 0.4, 0.6, 1], [120, 0, 0, -120]);
  const opacity = useTransform(scrollYProgress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);

  return (
    <section ref={containerRef} className="py-32 bg-[#fbfbfd] overflow-hidden">
      <div className="max-w-[1740px] mx-auto px-4 md:px-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-20 gap-6">
          <div className="max-w-xl">
            <span className="text-primary font-bold tracking-[0.2em] uppercase text-[12px] mb-4 block">
              Cập nhật mới nhất
            </span>
            <h2 className="text-[40px] md:text-[52px] font-extrabold text-slate-900 tracking-tight leading-tight">
              Tin tức & Khuyến mãi
            </h2>
          </div>
          <Link href="#" className="inline-flex items-center gap-2 text-[15px] font-bold text-slate-900 group hover:text-primary transition-colors">
            Xem tất cả bản tin
            <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {newsItems.map((item, index) => (
            <motion.div
              key={index}
              whileHover={{ y: -10 }}
              className="group relative bg-white rounded-[32px] overflow-hidden apple-card-shadow hover:apple-card-shadow-hover transition-all duration-500 border border-slate-100/50 flex flex-col h-full"
            >
              <div className="h-56 relative overflow-hidden">
                <Image
                  src={item.image}
                  alt={item.title}
                  fill
                  className="object-cover group-hover:scale-110 transition-transform duration-700 ease-out"
                />
                <div className="absolute top-6 left-6">
                  <span className="px-3 py-1 bg-white/70 backdrop-blur-md rounded-full text-[10px] font-extrabold text-slate-900 uppercase border border-white/50">
                    {item.category}
                  </span>
                </div>
              </div>

              <div className="p-8 flex-1 flex flex-col">
                <h4 className="text-[19px] font-extrabold text-slate-900 mb-4 line-clamp-2 leading-tight tracking-tight group-hover:text-primary transition-colors">
                  {item.title}
                </h4>
                <p className="text-[14px] text-slate-500 font-medium line-clamp-3 leading-relaxed mb-6">
                  {item.description}
                </p>
                <Link href={`/bai-viet/${createSlug(item.title)}`} className="mt-auto pt-4 flex items-center gap-1.5 text-[12px] font-bold text-slate-400 group-hover:text-primary transition-colors">
                  Đọc thêm
                  <ChevronRight size={14} className="group-hover:translate-x-1 transition-transform" />
                </Link>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
