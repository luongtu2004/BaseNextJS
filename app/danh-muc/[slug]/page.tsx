'use client';

import { use } from 'react';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import { PILLARS } from '@/lib/constants';
import { createSlug } from '@/lib/utils';
import { notFound } from 'next/navigation';
import { ChevronRight, Calendar, User, ArrowRight, LayoutGrid, Sparkles } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'motion/react';

// Find the title matching the slug
type PillarType = { id: string; title: string; description: string; image: string; industries: string[] };
type MatchResult = 
  | { type: 'pillar'; data: PillarType; title: string }
  | { type: 'industry'; data: string; parent: PillarType; title: string };

function findCategoryBySlug(slug: string): MatchResult | null {
  for (const pillar of PILLARS) {
    if (createSlug(pillar.title) === slug) {
      return { type: 'pillar', data: pillar, title: pillar.title };
    }
    for (const ind of pillar.industries) {
      if (createSlug(ind) === slug) {
        return { type: 'industry', data: ind, parent: pillar, title: ind };
      }
    }
  }
  return null;
}

export default function CategoryPage({ params }: { params: Promise<{ slug: string }> }) {
  const resolvedParams = use(params);
  const match = findCategoryBySlug(resolvedParams.slug);

  if (!match) {
    notFound();
  }

  const { title } = match;

  // Generate some mock articles based on the title
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
      image: match.type === 'industry' ? match.parent.image : match.data.image,
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
    {
      id: 4,
      title: `Top 5 đối tác cung cấp ${title} đánh giá cao nhất`,
      excerpt: `Cùng điểm qua danh sách các đơn vị đối tác được khách hàng của Sàn Dịch Vụ đánh giá 5 sao trong tháng vừa qua về chất lượng phục vụ.`,
      image: match.type === 'industry' ? match.parent.image : match.data.image,
      date: '05 Tháng 3, 2026',
      author: 'Đánh giá cộng đồng',
      category: title
    },
  ];

  return (
    <main className="min-h-screen bg-[#fbfbfd]">
      {/* Hero Banner for Category */}
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
            <span className="text-white truncate max-w-[200px] md:max-w-none">{title}</span>
          </motion.div>
          
          <motion.h1 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1, duration: 1, ease: [0.16, 1, 0.3, 1] }}
            className="text-4xl md:text-5xl lg:text-6xl font-black mb-6 tracking-tight leading-tight max-w-4xl uppercase"
          >
            {title}
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.8 }}
            className="text-xl text-slate-300 max-w-2xl font-medium leading-relaxed"
          >
            Khám phá các bài viết, hướng dẫn và thông tin hữu ích nhất về lĩnh vực <span className="text-white font-bold">{title}</span>.
          </motion.p>
        </motion.div>
      </section>

      {/* Content Section */}
      <section className="py-20">
        <div className="max-w-[1740px] mx-auto px-4 md:px-8">
          <div className="flex flex-col lg:flex-row gap-12">
            
            {/* Main Content: Article List */}
            <div className="flex-1">
              <div className="flex items-center justify-between mb-10 pb-6 border-b border-slate-200">
                <h2 className="text-2xl font-bold text-slate-900 uppercase">Bài viết & Tài liệu</h2>
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
                      <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-md px-3 py-1.5 rounded-full text-xs font-bold text-slate-900 uppercase tracking-wide">
                        {article.category}
                      </div>
                    </div>
                    
                    <div className="p-8 flex-1 flex flex-col">
                      <div className="flex items-center gap-4 text-xs font-medium text-slate-500 mb-4">
                        <div className="flex items-center gap-1.5">
                          <Calendar size={14} />
                          {article.date}
                        </div>
                        <div className="flex items-center gap-1.5">
                          <User size={14} />
                          {article.author}
                        </div>
                      </div>
                      
                      <h3 className="text-xl font-bold text-slate-900 mb-3 group-hover:text-primary transition-colors line-clamp-2 leading-snug">
                        {article.title}
                      </h3>
                      
                      <p className="text-slate-600 mb-6 line-clamp-3 leading-relaxed flex-1 text-[15px]">
                        {article.excerpt}
                      </p>
                      
                      <Link href="#" className="inline-flex items-center gap-2 text-sm font-bold text-primary group/link mt-auto w-fit">
                        Đọc tiếp 
                        <ArrowRight size={16} className="group-hover/link:translate-x-1 transition-transform" />
                      </Link>
                    </div>
                  </motion.article>
                ))}
              </div>
              
              {/* Pagination (Mock) */}
              <div className="mt-16 flex justify-center">
                <div className="flex items-center gap-2">
                  <button className="size-10 rounded-full flex items-center justify-center border border-slate-200 text-slate-400 cursor-not-allowed">
                    <ChevronRight size={18} className="rotate-180" />
                  </button>
                  <button className="size-10 rounded-full flex items-center justify-center bg-slate-900 text-white font-medium">1</button>
                  <button className="size-10 rounded-full flex items-center justify-center border border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300 font-medium transition-all">2</button>
                  <button className="size-10 rounded-full flex items-center justify-center border border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300 font-medium transition-all">3</button>
                  <span className="px-2 text-slate-400">...</span>
                  <button className="size-10 rounded-full flex items-center justify-center border border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-all">
                    <ChevronRight size={18} />
                  </button>
                </div>
              </div>
            </div>

            {/* Sidebar */}
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              className="w-full lg:w-[400px] shrink-0 space-y-8"
            >
              {/* Related Categories / Industries */}
              <div className="bg-white rounded-3xl p-8 border border-slate-100 shadow-sm">
                <h3 className="text-lg font-bold text-slate-900 mb-6 uppercase tracking-tight">
                  {match.type === 'industry' ? 'Cùng Thể Loại' : 'Các Ngành Nghề'}
                </h3>
                <div className="flex flex-col gap-3">
                  {match.type === 'industry' ? (
                    // Show other industries in the same pillar
                    match.parent.industries.map((ind, idx) => {
                      const isCurrent = ind === title;
                      return (
                        <Link 
                          key={idx} 
                          href={`/danh-muc/${createSlug(ind)}`}
                          className={`flex items-center justify-between p-3 rounded-xl transition-all ${isCurrent ? 'bg-primary/10 text-primary font-bold' : 'hover:bg-slate-50 text-slate-600 hover:text-slate-900 font-medium'}`}
                        >
                          <span className="text-sm truncate mr-4">{ind}</span>
                          <ChevronRight size={16} className={isCurrent ? 'opacity-100' : 'opacity-40'} />
                        </Link>
                      );
                    })
                  ) : (
                    // Show industries for this pillar
                    match.data.industries.map((ind, idx) => (
                      <Link 
                        key={idx} 
                        href={`/danh-muc/${createSlug(ind)}`}
                        className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-50 text-slate-600 hover:text-slate-900 font-medium transition-all"
                      >
                        <span className="text-sm truncate mr-4">{ind}</span>
                        <ChevronRight size={16} className="opacity-40" />
                      </Link>
                    ))
                  )}
                </div>
              </div>

              {/* Promotional Banner (Mock) */}
              <div className="relative bg-slate-900 rounded-3xl p-8 overflow-hidden text-white flex flex-col items-start min-h-[300px] justify-end group">
                <div className="absolute inset-0 bg-primary/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="absolute top-0 right-0 -mr-8 -mt-8 size-40 bg-primary/30 blur-3xl rounded-full" />
                
                <div className="relative z-10">
                  <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-md px-3 py-1.5 rounded-full text-xs font-bold mb-4 uppercase tracking-wider">
                    <Sparkles size={14} className="text-primary-light" />
                    Ưu đãi hội viên
                  </div>
                  <h3 className="text-2xl font-black mb-3 leading-tight">Đăng ký ngay để nhận tư vấn miễn phí</h3>
                  <p className="text-slate-300 text-sm mb-6 max-w-[250px]">Nhận báo giá chi tiết và các chương trình khuyến mãi độc quyền từ các đối tác.</p>
                  <button className="bg-white text-slate-900 px-6 py-2.5 rounded-full text-sm font-bold hover:bg-primary hover:text-white transition-all w-full">
                    Yêu cầu tư vấn
                  </button>
                </div>
              </div>
            </motion.div>

          </div>
        </div>
      </section>
    </main>
  );
}
