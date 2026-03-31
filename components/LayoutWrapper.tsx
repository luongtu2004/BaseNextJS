'use client';

import { usePathname } from 'next/navigation';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import SmoothScroll from '@/components/SmoothScroll';

export default function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAdmin = pathname?.startsWith('/admin');
  const isAuth = pathname?.startsWith('/login') || pathname?.startsWith('/register');

  if (isAdmin) {
    return (
      <main className="min-h-screen bg-background-light">
        {children}
      </main>
    );
  }

  return (
    <>
      <Navbar />
      <SmoothScroll>
        {children}
      </SmoothScroll>
      {!isAuth && <Footer />}
    </>
  );
}
