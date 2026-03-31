'use client';

import { use, useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import { fetchAPI } from '@/lib/api';
import { notFound } from 'next/navigation';
import { ChevronRight, Calendar, User, ArrowRight, LayoutGrid, Sparkles, Loader2, Info } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'motion/react';

interface CategoryData {
  type: 'industry' | 'service';
  data: any;
  parent?: any;
}

export default function CategoryPage({ params }: { params: Promise<{ slug: string }> }) {
  const resolvedParams = use(params);
  const [category, setCategory] = useState<CategoryData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function loadCategory() {
      try {
        setIsLoading(true);
        const result = await fetchAPI<CategoryData>(`/api/v1/customer/categories/${resolvedParams.slug}`);
        if (result) {
          setCategory(result);
        } else {
          setError(true);
        }
      } catch (err) {
        console.error('Error loading category:', err);
        setError(true);
      } finally {
        setIsLoading(false);
      }
    }
    loadCategory();
  }, [resolvedParams.slug]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#fbfbfd]">
        <Loader2 className="animate-spin text-primary" size={48} />
      </div>
    );
  }

  if (error || !category) {
    notFound();
  }

  const { data, type, parent } = category;
  const title = data.name;
  const description = data.description || `Khám phá các dịch vụ và thông tin hữu ích về ${title}.`;
  
  // Use a fallback image if icon_url is missing
  const heroImage = data.icon_url || (type === 'service' && parent?.icon_url ? parent.icon_url : '/hero_banner.png');

  // Generate some mock articles based on the real title (Posts will be integrated later)
  const mockArticles = [
    {
      id: 1,
      title: `Hướng dẫn chọn dịch vụ ${title} uy tín và chuyên nghiệp`,
      excerpt: `Khám phá các tiêu chí quan trọng khi lựa chọn dịch vụ ${title.toLowerCase()} để đảm bảo chất lượng và an toàn tuyệt đối cho bạn và gia đình.`,
      image: '/hero_banner.png',
      date: '18 Tháng 3, 2026',
      author: 'Chuyên gia Sàn Dịch Vụ',
      category: title
    },
    {
      id: 2,
      title: `Bảng giá chuẩn cho dịch vụ ${title} năm 2026`,
      excerpt: `Cập nhật chi tiết bảng giá mới nhất thị trường cho các gói dịch vụ thuộc nhóm ${title.toLowerCase()}. Minh bạch, rõ ràng và không phát sinh chi phí.`,
      image: heroImage,
      date: '15 Tháng 3, 2026',
      author: 'Ban Biên Tập',
      category: title
    },
    {
      id: 3,
      title: `Kinh nghiệm cần biết trước khi đặt ${title}`,
      excerpt: `Tổng hợp những lưu ý quan trọng và kinh nghiệm thực tế từ hàng ngàn khách hàng đã sử dụng dịch vụ ${title.toLowerCase()} trên hệ thống của chúng tôi.`,
      image: '/hero_banner.png',
      date: '10 Tháng 3, 2026',
      author: 'CSKH',
      category: title
    },
  ];

  return (
    <main className="min-h-screen bg-[#fbfbfd]">
      <section className="relative pt-32 pb-20 bg-slate-900 text-white overflow-hidden">
        <div className="absolute inset-0 bg-primary/10" />
        <div className="absolute inset-0 bg-[url('/hero_banner.png')] opacity-20 bg-cover bg-center" />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/80 to-transparent" />
        
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="relative max-w-[1740px] mx-auto px-4 md:px-8 z-10"
        >
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.8 }}
            className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-6"
          >
            <Link href="/" className="hover:text-white transition-colors flex items-center gap-1.5">
              <LayoutGrid size={16} /> Trang chủ
            </Link>
            <ChevronRight size={14} />
            <span className="text-primary-light">Danh mục</span>
            <ChevronRight size={14} />
            {type === 'service' && parent && (
              <>
                <Link href={`/danh-muc/${parent.slug}`} className="hover:text-white transition-all truncate max-w-[150px]">
                  {parent.name}
                </Link>
                <ChevronRight size={14} />
              </>
            )}
            <span className="text-white truncate max-w-[200px] md:max-w-none font-bold italic">{title}</span>
          </motion.div>
          
          <motion.h1 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1, duration: 1, ease: [0.16, 1, 0.3, 1] }}
            className="text-4xl md:text-5xl lg:text-6xl font-black mb-6 tracking-tight leading-tight max-w-5xl uppercase"
          >
            {title}
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.8 }}
            className="text-xl text-slate-300 max-w-2xl font-medium leading-relaxed"
          >
            {description}
          </motion.p>
        </motion.div>
      </section>

      <section className="py-20">
        <div className="max-w-[1740px] mx-auto px-4 md:px-8">
          <div className="flex flex-col lg:flex-row gap-12">
            
            <div className="flex-1">
              <div className="flex items-center justify-between mb-10 pb-6 border-b border-slate-200">
                <h2 className="text-2xl font-bold text-slate-900 uppercase">Tin tức & Hướng dẫn</h2>
                <span className="text-sm font-medium text-slate-500 bg-slate-100 px-3 py-1 rounded-full">{mockArticles.length} bài viết</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {mockArticles.map((article, index) => (
                  <motion.article 
                    key={article.id} 
                    initial={{ opacity: 0, y: 40 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, margin: "-50px" }}
                    transition={{ duration: 0.7, delay: index * 0.1, ease: [0.16, 1, 0.3, 1] }}
                    className="group bg-white rounded-3xl overflow-hidden border border-slate-100 shadow-sm hover:shadow-xl hover:shadow-primary/5 transition-all duration-300 flex flex-col"
                  >
                    <div className="relative aspect-[16/10] overflow-hidden bg-slate-100">
                      <Image 
                        src={article.image || '/hero_banner.png'} 
                        alt={article.title}
                        fill
                        className="object-cover group-hover:scale-105 transition-transform duration-700 ease-out"
                      />
                    </div>
                    
                    <div className="p-8 flex-1 flex flex-col">
                      <div className="flex items-center gap-4 text-xs font-medium text-slate-500 mb-4">
                        <div className="flex items-center gap-1.5"><Calendar size={14} /> {article.date}</div>
                        <div className="flex items-center gap-1.5"><User size={14} /> {article.author}</div>
                      </div>
                      <h3 className="text-xl font-bold text-slate-900 mb-3 group-hover:text-primary transition-colors line-clamp-2 leading-snug">
                        {article.title}
                      </h3>
                      <p className="text-slate-600 mb-6 line-clamp-3 leading-relaxed flex-1 text-[15px]">
                        {article.excerpt}
                      </p>
                      <Link href="#" className="inline-flex items-center gap-2 text-sm font-bold text-primary group/link mt-auto w-fit">
                        Chi tiết <ArrowRight size={16} className="group-hover/link:translate-x-1 transition-transform" />
                      </Link>
                    </div>
                  </motion.article>
                ))}
              </div>
            </div>

            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              className="w-full lg:w-[400px] shrink-0 space-y-8"
            >
              <div className="bg-white rounded-3xl p-8 border border-slate-100 shadow-sm">
                <h3 className="text-lg font-bold text-slate-900 mb-6 uppercase tracking-tight">
                  {type === 'service' ? 'Ngành cùng Trụ cột' : 'Các Ngành nghề'}
                </h3>
                <div className="flex flex-col gap-3">
                  {type === 'industry' ? (
                    data.service_categories?.map((s: any, idx: number) => (
                      <Link 
                        key={idx} 
                        href={`/danh-muc/${s.slug}`}
                        className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-50 text-slate-600 hover:text-slate-900 font-medium transition-all"
                      >
                        <span className="text-sm truncate mr-4">{s.name}</span>
                        <ChevronRight size={16} className="opacity-40" />
                      </Link>
                    ))
                  ) : (
                    parent?.service_categories?.map((s: any, idx: number) => {
                      const isCurrent = s.slug === resolvedParams.slug;
                      return (
                        <Link 
                          key={idx} 
                          href={`/danh-muc/${s.slug}`}
                          className={`flex items-center justify-between p-3 rounded-xl transition-all ${isCurrent ? 'bg-primary/10 text-primary font-bold' : 'hover:bg-slate-50 text-slate-600 hover:text-slate-900 font-medium'}`}
                        >
                          <span className="text-sm truncate mr-4">{s.name}</span>
                          <ChevronRight size={16} className={isCurrent ? 'opacity-100' : 'opacity-40'} />
                        </Link>
                      );
                    })
                  )}
                </div>
              </div>

              <div className="relative bg-slate-900 rounded-3xl p-8 overflow-hidden text-white flex flex-col items-start min-h-[300px] justify-end group">
                <div className="absolute inset-0 bg-primary/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="absolute top-0 right-0 -mr-8 -mt-8 size-40 bg-primary/30 blur-3xl rounded-full" />
                <div className="relative z-10">
                  <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-md px-3 py-1.5 rounded-full text-xs font-bold mb-4 uppercase tracking-wider">
                    <Sparkles size={14} className="text-primary-light" /> Dịch vụ chuyên nghiệp
                  </div>
                  <h3 className="text-2xl font-black mb-3 leading-tight">Yêu cầu tư vấn dịch vụ {title}</h3>
                  <button className="bg-white text-slate-900 px-6 py-2.5 rounded-full text-sm font-bold hover:bg-primary hover:text-white transition-all w-full">Gửi yêu cầu</button>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>
    </main>
  );
}
