import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, CheckCircle2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/contexts/LanguageContext';
import { useTranslation } from '@/lib/i18n';
import { toast } from 'sonner';

interface UploadedFile {
  name: string;
  status: 'uploading' | 'processing' | 'processed';
  emissions?: number;
}

export default function UploadArea() {
  const { language } = useLanguage();
  const { t } = useTranslation(language);
  const [files, setFiles] = useState<UploadedFile[]>([]);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newFiles: UploadedFile[] = acceptedFiles.map((file) => ({
        name: file.name,
        status: 'uploading',
      }));

      setFiles((prev) => [...prev, ...newFiles]);

      // Simulate upload and processing with status updates
      newFiles.forEach((file, index) => {
        setTimeout(() => {
          setFiles((prev) =>
            prev.map((f) =>
              f.name === file.name ? { ...f, status: 'processing' } : f
            )
          );
        }, 1000 + index * 200);

        setTimeout(() => {
          setFiles((prev) =>
            prev.map((f) =>
              f.name === file.name
                ? { ...f, status: 'processed', emissions: Math.random() * 100 }
                : f
            )
          );
        }, 3000 + index * 500);
      });
    },
    []
  );

  const onDropRejected = useCallback(() => {
    toast.error(t.dashboard.error);
  }, [t]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    onDropRejected,
    accept: {
      'application/pdf': ['.pdf'],
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
    },
    maxSize: 10485760, // 10MB
  });

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return <Loader2 className="h-5 w-5 text-primary animate-spin" />;
      case 'processing':
        return <Loader2 className="h-5 w-5 text-primary animate-spin" />;
      case 'processed':
        return <CheckCircle2 className="h-5 w-5 text-primary" />;
    }
  };

  const getStatusText = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return t.dashboard.uploading;
      case 'processing':
        return t.dashboard.processing;
      case 'processed':
        return t.dashboard.processed;
    }
  };

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-border hover:border-primary/50 bg-background'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-lg font-medium mb-2">{t.dashboard.dragDrop}</p>
        <p className="text-sm text-muted-foreground mb-4">{t.dashboard.orBrowse}</p>
        <Button variant="default" type="button">
          {t.dashboard.uploadButton}
        </Button>
        <p className="text-xs text-muted-foreground mt-4">
          {t.dashboard.supportedFormats}
        </p>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-4 bg-card border rounded-lg animate-fade-in"
            >
              <div className="flex items-center gap-3">
                <File className="h-5 w-5 text-primary" />
                <div>
                  <p className="text-sm font-medium">{file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {file.emissions ? `${file.emissions.toFixed(1)} kg CO₂e` : '—'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {getStatusIcon(file.status)}
                <span className="text-sm text-muted-foreground">
                  {getStatusText(file.status)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
