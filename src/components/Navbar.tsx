import { Link, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/contexts/LanguageContext';
import { useTranslation } from '@/lib/i18n';
import { Globe } from 'lucide-react';
import lumaLogo from '@/assets/luma-logo.png';

export const Navbar = () => {
  const { language, setLanguage } = useLanguage();
  const { t } = useTranslation(language);
  const location = useLocation();

  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'es' : 'en');
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 animate-fade-in">
            <img src={lumaLogo} alt="Luma" className="h-8 w-8" />
            <span className="text-xl font-semibold text-foreground">Luma</span>
          </Link>

          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleLanguage}
              className="gap-2"
            >
              <Globe className="h-4 w-4" />
              {language.toUpperCase()}
            </Button>

            {location.pathname !== '/login' && location.pathname !== '/dashboard' && (
              <Link to="/login">
                <Button variant="default" size="sm">
                  {t.nav.login}
                </Button>
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};
