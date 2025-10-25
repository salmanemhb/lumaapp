import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Joyride, { Step } from 'react-joyride';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import UploadArea from '@/components/UploadArea';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { LogOut, FileText, Mail, Download, TrendingUp, TrendingDown, Calendar, Loader2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useTranslation } from '@/lib/i18n';
import { toast } from 'sonner';
import lumaLogo from '@/assets/luma-logo.png';

const API_URL = import.meta.env.VITE_API_URL || 'https://luma-final.onrender.com';

export default function Dashboard() {
  const { logout, user, isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  const { language } = useLanguage();
  const { t } = useTranslation(language);
  const [showGuide, setShowGuide] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [lastReportDate, setLastReportDate] = useState<Date | null>(null);
  const [uploads, setUploads] = useState<any[]>([]);
  const [dashboardData, setDashboardData] = useState<any>(null);
  
  // Check if user is demo or real user
  const isDemo = user?.email === 'demo@luma.es';
  const hasData = uploads.length > 0 || isDemo;

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      toast.error(t.login.sessionExpired);
      navigate('/login');
    }
  }, [isAuthenticated, authLoading, navigate, t]);

  useEffect(() => {
    const loadDashboardData = async () => {
      if (!isAuthenticated || authLoading) return;

      try {
        const token = localStorage.getItem('access_token');
        
        // Fetch uploads
        const uploadsResponse = await fetch(`${API_URL}/api/files/uploads`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (uploadsResponse.ok) {
          const uploadsData = await uploadsResponse.json();
          setUploads(uploadsData);
        }

        // Fetch dashboard summary
        const dashboardResponse = await fetch(`${API_URL}/api/dashboard`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (dashboardResponse.ok) {
          const data = await dashboardResponse.json();
          setDashboardData(data);
        }
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setIsLoading(false);
        // Check if this is first visit for guide
        const hasSeenGuide = localStorage.getItem('luma_guide_seen');
        if (!hasSeenGuide && (uploads.length > 0 || isDemo)) {
          setShowGuide(true);
        }
      }
    };

    loadDashboardData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, [isAuthenticated, authLoading, isDemo]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleGenerateReport = async () => {
    setIsGeneratingReport(true);
    // Simulate report generation
    await new Promise(resolve => setTimeout(resolve, 2000));
    setLastReportDate(new Date());
    setIsGeneratingReport(false);
    toast.success(t.dashboard.reportReady);
  };

  const steps: Step[] = [
    {
      target: '.upload-section',
      content: t.guide.steps.upload,
      disableBeacon: true,
    },
    {
      target: '.kpi-cards',
      content: t.guide.steps.emissions,
    },
    {
      target: '.charts-section',
      content: t.guide.steps.charts,
    },
    {
      target: '.report-section',
      content: t.guide.steps.report,
    },
  ];

  // Mock data (used for demo or when no real data available)
  const monthlyData = dashboardData?.monthly_emissions || [
    { month: 'Jan', emissions: 120 },
    { month: 'Feb', emissions: 150 },
    { month: 'Mar', emissions: 135 },
    { month: 'Apr', emissions: 145 },
    { month: 'May', emissions: 160 },
    { month: 'Jun', emissions: 140 },
  ];

  const scopeData = dashboardData?.scope_breakdown || [
    { name: t.dashboard.scope1, value: 450, color: 'hsl(var(--sage))' },
    { name: t.dashboard.scope2, value: 320, color: 'hsl(var(--gold))' },
    { name: t.dashboard.scope3, value: 180, color: 'hsl(var(--accent))' },
  ];

  const recentFiles = uploads.slice(0, 4).map((upload: any) => ({
    name: upload.file_name,
    status: upload.status,
    emissions: upload.co2e_kg,
    date: upload.uploaded_at,
  }));

  const currentMonthEmissions = dashboardData?.total_emissions_kg || (isDemo ? 950 : 0);
  const lastMonthEmissions = dashboardData?.last_month_emissions_kg || (isDemo ? 1020 : 0);
  const percentChange = lastMonthEmissions > 0 
    ? ((currentMonthEmissions - lastMonthEmissions) / lastMonthEmissions * 100).toFixed(1)
    : '0.0';
  const isDecrease = currentMonthEmissions < lastMonthEmissions;
  const progress = dashboardData?.csrd_readiness_pct || (isDemo ? 78 : 0);

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="border-b bg-card">
          <div className="container mx-auto px-4 py-4 flex justify-between items-center">
            <Skeleton className="h-10 w-24" />
            <Skeleton className="h-10 w-32" />
          </div>
        </div>
        <div className="container mx-auto px-4 py-8 space-y-6">
          <Skeleton className="h-12 w-64" />
          <div className="grid md:grid-cols-4 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {[1, 2].map((i) => (
              <Skeleton key={i} className="h-64" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Joyride
        steps={steps}
        run={showGuide}
        continuous
        showProgress
        showSkipButton
        callback={(data) => {
          if (data.status === 'finished' || data.status === 'skipped') {
            setShowGuide(false);
            localStorage.setItem('luma_guide_seen', 'true');
          }
        }}
        styles={{
          options: {
            primaryColor: 'hsl(var(--primary))',
            zIndex: 10000,
          },
        }}
        locale={{
          skip: t.guide.skip,
          next: t.guide.next,
          back: t.guide.prev,
          last: t.guide.finish,
        }}
      />

      {/* Demo Mode Banner */}
      {user?.email === 'demo@luma.es' && (
        <div className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white py-2 px-4 text-center">
          <p className="text-sm font-medium">
            🎯 Demo Mode - All data shown is sample data for demonstration purposes
          </p>
        </div>
      )}

      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <img src={lumaLogo} alt="Luma" className="h-10 w-10" />
            <h1 className="text-2xl font-bold">{t.dashboard.welcome}</h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground hidden sm:inline">{user?.email}</span>
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="h-4 w-4 mr-2" />
              {t.dashboard.logout}
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {!hasData ? (
          /* Empty State */
          <div className="max-w-4xl mx-auto upload-section">
            <Card className="shadow-elevated animate-scale-in">
              <CardHeader className="text-center">
                <CardTitle className="text-3xl mb-2">{t.dashboard.welcome}</CardTitle>
                <CardDescription className="text-base">{t.dashboard.emptyState}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <UploadArea />
                
                <div className="text-center pt-4">
                  <FileText className="mx-auto h-16 w-16 text-muted-foreground mb-4 opacity-50" />
                  <h3 className="text-xl font-semibold mb-2">{t.dashboard.emptyTitle}</h3>
                  <p className="text-muted-foreground">{t.dashboard.emptyDescription}</p>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          /* Dashboard with Data */
          <div className="space-y-8 animate-fade-in">
            {/* Progress Bar */}
            <Card className="shadow-soft">
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">{t.dashboard.progressLabel}</span>
                    <span className="text-muted-foreground">{progress}%</span>
                  </div>
                  <Progress value={progress} className="h-2" />
                  <p className="text-xs text-muted-foreground">
                    {progress < 100 
                      ? `${100 - progress}% remaining to complete your CSRD report`
                      : 'Your CSRD report is ready to generate!'}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Upload Section */}
            <div className="upload-section">
              <h2 className="text-2xl font-bold mb-4">{t.dashboard.uploadButton}</h2>
              <UploadArea />
            </div>

            {/* KPI Cards */}
            <div className="kpi-cards grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="shadow-soft">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">{t.dashboard.totalEmissions}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{currentMonthEmissions} kg</div>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                    {isDecrease ? (
                      <TrendingDown className="h-3 w-3 text-primary" />
                    ) : (
                      <TrendingUp className="h-3 w-3 text-destructive" />
                    )}
                    <span className={isDecrease ? 'text-primary' : 'text-destructive'}>
                      {Math.abs(Number(percentChange))}% {isDecrease ? t.dashboard.decrease : t.dashboard.increase}
                    </span>
                  </div>
                </CardContent>
              </Card>

              <Card className="shadow-soft">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">{t.dashboard.scope1}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">450 kg</div>
                  <p className="text-xs text-muted-foreground">CO₂e</p>
                </CardContent>
              </Card>

              <Card className="shadow-soft">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">{t.dashboard.scope2}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">320 kg</div>
                  <p className="text-xs text-muted-foreground">CO₂e</p>
                </CardContent>
              </Card>

              <Card className="shadow-soft">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">{t.dashboard.dataCoverage}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{progress}%</div>
                  <p className="text-xs text-muted-foreground">Complete</p>
                </CardContent>
              </Card>
            </div>

            {/* Charts */}
            <div className="charts-section grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="shadow-soft">
                <CardHeader>
                  <CardTitle>{t.dashboard.monthlyTrend}</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={monthlyData}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="emissions" 
                        stroke="hsl(var(--sage))" 
                        strokeWidth={2}
                        dot={{ fill: 'hsl(var(--sage))' }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card className="shadow-soft">
                <CardHeader>
                  <CardTitle>{t.dashboard.scopeBreakdown}</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={scopeData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(entry) => `${entry.name}: ${entry.value} kg`}
                        outerRadius={80}
                        dataKey="value"
                      >
                        {scopeData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Report Generation */}
            <Card className="shadow-soft report-section">
              <CardHeader>
                <CardTitle>{t.dashboard.reportGeneration}</CardTitle>
                <CardDescription>
                  Generate your CSRD-compliant sustainability report
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {lastReportDate && (
                  <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                    <div className="flex items-center gap-3">
                      <Calendar className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="text-sm font-medium">{t.dashboard.lastReportGenerated}</p>
                        <p className="text-xs text-muted-foreground">
                          {lastReportDate.toLocaleDateString(language === 'es' ? 'es-ES' : 'en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                          })}
                        </p>
                      </div>
                    </div>
                    <Button variant="outline" size="sm" className="gap-2">
                      <Download className="h-4 w-4" />
                      {t.dashboard.downloadReport}
                    </Button>
                  </div>
                )}
                
                <Button 
                  variant="hero" 
                  size="lg" 
                  className="w-full gap-2"
                  onClick={handleGenerateReport}
                  disabled={isGeneratingReport}
                >
                  {isGeneratingReport ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      {t.dashboard.generatingReport}
                    </>
                  ) : (
                    <>
                      <FileText className="h-5 w-5" />
                      {t.dashboard.generateReport}
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Recent Uploads */}
            <Card className="shadow-soft">
              <CardHeader>
                <CardTitle>{t.dashboard.recentUploads}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{t.dashboard.fileName}</TableHead>
                        <TableHead>{t.dashboard.status}</TableHead>
                        <TableHead className="text-right">{t.dashboard.emissions}</TableHead>
                        <TableHead className="text-right">{t.dashboard.uploaded}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {recentFiles.length > 0 ? (
                        recentFiles.map((file: any, index: number) => (
                          <TableRow key={index}>
                            <TableCell className="flex items-center gap-2">
                              <FileText className="h-4 w-4 text-muted-foreground" />
                              {file.name}
                            </TableCell>
                            <TableCell>
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                file.status === 'processed' 
                                  ? 'bg-primary/10 text-primary' 
                                  : 'bg-muted text-muted-foreground'
                              }`}>
                                {file.status === 'processed' ? t.dashboard.processed : t.dashboard.processing}
                              </span>
                            </TableCell>
                            <TableCell className="text-right font-medium">
                              {file.emissions ? `${file.emissions.toFixed(2)} kg` : '—'}
                            </TableCell>
                            <TableCell className="text-right text-sm text-muted-foreground">
                              {file.date ? new Date(file.date).toLocaleDateString(language === 'es' ? 'es-ES' : 'en-US', {
                                month: 'short',
                                day: 'numeric',
                              }) : '—'}
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                            No uploads yet. Upload your first file to get started!
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      <footer className="mt-16 border-t bg-card">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
            <div className="text-center sm:text-left">
              <p>{t.footer.tagline}</p>
              <p className="mt-1">{t.footer.rights}</p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              asChild
              className="gap-2"
            >
              <a href="mailto:support@getluma.es">
                <Mail className="h-4 w-4" />
                {t.dashboard.needHelp}
              </a>
            </Button>
          </div>
        </div>
      </footer>
    </div>
  );
}
