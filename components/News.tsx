'use client';

import { useEffect, useState, useRef } from 'react';
import { ChevronRight } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { createSlug } from '@/lib/utils';
import { motion, useScroll, useTransform } from 'motion/react';
import { fetchAPI } from '@/lib/api';

interface NewsItem {
  category: string;
  title: string;
  description: string;
  image: string;
  slug: string;
}

export default function News() {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const containerRef = useRef(null);

  useEffect(() => {
    async function loadNews() {
      try {
        const data = await fetchAPI<any>('/api/v1/common/posts?page_size=4');
        if (data && data.items) {
          const mapped: NewsItem[] = data.items.map((item: any) => ({
            category: 'Tin tức',
            title: item.title,
            description: item.summary || 'Click để xem chi tiết bài viết.',
            image: item.cover_image_url || 'https://images.unsplash.com/photo-1586339949916-3e9457bef6d3?q=80&w=2070&auto=format&fit=crop',
            slug: item.slug
          }));
          setItems(mapped);
        }
      } catch (err) {
        console.error('Failed to load news:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadNews();
  }, []);

  const { scrollYProgress } = useScroll({
// ... (rest of scroll logic)
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
          <Link href="/bai-viet" className="inline-flex items-center gap-3 text-[15px] font-bold text-[#5d4037] group hover:text-primary transition-all pb-1">
            Xem tất cả bản tin
            <div className="size-8 rounded-full bg-black/5 flex items-center justify-center group-hover:bg-primary group-hover:text-white transition-all">
              <ChevronRight size={16} />
            </div>
          </Link>
        </div>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="size-10 border-4 border-black/10 border-t-black rounded-full animate-spin" />
            <p className="text-[11px] font-black uppercase tracking-widest text-black/20">Đang tải bản tin...</p>
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-20 text-[11px] font-black uppercase tracking-widest text-black/20">
            Chưa có bài viết nào được hiển thị.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10">
            {items.map((item, index) => (
              <motion.div
                key={index}
                whileHover={{ y: -12 }}
                className="group relative bg-white rounded-[40px] overflow-hidden shadow-[0_20px_50_rgba(0,0,0,0.05)] hover:shadow-[0_40px_80px_rgba(0,0,0,0.12)] transition-all duration-700 border border-black/[0.03] flex flex-col h-full"
              >
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
                  <Link href={`/bai-viet/${item.slug}`} className="mt-auto flex items-center gap-2 text-[13px] font-black text-primary/40 group-hover:text-primary transition-all">
                    Đọc tiếp
                    <ChevronRight size={14} className="group-hover:translate-x-1 transition-transform" />
                  </Link>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
