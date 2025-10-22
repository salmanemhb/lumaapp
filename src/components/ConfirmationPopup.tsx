import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { CheckCircle } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useTranslation } from '@/lib/i18n';

interface ConfirmationPopupProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ConfirmationPopup = ({ isOpen, onClose }: ConfirmationPopupProps) => {
  const { language } = useLanguage();
  const { t } = useTranslation(language);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-sage-light">
            <CheckCircle className="h-6 w-6 text-sage-dark" />
          </div>
          <DialogTitle className="text-2xl">{t.confirmation.title}</DialogTitle>
          <DialogDescription className="text-base pt-2">
            {t.confirmation.message}
          </DialogDescription>
        </DialogHeader>
        <div className="flex justify-center pt-4">
          <Button onClick={onClose} variant="default">
            {t.confirmation.close}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
