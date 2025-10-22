import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Navbar } from '@/components/Navbar';
import { JoinForm } from '@/components/JoinForm';
import { ConfirmationPopup } from '@/components/ConfirmationPopup';
import ConfirmationBanner from '@/components/ConfirmationBanner';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useLanguage } from '@/contexts/LanguageContext';
import { useTranslation } from '@/lib/i18n';
import { CheckCircle, TrendingUp, Zap } from 'lucide-react';
import heroBg from '@/assets/hero-bg.jpg';

export default function Landing() {
  const { language } = useLanguage();
  const { t } = useTranslation(language);
  const [showConfirmation, setShowConfirmation] = useState(false);

  const scrollToForm = () => {
    document.getElementById('join-form')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-background">
      <ConfirmationBanner />
      <Navbar />

      {/* Hero Section */}
      <section 
        className="relative pt-32 pb-20 px-4 bg-gradient-hero overflow-hidden"
        style={{
          backgroundImage: `linear-gradient(135deg, rgba(136, 183, 146, 0.9) 0%, rgba(245, 241, 236, 0.95) 50%), url(${heroBg})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      >
        <div className="container mx-auto max-w-6xl text-center relative z-10">
          <h1 className="text-5xl md:text-7xl font-bold mb-6 text-foreground animate-fade-in">
            {t.hero.tagline}
          </h1>
          <p className="text-xl md:text-2xl mb-8 text-foreground/80 max-w-3xl mx-auto animate-slide-up">
            {t.hero.subtitle}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-scale-in">
            <Button 
              variant="hero" 
              size="lg"
              onClick={scrollToForm}
            >
              {t.hero.cta}
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 bg-background">
        <div className="container mx-auto max-w-6xl">
          <h2 className="text-4xl font-bold text-center mb-12 text-foreground">
            {t.features.title}
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <Card className="shadow-soft hover:shadow-elevated transition-all animate-slide-up">
              <CardContent className="pt-6">
                <div className="h-12 w-12 rounded-full bg-sage-light flex items-center justify-center mb-4">
                  <CheckCircle className="h-6 w-6 text-sage-dark" />
                </div>
                <h3 className="text-xl font-semibold mb-2">{t.features.transparent.title}</h3>
                <p className="text-muted-foreground">{t.features.transparent.description}</p>
              </CardContent>
            </Card>

            <Card className="shadow-soft hover:shadow-elevated transition-all animate-slide-up" style={{ animationDelay: '0.1s' }}>
              <CardContent className="pt-6">
                <div className="h-12 w-12 rounded-full bg-gold-light flex items-center justify-center mb-4">
                  <TrendingUp className="h-6 w-6 text-accent" />
                </div>
                <h3 className="text-xl font-semibold mb-2">{t.features.accurate.title}</h3>
                <p className="text-muted-foreground">{t.features.accurate.description}</p>
              </CardContent>
            </Card>

            <Card className="shadow-soft hover:shadow-elevated transition-all animate-slide-up" style={{ animationDelay: '0.2s' }}>
              <CardContent className="pt-6">
                <div className="h-12 w-12 rounded-full bg-sage-light flex items-center justify-center mb-4">
                  <Zap className="h-6 w-6 text-sage-dark" />
                </div>
                <h3 className="text-xl font-semibold mb-2">{t.features.automated.title}</h3>
                <p className="text-muted-foreground">{t.features.automated.description}</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 px-4 bg-gradient-card">
        <div className="container mx-auto max-w-6xl">
          <h2 className="text-4xl font-bold text-center mb-12 text-foreground">
            {t.howItWorks.title}
          </h2>
          <div className="grid md:grid-cols-3 gap-12">
            {[
              { num: '01', ...t.howItWorks.step1 },
              { num: '02', ...t.howItWorks.step2 },
              { num: '03', ...t.howItWorks.step3 },
            ].map((step, index) => (
              <div key={index} className="text-center animate-fade-in" style={{ animationDelay: `${index * 0.1}s` }}>
                <div className="text-5xl font-bold text-sage mb-4">{step.num}</div>
                <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
                <p className="text-muted-foreground">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Join Form Section */}
      <section id="join-form" className="py-20 px-4 bg-background">
        <div className="container mx-auto">
          <JoinForm onSuccess={() => setShowConfirmation(true)} />
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-border bg-gradient-card">
        <div className="container mx-auto max-w-6xl">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-center md:text-left">
              <p className="text-lg font-semibold text-foreground">{t.footer.tagline}</p>
              <p className="text-sm text-muted-foreground">{t.footer.rights}</p>
            </div>
            <Link to="/login">
              <Button variant="ghost">{t.nav.login}</Button>
            </Link>
          </div>
        </div>
      </footer>

      <ConfirmationPopup 
        isOpen={showConfirmation} 
        onClose={() => setShowConfirmation(false)} 
      />
    </div>
  );
}
