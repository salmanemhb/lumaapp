import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { useLanguage } from '@/contexts/LanguageContext';
import { useTranslation } from '@/lib/i18n';
import { toast } from 'sonner';

interface JoinFormProps {
  onSuccess: () => void;
}

export const JoinForm = ({ onSuccess }: JoinFormProps) => {
  const { language } = useLanguage();
  const { t } = useTranslation(language);
  const [isSubmitting, setIsSubmitting] = useState(false);
  // Form state
  const [formData, setFormData] = useState({
    companyName: '',
    contactName: '',
    email: '',
    country: '',
    message: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await fetch('https://luma-final.onrender.com/api/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          company_name: formData.companyName,
          sector: formData.country, // Using country as sector for now
          contact_email: formData.email,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Signup failed');
      }
      
      onSuccess();
      sessionStorage.setItem('show_confirmation_banner', 'true');
      
      // Reset form
      setFormData({
        companyName: '',
        contactName: '',
        email: '',
        country: '',
        message: '',
      });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Something went wrong. Please try again.');
      console.error('Join form error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  return (
    <Card className="w-full max-w-2xl mx-auto shadow-elevated animate-slide-up">
      <CardHeader className="text-center">
        <CardTitle className="text-3xl">{t.joinForm.title}</CardTitle>
        <CardDescription className="text-base">{t.joinForm.subtitle}</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="companyName">{t.joinForm.companyName}</Label>
              <Input
                id="companyName"
                name="companyName"
                value={formData.companyName}
                onChange={handleChange}
                placeholder={t.joinForm.companyNamePlaceholder}
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="contactName">{t.joinForm.contactName}</Label>
              <Input
                id="contactName"
                name="contactName"
                value={formData.contactName}
                onChange={handleChange}
                placeholder={t.joinForm.contactNamePlaceholder}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="email">{t.joinForm.email}</Label>
              <Input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                placeholder={t.joinForm.emailPlaceholder}
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="country">{t.joinForm.country}</Label>
              <Input
                id="country"
                name="country"
                value={formData.country}
                onChange={handleChange}
                placeholder={t.joinForm.countryPlaceholder}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="message">{t.joinForm.message}</Label>
            <Textarea
              id="message"
              name="message"
              value={formData.message}
              onChange={handleChange}
              placeholder={t.joinForm.messagePlaceholder}
              rows={4}
            />
          </div>

          <Button 
            type="submit" 
            variant="hero" 
            size="lg" 
            className="w-full"
            disabled={isSubmitting}
          >
            {isSubmitting ? t.joinForm.submitting : t.joinForm.submit}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};
