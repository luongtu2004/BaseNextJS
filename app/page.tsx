import Hero from '@/components/Hero';
import CoreServices from '@/components/CoreServices';
import Impact from '@/components/Impact';
import AppPromotion from '@/components/AppPromotion';
import News from '@/components/News';

export default function Home() {
  return (
    <main>
      <Hero />
      <AppPromotion />
      <CoreServices />
      <Impact />
      <News />
    </main>
  );
}
