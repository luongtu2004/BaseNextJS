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

  // Delete mockArticles as News isn't meant for the service pillar page

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
              <div className="flex items-center justify-between mb-8 pb-6 border-b border-slate-200">
                <h2 className="text-2xl font-bold text-slate-900 uppercase">Chi tiết Dịch vụ</h2>
              </div>

              <div className="bg-white rounded-3xl p-8 md:p-12 border border-slate-100 shadow-sm leading-relaxed text-slate-700">
                  {data.description ? (
                      <div 
                         className="prose prose-lg md:prose-xl max-w-none prose-p:mb-6 prose-h2:text-2xl prose-h2:font-bold prose-h2:text-slate-900 prose-h2:mb-4 prose-ul:list-disc prose-ul:pl-6 prose-li:mb-2 prose-a:text-primary"
                         dangerouslySetInnerHTML={{ __html: data.description }} 
                      />
                  ) : (
                     <div className="prose prose-lg max-w-none">
                        <p className="text-xl font-medium text-slate-600 mb-8">
                          Dịch vụ <strong>{title}</strong> thuộc hệ sinh thái Sàn Dịch Vụ cam kết mang đến trải nghiệm chất lượng, uy tín và minh bạch nhất cho khách hàng.
                        </p>
                        
                        <h2 className="text-2xl font-bold text-slate-900 mb-4 mt-8">Tại sao nên chọn chúng tôi?</h2>
                        <ul className="list-disc pl-6 mb-8 space-y-3 text-slate-600">
                           <li><strong>Quy trình chuyên nghiệp:</strong> Mọi đối tác đều trải qua quá trình kiểm duyệt khắt khe và đào tạo bài bản để phục vụ khách hàng tốt nhất.</li>
                           <li><strong>Minh bạch giá cả:</strong> Hệ thống tự động tính toán và báo giá công khai trước khi bạn quyết định đặt dịch vụ.</li>
                           <li><strong>Bảo hành tận tâm:</strong> Sẵn sàng hỗ trợ và xử lý khiếu nại nhanh chóng nếu có bất kỳ vấn đề phát sinh.</li>
                        </ul>

                        <h2 className="text-2xl font-bold text-slate-900 mb-4 mt-8">Quy trình thực hiện</h2>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 my-8 not-prose">
                           <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100 hover:border-primary/30 transition-colors">
                              <div className="size-10 bg-primary/10 text-primary rounded-full flex items-center justify-center font-black text-lg mb-4">1</div>
                              <h4 className="font-bold text-slate-900 mb-2">Tiếp nhận</h4>
                              <p className="text-sm text-slate-600">Ghi nhận thông tin yêu cầu của khách hàng qua hệ thống nhánh chóng.</p>
                           </div>
                           <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100 hover:border-primary/30 transition-colors">
                              <div className="size-10 bg-primary/10 text-primary rounded-full flex items-center justify-center font-black text-lg mb-4">2</div>
                              <h4 className="font-bold text-slate-900 mb-2">Thực thi</h4>
                              <p className="text-sm text-slate-600">Đối tác chuyên nghiệp tiến hành dịch vụ theo tiêu chuẩn an toàn.</p>
                           </div>
                           <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100 hover:border-primary/30 transition-colors">
                              <div className="size-10 bg-primary/10 text-primary rounded-full flex items-center justify-center font-black text-lg mb-4">3</div>
                              <h4 className="font-bold text-slate-900 mb-2">Nghiệm thu</h4>
                              <p className="text-sm text-slate-600">Khách hàng xác nhận hoàn thành và đánh giá trải nghiệm trực tiếp trên ứng dụng.</p>
                           </div>
                        </div>

                        <div className="bg-blue-50/50 text-blue-800 p-6 rounded-2xl flex gap-4 mt-12 border border-blue-100">
                           <Info className="shrink-0 mt-1" size={24} />
                           <div>
                             <p className="text-sm mb-1 font-bold">Lưu ý Dành Cho Quản Trị Viên:</p>
                             <p className="text-xs mb-0">Định dạng bạn đang xem là form cấu trúc mẫu (Mock layout). Vui lòng đăng nhập Admin CMS và bổ sung trực tiếp nội dung Mô tả (Bài viết chuẩn SEO, Hình ảnh, Bảng giá) vào dữ liệu của danh mục <strong>{title}</strong> để nó được hiển thị tự động lên đây nhé.</p>
                           </div>
                        </div>
                     </div>
                  )}
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
