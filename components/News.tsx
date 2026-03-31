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
    <section ref={containerRef} className="py-32 bg-white overflow-hidden">
      <div className="max-w-[1740px] mx-auto px-6 md:px-12">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-24 gap-8 border-b border-black/5 pb-10">
          <div className="max-w-xl">
            <span className="text-primary font-black tracking-[0.3em] uppercase text-[12px] mb-4 block opacity-60">
              Cập nhật mới nhất
            </span>
            <h2 className="text-[32px] md:text-[42px] font-black text-primary tracking-[-0.04em] leading-tight uppercase">
              Tin tức & Khuyến mãi
            </h2>
          </div>
          <Link href="#" className="inline-flex items-center gap-3 text-[15px] font-bold text-[#5d4037] group hover:text-primary transition-all pb-1">
            Xem tất cả bản tin
            <div className="size-8 rounded-full bg-black/5 flex items-center justify-center group-hover:bg-primary group-hover:text-white transition-all">
              <ChevronRight size={16} />
            </div>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10">
          {newsItems.map((item, index) => (
            <motion.div
              key={index}
              whileHover={{ y: -12 }}
              className="group relative bg-white rounded-[40px] overflow-hidden shadow-[0_20px_50px_rgba(0,0,0,0.05)] hover:shadow-[0_40px_80px_rgba(0,0,0,0.12)] transition-all duration-700 border border-black/[0.03] flex flex-col h-full"
            >
              {/* Sunken Image Frame Style */}
              <div className="p-4">
                <div className="h-52 relative rounded-[28px] overflow-hidden shadow-[inset_0_2px_12px_rgba(0,0,0,0.1)] bg-slate-50">
                  <Image
                    src={item.image}
                    alt={item.title}
                    fill
                    className="object-cover group-hover:scale-110 transition-transform duration-1000 ease-out"
                  />
                  <div className="absolute inset-0 shadow-[inset_0_0_40px_rgba(0,0,0,0.15)] pointer-events-none" />
                  <div className="absolute top-4 left-4">
                    <span className="px-4 py-1.5 bg-white/60 backdrop-blur-2xl rounded-full text-[10px] font-black text-primary uppercase border border-white/40 shadow-sm">
                      {item.category}
                    </span>
                  </div>
                </div>
              </div>

              <div className="px-8 pb-10 pt-4 flex-1 flex flex-col">
                <h4 className="text-[20px] font-black text-primary mb-4 line-clamp-2 leading-[1.2] tracking-tight group-hover:text-primary/70 transition-colors uppercase">
                  {item.title}
                </h4>
                <p className="text-[15px] text-[#5d4037] font-medium line-clamp-3 leading-relaxed mb-8 opacity-80">
                  {item.description}
                </p>
                <Link href={`/bai-viet/${createSlug(item.title)}`} className="mt-auto flex items-center gap-2 text-[13px] font-black text-primary/40 group-hover:text-primary transition-all">
                  Đọc tiếp
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
