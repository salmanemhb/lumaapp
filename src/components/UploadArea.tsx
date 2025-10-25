import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/contexts/LanguageContext';
import { useTranslation } from '@/lib/i18n';
import { toast } from 'sonner';

const API_URL = import.meta.env.VITE_API_URL || 'https://luma-final.onrender.com';

interface UploadedFile {
  name: string;
  status: 'uploading' | 'processing' | 'processed' | 'failed';
  emissions?: number;
  fileId?: string;
  error?: string;
}

export default function UploadArea() {
  const { language } = useLanguage();
  const { t } = useTranslation(language);
  const [files, setFiles] = useState<UploadedFile[]>([]);

  const uploadToBackend = async (file: File): Promise<void> => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      // Get token from localStorage (matches AuthContext key)
      const token = localStorage.getItem('luma_auth_token');
      if (!token) {
        throw new Error('Not authenticated. Please log in again.');
      }

      const response = await fetch(`${API_URL}/api/files/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      
      // Update file status with actual data
      setFiles((prev) =>
        prev.map((f) =>
          f.name === file.name
            ? {
                ...f,
                status: 'processed',
                emissions: data.record?.co2e_kg || 0,
                fileId: data.file_id,
              }
            : f
        )
      );

      toast.success(`${file.name} processed successfully!`);
    } catch (error) {
      console.error('Upload error:', error);
      
      setFiles((prev) =>
        prev.map((f) =>
          f.name === file.name
            ? {
                ...f,
                status: 'failed',
                error: error instanceof Error ? error.message : 'Upload failed',
              }
            : f
        )
      );

      toast.error(`Failed to upload ${file.name}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      // Create initial file entries
      const newFiles: UploadedFile[] = acceptedFiles.map((file) => ({
        name: file.name,
        status: 'uploading',
      }));

      setFiles((prev) => [...prev, ...newFiles]);

      // Upload each file to backend
      acceptedFiles.forEach((file) => {
        uploadToBackend(file);
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
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
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
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-destructive" />;
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
      case 'failed':
        return 'Failed';
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
              <div className="flex items-center gap-3 flex-1">
                <File className="h-5 w-5 text-primary" />
                <div className="flex-1">
                  <p className="text-sm font-medium">{file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {file.status === 'processed' && file.emissions !== undefined
                      ? `${file.emissions.toFixed(2)} kg CO₂e`
                      : file.error || '—'}
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
