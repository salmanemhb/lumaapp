import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/contexts/LanguageContext';
import { useTranslation } from '@/lib/i18n';

const BANNER_STORAGE_KEY = 'luma_confirmation_banner_dismissed';

export default function ConfirmationBanner() {
  const [isVisible, setIsVisible] = useState(false);
  const { language } = useLanguage();
  const { t } = useTranslation(language);

  useEffect(() => {
    const showBanner = sessionStorage.getItem('show_confirmation_banner');
    const dismissed = localStorage.getItem(BANNER_STORAGE_KEY);
    
    if (showBanner && !dismissed) {
      setIsVisible(true);
      sessionStorage.removeItem('show_confirmation_banner');
    }
  }, []);

  const handleDismiss = () => {
    setIsVisible(false);
    localStorage.setItem(BANNER_STORAGE_KEY, 'true');
  };

  if (!isVisible) return null;

  return (
    <div className="bg-primary/10 border-b border-primary/20 animate-fade-in">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between gap-4">
        <p className="text-sm text-foreground flex-1">
          {t.confirmation.banner}
        </p>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleDismiss}
          className="h-6 w-6 p-0 hover:bg-primary/20"
        >
          <X className="h-4 w-4" />
          <span className="sr-only">Dismiss</span>
        </Button>
      </div>
    </div>
  );
}
