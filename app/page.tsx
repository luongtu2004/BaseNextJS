import Navbar from '@/components/Navbar';
import Hero from '@/components/Hero';
import CoreServices from '@/components/CoreServices';
import Impact from '@/components/Impact';
import AppPromotion from '@/components/AppPromotion';
import News from '@/components/News';
import Footer from '@/components/Footer';

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <AppPromotion />
        <CoreServices />
        <Impact />
        <News />
      </main>
      <Footer />
    </>
  );
}
