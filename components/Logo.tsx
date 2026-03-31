'use client';

import Image from 'next/image';

interface LogoProps {
  className?: string;
  iconSize?: number;
  textSize?: string;
  showText?: boolean;
  showTagline?: boolean;
}

export default function Logo({
  className = '',
  iconSize = 40,
  textSize = 'text-xl',
  showText = true,
  showTagline = false
}: LogoProps) {
  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      <div className="flex items-center gap-3 group">
        <div
          className="relative flex items-center justify-center transition-all duration-500 group-hover:scale-105"
          style={{ width: `${iconSize}px`, height: `${iconSize}px` }}
        >
          <Image
            src="/logo.png"
            alt="Sandichvu.vn Logo"
            fill
            className="object-contain"
            priority
          />
        </div>
        {showText && (
          <span className={`${textSize} font-black tracking-tighter text-[#00523b] uppercase leading-tight`}>
            Sàn Dịch Vụ
          </span>
        )}
      </div>
      {showTagline && (
        <p className="text-[#5d4037] text-[14px] md:text-[16px] max-w-sm font-bold opacity-70 uppercase tracking-tight leading-relaxed">
          Hệ sinh thái đa tiện ích hàng đầu Việt Nam, cung cấp giải pháp toàn diện cho mọi nhu cầu cuộc sống của bạn và gia đình.
        </p>
      )}
    </div>
  );
}
