'use client';

import { use } from 'react';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import { notFound } from 'next/navigation';
import { ChevronRight, Calendar, User, ArrowLeft, ArrowRight, Share2, Facebook, Twitter, Linkedin, LayoutGrid } from 'lucide-react';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'motion/react';

const mockArticles = [
  {
    slug: 'he-sinh-thai-san-dich-vu-chinh-thuc-phu-song-toan-quoc',
    category: 'Tin tức',
    title: 'Hệ sinh thái Sàn Dịch Vụ chính thức phủ sóng toàn quốc',
    description: 'Chúng tôi tự hào mở rộng mạng lưới rất nhiều ngành nghề dịch vụ đến mọi miền tổ quốc, nâng tầm chất lượng sống người Việt.',
    content: `
      <p>Với sứ mệnh mang lại sự tiện nghi và chất lượng dịch vụ tốt nhất cho người dân Việt Nam, Sàn Dịch Vụ chính thức công bố việc mở rộng hoạt động trên toàn quốc. Động thái này đánh dấu một bước tiến quan trọng trong chiến lược phát triển của chúng tôi, nhằm kết nối nhanh chóng và hiệu quả giữa người dùng và các nhà cung cấp dịch vụ chuyên nghiệp.</p>
      
      <h2>Những lợi ích cốt lõi</h2>
      <ul>
        <li><strong>Đa dạng dịch vụ:</strong> Từ vận tải, xây dựng, điện máy đến y tế và giáo dục, khách hàng có thể tìm thấy mọi dịch vụ cần thiết chỉ với vài thao tác đơn giản.</li>
        <li><strong>Đội ngũ chuyên nghiệp:</strong> Các đối tác của Sàn Dịch Vụ đều được tuyển chọn kỹ lưỡng, đảm bảo chuyên môn và thái độ phục vụ chuyên nghiệp nhất.</li>
        <li><strong>Minh bạch chi phí:</strong> Mức giá được hiển thị rõ ràng, giúp khách hàng dễ dàng so sánh và lựa chọn dịch vụ phù hợp với ngân sách của mình.</li>
      </ul>

      <p>Sự mở rộng này không chỉ mang lại lợi ích cho người tiêu dùng mà còn tạo ra hàng ngàn cơ hội việc làm cho các đối tác, thợ tự do và doanh nghiệp nhỏ lẻ trên khắp cả nước. Chúng tôi cam kết sẽ tiếp tục nâng cao chất lượng nền tảng, áp dụng công nghệ tiên tiến nhất để tối ưu hóa trải nghiệm người dùng.</p>

      <blockquote>"Sàn Dịch Vụ không chỉ là một ứng dụng, mà là một hệ sinh thái đồng hành cùng mọi gia đình Việt trong cuộc sống hàng ngày." - Đại diện Sàn Dịch Vụ chia sẻ.</blockquote>
    `,
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBPsPSlnS35PI-XKZib3mcGm9qSTcEyr2h3rGd5h6TSFbO72E9rZeGMqFdZvLJrTCQy345Lqfs0wObZE-h2xbiyvzJzGzKVqzYDVoqU2rsuGG6H6MD1AYczMwwz4a7vGTJmlwVp9xFmHkV6lzMRb5b_RIr3AHfPwp3yygj1lqmN3kGa24R9FCugQ22qrd2b7SYadg6jKdTpBV_S0D46le-1dPgP_L0ZzGctvFra65z9UUb7VyyE6nw4JLUkiq_10-VJfuG6A73eIAqw',
    date: '18 Tháng 3, 2026',
    author: 'Ban Quản Trị Hệ Thống'
  },
  {
    slug: 'sieu-uu-dai-50-trai-nghiem-dich-vu-ve-sinh-va-y-te',
    category: 'Khuyến mãi',
    title: 'Siêu ưu đãi 50%: Trải nghiệm dịch vụ vệ sinh và y tế',
    description: 'Duy nhất trong tháng này, giảm ngay 50% cho các gói dịch vụ vệ sinh công nghiệp và xét nghiệm tại nhà.',
    content: `
      <p>Để tri ân khách hàng đã đồng hành cùng Sàn Dịch Vụ trong thời gian qua, chúng tôi mang đến chương trình siêu khuyến mãi giảm giá lên đến 50% cho các dịch vụ vệ sinh và y tế thiết yếu. Đây là cơ hội tuyệt vời để bạn chăm sóc không gian sống và sức khỏe của bản thân cũng như gia đình với mức chi phí vô cùng tiết kiệm.</p>
      
      <h2>Chi tiết chương trình</h2>
      <p>Chương trình áp dụng cho các hạng mục sau:</p>
      <ul>
        <li>Vệ sinh công nghiệp và vệ sinh nhà cửa trọn gói sau xây dựng.</li>
        <li>Giặt sofa, thảm, nệm tại nhà bằng công nghệ hơi nước nóng diệt khuẩn.</li>
        <li>Gói khám sức khỏe và xét nghiệm máu cơ bản tại nhà.</li>
        <li>Các dịch vụ điều dưỡng và chăm sóc người bệnh cơ bản.</li>
      </ul>

      <p><em>Lưu ý: Chương trình chỉ diễn ra từ ngày 18/03/2026 đến hết ngày 31/03/2026. Số lượng mã giảm giá có hạn, vì vậy hãy nhanh tay đặt lịch ngay hôm nay!</em></p>
    `,
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAfn09_dSHT7LgbhPCfmkyDgLHwDxPkhEqzECkOXA5iOKjlbWcri5jWGvVvZ-Ij1c-UdIt9JUpts063225q80rbjLHYs_lR1nLduMJPtZi33WeRM34K4eZUo7-vFPJo07cQiLe5cQo6L355ESNCNolsZ8gcpz9bS2kGXMO09tfcfAC4Z-FPvW7bM1aLyQHZYcOZ3dVrThC5EKM-kkL2evXx9SoiUvioUz5j8un14yVDNS52RZDNsNrNfXOF2Mh6DGzk0OFo6I4S-FOs',
    date: '15 Tháng 3, 2026',
    author: 'Phòng Marketing'
  },
  {
    slug: 'hanh-trinh-ket-noi-vi-mot-cuoc-song-tien-nghi-hon',
    category: 'Cộng đồng',
    title: 'Hành trình kết nối: Vì một cuộc sống tiện nghi hơn',
    description: 'Chia sẻ từ các đối tác chuyên nghiệp đã đồng hành cùng Sàn Dịch Vụ trong chặng đường vừa qua.',
    content: `
      <p>Mỗi dịch vụ được hoàn thành trên hệ thống không chỉ là một giao dịch, mà là một sự kết nối giữa con người với con người. Sàn Dịch Vụ tự hào mang hàng ngàn đối tác tận tâm đến với những khách hàng đang thực sự cần họ.</p>
      
      <p>Trong chuyên mục này, chúng tôi muốn chia sẻ những câu chuyện truyền cảm hứng từ các anh chị thợ điện nước, cô giúp việc, anh tài xế... những người ngày đêm miệt mài đóng góp vào sự vận hành trơn tru của xã hội.</p>

      <h2>Câu chuyện nổi bật</h2>
      <p>Anh Nguyễn Văn Hùng - Kỹ thuật viên sửa chữa điện lạnh chia sẻ: <em>"Từ ngày tham gia Sàn Dịch Vụ, lượng khách hàng của tôi ổn định hơn hẳn. Tôi không còn phải lo lắng về việc tìm kiếm khách hàng mỗi ngày, mà có thể tập trung nâng cao tay nghề và phục vụ khách hàng tốt nhất."</em></p>
      <p>Chị Trần Thị Tám - Đối tác giúp việc gia đình: <em>"Cảm ơn Sàn Dịch Vụ đã tạo ra một môi trường làm việc an toàn, thu nhập tốt cho những người lao động tự do như chúng tôi."</em></p>
    `,
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDH0lgR5F7gW_rrBmiRpx518xygO1odn2ep9QJ-Hezk-y4ZMOnmqsOq7dZbUZene_FmGrvlTpNX_eYorasQ_q96WB0Nvqxy-K8BWIT5GIwZrvkaWpPGZqUkPcVLk3k9bkRUr1iM4c6DHi6fBBEU2qBnriWH1y5h_ZJCwggFsNwzCNpHtVCm1wQI1rpSvNeJ9jaa4lcGoWItsPCeKkDSi8wGADEvMBlkQ39qhaD3_2u6-UyzQqUbPP7bBBN49jqhcrqTcOUDVgBgHtkI',
    date: '10 Tháng 3, 2026',
    author: 'Ban Tin Tức'
  },
  {
    slug: 'nang-cap-ai-ho-tro-dat-lich-hen-tuc-thi-24-7',
    category: 'Công nghệ',
    title: 'Nâng cấp AI hỗ trợ đặt lịch hẹn tức thì 24/7',
    description: 'Trải nghiệm hệ thống đặt lịch thông minh mới, tự động kết nối đối tác gần nhất chỉ trong 30 giây.',
    content: `
      <p>Tin vui cho toàn bộ người dùng và đối tác của Sàn Dịch Vụ: Hệ thống lõi của nền tảng vừa được tích hợp thành công trí tuệ nhân tạo (AI) phiên bản mới nhất nhằm tối ưu hóa quá trình điều phối dịch vụ.</p>
      
      <h2>Những cải tiến đáng giá</h2>
      <ul>
        <li><strong>Tốc độ xử lý siêu tốc:</strong> Chuyển đổi yêu cầu từ text/voice sang dữ liệu chuẩn hóa, phân loại và tìm kiếm đối tác phù hợp trong vòng chưa đầy 30 giây.</li>
        <li><strong>Khả năng đáp ứng 24/7:</strong> Bất kể ngày đêm hay cuối tuần, AI Agent luôn sẵn sàng tiếp nhận, lên lịch và phản hồi khách hàng ngay lập tức.</li>
        <li><strong>Tối ưu hóa hành trình:</strong> Thuật toán AI giúp tự động tính toán quãng đường ngắn nhất và tình trạng giao thông thực tế để phân công đối tác có vị trí gần nhất, giảm thiểu thời gian chờ đợi của khách hàng.</li>
      </ul>

      <p>Với bản cập nhật này, chúng tôi tin chắc rằng rào cản về thời gian và khoảng cách địa lý sẽ bị phá vỡ, mang đến sự tiện nghi tuyệt đối cho cuộc sống hiện đại của mọi người.</p>
    `,
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBW3haVec5QFqxgRcHRrtO42MFgFxK85-13Pv_XrLFRRUCPZpu6QniGqYNhPZeE6_g7T5dsRso3_MCV0re8deNW4Qv4_HnkDVOYVyOvDLaKedsTAeNenVci0DFWoUauRzsziNQozgP2DYOr3Bv0WZ-1pTUb5kDZDoKh_n-gp8QARGfH-JDZVPwyuOP9uuN88dLJL46qqX7VTz4b5aVs_17aDyJi9nnZaPbwJnDYJNR6oG6S71KG9NRs6SttTrGXawuzSTSWzVwUZ2Rp',
    date: '05 Tháng 3, 2026',
    author: 'Phối Hợp Kỹ Thuật'
  }
];

export default function ArticlePage({ params }: { params: Promise<{ slug: string }> }) {
  const resolvedParams = use(params);
  const article = mockArticles.find(a => a.slug === resolvedParams.slug);

  if (!article) {
    notFound();
  }

  // Get related articles (excluding the current one)
  const relatedArticles = mockArticles.filter(a => a.slug !== article.slug).slice(0, 3);

  return (
    <main className="min-h-screen bg-[#fbfbfd]">

      {/* Article Header (Hero) */}
      <section className="relative pt-32 pb-20 bg-slate-900 text-white overflow-hidden">
        <div className="absolute inset-0 bg-primary/10" />
        <div
          className="absolute inset-0 opacity-20 bg-cover bg-center"
          style={{ backgroundImage: `url(${article.image})` }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/80 to-transparent" />

        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="relative max-w-[900px] mx-auto px-4 md:px-8 z-10 text-center"
        >
          {/* Breadcrumb */}
          <div className="flex items-center justify-center gap-2 text-sm font-medium text-slate-300 mb-8 flex-wrap">
            <Link href="/" className="hover:text-white transition-colors flex items-center gap-1.5">
              <LayoutGrid size={16} /> Trang chủ
            </Link>
            <ChevronRight size={14} />
            <Link href="#" className="hover:text-white transition-colors">
              Tin tức & Sự kiện
            </Link>
            <ChevronRight size={14} />
            <span className="text-primary-light">{article.category}</span>
          </div>

          <div className="inline-flex items-center justify-center px-4 py-1.5 bg-primary/20 text-primary-light border border-primary/30 rounded-full text-xs font-bold uppercase tracking-wider mb-6">
            {article.category}
          </div>

          <h1 className="text-3xl md:text-5xl font-black mb-6 tracking-tight leading-tight md:leading-[1.15]">
            {article.title}
          </h1>

          <div className="flex items-center justify-center gap-6 text-sm font-medium text-slate-300">
            <div className="flex items-center gap-2">
              <Calendar size={16} className="text-primary/70" />
              {article.date}
            </div>
            <div className="w-1.5 h-1.5 rounded-full bg-slate-700" />
            <div className="flex items-center gap-2">
              <User size={16} className="text-primary/70" />
              {article.author}
            </div>
          </div>
        </motion.div>
      </section>

      {/* Article Content & Sidebar */}
      <section className="py-20">
        <div className="max-w-[1740px] mx-auto px-4 md:px-8">
          <div className="max-w-[1100px] mx-auto flex flex-col lg:flex-row gap-16 relative">

            {/* Left Sidebar (Share Buttons - Sticky) */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="lg:w-[60px] shrink-0 hidden lg:block"
            >
              <div className="sticky top-24 flex flex-col gap-4">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-widest rotate-180" style={{ writingMode: 'vertical-rl' }}>
                  Chia sẻ
                </span>
                <div className="w-px h-8 bg-slate-200 mx-auto my-2" />
                <button className="size-10 rounded-full border border-slate-200 bg-white text-slate-500 hover:text-blue-600 hover:border-blue-600 flex items-center justify-center transition-colors shadow-sm">
                  <Facebook size={18} />
                </button>
                <button className="size-10 rounded-full border border-slate-200 bg-white text-slate-500 hover:text-sky-500 hover:border-sky-500 flex items-center justify-center transition-colors shadow-sm">
                  <Twitter size={18} />
                </button>
                <button className="size-10 rounded-full border border-slate-200 bg-white text-slate-500 hover:text-blue-700 hover:border-blue-700 flex items-center justify-center transition-colors shadow-sm">
                  <Linkedin size={18} />
                </button>
                <button className="size-10 rounded-full border border-slate-200 bg-white text-slate-500 hover:text-slate-900 hover:border-slate-900 flex items-center justify-center transition-colors shadow-sm mt-2">
                  <Share2 size={18} />
                </button>
              </div>
            </motion.div>

            {/* Main Content Area */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
              className="flex-1 min-w-0 bg-white rounded-[40px] p-8 md:p-12 lg:p-16 border border-slate-100 shadow-sm -mt-20 relative z-20"
            >
              {/* Description Excerpt */}
              <p className="text-xl md:text-2xl text-slate-600 font-medium leading-relaxed mb-12 pb-12 border-b border-slate-100">
                {article.description}
              </p>

              {/* Prose Content (HTML rendering) */}
              <div
                className="prose prose-lg md:prose-xl prose-slate max-w-none
                           prose-headings:font-black prose-headings:text-slate-900 prose-headings:tracking-tight
                           prose-h2:mt-12 prose-h2:mb-6 prose-h2:text-3xl
                           prose-h3:text-2xl
                           prose-p:text-slate-600 prose-p:leading-relaxed prose-p:mb-6
                           prose-a:text-primary hover:prose-a:text-primary-dark
                           prose-strong:text-slate-800
                           prose-ul:list-disc prose-ul:pl-6 prose-ul:text-slate-600 prose-li:mb-3
                           prose-blockquote:border-l-4 prose-blockquote:border-primary prose-blockquote:bg-primary/5 prose-blockquote:p-6 prose-blockquote:rounded-r-2xl prose-blockquote:text-slate-700 prose-blockquote:not-italic prose-blockquote:font-medium"
                dangerouslySetInnerHTML={{ __html: article.content }}
              />

              {/* Mobile Share Buttons */}
              <div className="mt-16 pt-8 border-t border-slate-100 flex items-center justify-between lg:hidden">
                <span className="font-bold text-slate-900">Chia sẻ bài viết:</span>
                <div className="flex gap-3">
                  <button className="size-10 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center">
                    <Facebook size={18} />
                  </button>
                  <button className="size-10 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center">
                    <Twitter size={18} />
                  </button>
                  <button className="size-10 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center">
                    <Share2 size={18} />
                  </button>
                </div>
              </div>
            </motion.div>

          </div>
        </div>
      </section>

      {/* Related Articles Slider/Grid */}
      <section className="py-20 bg-slate-50 border-t border-slate-200">
        <div className="max-w-[1740px] mx-auto px-4 md:px-8">
          <div className="max-w-[1100px] mx-auto">
            <div className="flex items-center justify-between mb-12">
              <h3 className="text-3xl font-black text-slate-900 tracking-tight">Bài viết liên quan</h3>
              <Link href="#" className="hidden md:flex items-center gap-2 text-sm font-bold text-primary group">
                Xem tất cả
                <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {relatedArticles.map((rel, index) => (
                <motion.div
                  key={rel.slug}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-50px" }}
                  transition={{ duration: 0.6, delay: index * 0.1, ease: [0.16, 1, 0.3, 1] }}
                  className="h-full"
                >
                  <Link href={`/bai-viet/${rel.slug}`} className="group flex flex-col bg-white rounded-3xl overflow-hidden border border-slate-100 shadow-sm hover:shadow-xl hover:shadow-primary/5 transition-all duration-300 h-full">
                    <div className="relative aspect-[16/10] overflow-hidden">
                      <Image
                        src={rel.image}
                        alt={rel.title}
                        fill
                        className="object-cover group-hover:scale-110 transition-transform duration-700 ease-out"
                      />
                      <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-md px-3 py-1 rounded-full text-[10px] font-bold text-slate-900 uppercase">
                        {rel.category}
                      </div>
                    </div>
                    <div className="p-6 flex-1 flex flex-col">
                      <div className="flex items-center gap-2 text-xs font-medium text-slate-500 mb-3">
                        <Calendar size={12} />
                        {rel.date}
                      </div>
                      <h4 className="text-lg font-bold text-slate-900 mb-3 group-hover:text-primary transition-colors line-clamp-2 leading-snug">
                        {rel.title}
                      </h4>
                      <div className="mt-auto flex items-center gap-1.5 text-xs font-bold text-primary opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all">
                        Đọc tiếp <ChevronRight size={14} />
                      </div>
                    </div>
                  </Link>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
