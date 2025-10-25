import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Joyride, { Step } from 'react-joyride';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import UploadArea from '@/components/UploadArea';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { LogOut, FileText, Mail, Download, TrendingUp, TrendingDown, Calendar, Loader2, Trash2, ChevronRight, ChevronDown, Calculator, Package, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
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
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [loadingDetails, setLoadingDetails] = useState<Set<string>>(new Set());
  const [fileDetails, setFileDetails] = useState<Map<string, any>>(new Map());
  
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
        const token = localStorage.getItem('luma_auth_token');
        if (!token) return;
        
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

  const handleDeleteFile = async (fileId: string, fileName: string) => {
    if (!confirm(`Delete ${fileName}? This cannot be undone.`)) return;
    
    try {
      const token = localStorage.getItem('luma_auth_token');
      const response = await fetch(`${API_URL}/api/files/uploads/${fileId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        toast.success('File deleted successfully');
        // Refresh uploads list
        setUploads(prev => prev.filter((u: any) => u.file_id !== fileId));
        // Also refresh dashboard data
        const dashboardResponse = await fetch(`${API_URL}/api/dashboard`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (dashboardResponse.ok) {
          const data = await dashboardResponse.json();
          setDashboardData(data);
        }
      } else {
        toast.error('Failed to delete file');
      }
    } catch (error) {
      console.error('Delete error:', error);
      toast.error('Failed to delete file');
    }
  };

  const toggleRowExpansion = async (fileId: string) => {
    const newExpanded = new Set(expandedRows);
    
    if (newExpanded.has(fileId)) {
      // Collapse
      newExpanded.delete(fileId);
      setExpandedRows(newExpanded);
    } else {
      // Expand
      newExpanded.add(fileId);
      setExpandedRows(newExpanded);
      
      // Fetch details if not already loaded
      if (!fileDetails.has(fileId)) {
        const newLoading = new Set(loadingDetails);
        newLoading.add(fileId);
        setLoadingDetails(newLoading);
        
        try {
          const token = localStorage.getItem('luma_auth_token');
          const response = await fetch(`${API_URL}/api/files/uploads/${fileId}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });
          
          if (response.ok) {
            const details = await response.json();
            const newDetails = new Map(fileDetails);
            newDetails.set(fileId, details);
            setFileDetails(newDetails);
          }
        } catch (error) {
          console.error('Failed to fetch file details:', error);
        } finally {
          const newLoading = new Set(loadingDetails);
          newLoading.delete(fileId);
          setLoadingDetails(newLoading);
        }
      }
    }
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

  // Calculate totals from actual uploads
  const totalEmissions = uploads.reduce((sum: number, u: any) => sum + (u.co2e_kg || 0), 0);
  const scope1Total = uploads.filter((u: any) => u.scope === 1).reduce((sum: number, u: any) => sum + (u.co2e_kg || 0), 0);
  const scope2Total = uploads.filter((u: any) => u.scope === 2).reduce((sum: number, u: any) => sum + (u.co2e_kg || 0), 0);
  const scope3Total = uploads.filter((u: any) => u.scope === 3).reduce((sum: number, u: any) => sum + (u.co2e_kg || 0), 0);
  
  // Use real data first, fall back to demo only if demo user AND no real data
  const hasRealData = uploads.length > 0;
  const showDemoData = isDemo && !hasRealData;
  
  const monthlyData = showDemoData ? [
    { month: 'Jan', emissions: 120 },
    { month: 'Feb', emissions: 150 },
    { month: 'Mar', emissions: 135 },
    { month: 'Apr', emissions: 145 },
    { month: 'May', emissions: 160 },
    { month: 'Jun', emissions: 140 },
  ] : (dashboardData?.monthly_emissions || []);

  const scopeData = showDemoData ? [
    { name: t.dashboard.scope1, value: 450, color: 'hsl(var(--sage))' },
    { name: t.dashboard.scope2, value: 320, color: 'hsl(var(--gold))' },
    { name: t.dashboard.scope3, value: 180, color: 'hsl(var(--accent))' },
  ] : (hasRealData ? [
    { name: t.dashboard.scope1, value: scope1Total, color: 'hsl(var(--sage))' },
    { name: t.dashboard.scope2, value: scope2Total, color: 'hsl(var(--gold))' },
    { name: t.dashboard.scope3, value: scope3Total, color: 'hsl(var(--accent))' },
  ] : []);

  // Group uploads by filename and aggregate
  const groupedUploads = uploads.reduce((acc: any, upload: any) => {
    const key = upload.file_name;
    if (!acc[key]) {
      acc[key] = {
        file_name: upload.file_name,
        file_id: upload.file_id,
        status: upload.status,
        uploaded_at: upload.uploaded_at,
        records: [],
        total_emissions: 0,
        record_count: 0,
      };
    }
    acc[key].records.push(upload);
    acc[key].total_emissions += upload.co2e_kg || 0;
    acc[key].record_count += 1;
    if (upload.status === 'processing') {
      acc[key].status = 'processing';
    }
    return acc;
  }, {});

  const recentFiles = Object.values(groupedUploads)
    .sort((a: any, b: any) => new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime())
    .map((group: any) => ({
      file_id: group.file_id,
      name: group.file_name,
      status: group.status,
      emissions: group.total_emissions,
      date: group.uploaded_at,
      record_count: group.record_count,
      records: group.records,
    }));

  const currentMonthEmissions = hasRealData ? Number(totalEmissions.toFixed(2)) : (showDemoData ? 950 : 0);
  const lastMonthEmissions = showDemoData ? 1020 : (dashboardData?.last_month_emissions_kg || 0);
  const percentChange = lastMonthEmissions > 0 
    ? ((currentMonthEmissions - lastMonthEmissions) / lastMonthEmissions * 100).toFixed(1)
    : '0.0';
  const isDecrease = currentMonthEmissions < lastMonthEmissions;
  const progress = hasRealData ? Number(((uploads.filter((u: any) => u.status === 'processed').length / uploads.length) * 100).toFixed(2)) : (showDemoData ? 78 : 0);

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
                <UploadArea onUploadComplete={() => {
                  // Reload dashboard data after upload
                  const token = localStorage.getItem('luma_auth_token');
                  if (token) {
                    fetch(`${API_URL}/api/files/uploads`, {
                      headers: { 'Authorization': `Bearer ${token}` },
                    })
                      .then(res => res.json())
                      .then(data => setUploads(data))
                      .catch(console.error);
                  }
                }} />
                
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
              <UploadArea onUploadComplete={() => {
                // Reload dashboard data after upload
                const token = localStorage.getItem('luma_auth_token');
                if (token) {
                  fetch(`${API_URL}/api/files/uploads`, {
                    headers: { 'Authorization': `Bearer ${token}` },
                  })
                    .then(res => res.json())
                    .then(data => {
                      setUploads(data);
                      // Also refresh dashboard summary
                      fetch(`${API_URL}/api/dashboard`, {
                        headers: { 'Authorization': `Bearer ${token}` },
                      })
                        .then(res => res.json())
                        .then(summary => setDashboardData(summary))
                        .catch(console.error);
                    })
                    .catch(console.error);
                }
              }} />
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
                  <div className="text-2xl font-bold">{scope1Total.toFixed(2)} kg</div>
                  <p className="text-xs text-muted-foreground">CO₂e</p>
                </CardContent>
              </Card>

              <Card className="shadow-soft">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">{t.dashboard.scope2}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{scope2Total.toFixed(2)} kg</div>
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
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
                <CardTitle>{t.dashboard.recentUploads}</CardTitle>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={async () => {
                    if (confirm('Are you sure you want to delete ALL uploads? This cannot be undone.')) {
                      try {
                        const token = localStorage.getItem('luma_auth_token');
                        const response = await fetch(`${API_URL}/api/files/uploads/clear`, {
                          method: 'DELETE',
                          headers: {
                            'Authorization': `Bearer ${token}`,
                          },
                        });
                        if (response.ok) {
                          const result = await response.json();
                          toast.success(`Successfully deleted ${result.deleted_count} upload(s)`);
                          setUploads([]);
                          setDashboardData(null);
                        } else {
                          const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
                          toast.error(`Failed to clear uploads: ${error.detail || response.statusText}`);
                        }
                      } catch (error) {
                        console.error('Clear uploads error:', error);
                        toast.error(`Failed to clear uploads: ${error instanceof Error ? error.message : 'Network error'}`);
                      }
                    }
                  }}
                  className="gap-2"
                >
                  <Trash2 className="h-4 w-4" />
                  Clear All
                </Button>
              </CardHeader>
              <CardContent>
                <div className="max-h-[600px] overflow-y-auto overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[40px]"></TableHead>
                        <TableHead>{t.dashboard.fileName}</TableHead>
                        <TableHead>{t.dashboard.status}</TableHead>
                        <TableHead className="text-right">{t.dashboard.emissions}</TableHead>
                        <TableHead className="text-right">{t.dashboard.uploaded}</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {recentFiles.length > 0 ? (
                        recentFiles.map((file: any, index: number) => {
                          const isExpanded = expandedRows.has(file.file_id);
                          const details = fileDetails.get(file.file_id);
                          const isLoadingDetails = loadingDetails.has(file.file_id);
                          
                          return (
                            <>
                              <TableRow key={index} className="group">
                                <TableCell className="w-[40px]">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => toggleRowExpansion(file.file_id)}
                                    className="h-6 w-6 p-0 hover:bg-accent"
                                  >
                                    {isExpanded ? (
                                      <ChevronDown className="h-4 w-4 text-muted-foreground transition-transform" />
                                    ) : (
                                      <ChevronRight className="h-4 w-4 text-muted-foreground transition-transform" />
                                    )}
                                  </Button>
                                </TableCell>
                                <TableCell>
                                  <div className="flex items-center gap-2">
                                    <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                                    <span className="font-medium truncate">{file.name}</span>
                                    {file.record_count > 1 && (
                                      <Badge variant="secondary" className="text-xs">
                                        {file.record_count} invoices
                                      </Badge>
                                    )}
                                  </div>
                                </TableCell>
                                <TableCell>
                                  <Badge 
                                    variant={file.status === 'processed' ? 'default' : 'secondary'}
                                    className="font-normal"
                                  >
                                    {file.status === 'processed' ? t.dashboard.processed : t.dashboard.processing}
                                  </Badge>
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
                                <TableCell className="text-right">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleDeleteFile(file.file_id || uploads[index]?.file_id, file.name)}
                                    className="h-8 w-8 p-0 text-destructive hover:text-destructive hover:bg-destructive/10"
                                  >
                                    <Trash2 className="h-4 w-4" />
                                  </Button>
                                </TableCell>
                              </TableRow>
                              
                              {/* Expandable Details Row */}
                              {isExpanded && (
                                <TableRow key={`${index}-details`} className="bg-muted/30 hover:bg-muted/30">
                                  <TableCell colSpan={6} className="p-0">
                                    <div className="px-6 py-4 space-y-4 animate-in slide-in-from-top-2 duration-200">
                                      {file.record_count > 1 && file.record_count <= 15 ? (
                                        <div className="space-y-4">
                                          <div className="text-sm font-semibold text-muted-foreground">
                                            Showing {file.record_count} invoices from this file:
                                          </div>
                                          <div className="grid gap-3">
                                            {file.records?.map((rec: any, idx: number) => (
                                              <div key={idx} className="border rounded-lg p-3 bg-background space-y-2">
                                                <div className="flex justify-between items-start">
                                                  <div className="space-y-1 flex-1">
                                                    <div className="font-medium text-sm">
                                                      {rec.supplier || 'Unknown Supplier'}
                                                      {rec.invoice_number && <span className="text-muted-foreground ml-2 text-xs">#{rec.invoice_number}</span>}
                                                    </div>
                                                    {rec.usage_value ? (
                                                      <div className="text-xs text-muted-foreground">
                                                        {rec.usage_value.toLocaleString()} {rec.usage_unit}
                                                      </div>
                                                    ) : (
                                                      <div className="text-xs text-orange-600">
                                                        ⚠️ Usage value not extracted
                                                      </div>
                                                    )}
                                                    {rec.amount_total && (
                                                      <div className="text-xs text-muted-foreground">
                                                        Amount: €{rec.amount_total.toFixed(2)}
                                                      </div>
                                                    )}
                                                    {rec.category && (
                                                      <div className="text-xs text-muted-foreground capitalize">
                                                        Category: {rec.category}
                                                      </div>
                                                    )}
                                                  </div>
                                                  <div className="text-right">
                                                    <div className="font-semibold text-sm">
                                                      {rec.co2e_kg ? `${rec.co2e_kg.toFixed(2)} kg` : <span className="text-orange-600">—</span>}
                                                    </div>
                                                    {rec.confidence !== undefined && (
                                                      <div className={`text-xs ${rec.confidence >= 0.7 ? 'text-green-600' : rec.confidence >= 0.5 ? 'text-yellow-600' : 'text-orange-600'}`}>
                                                        {(rec.confidence * 100).toFixed(0)}% confidence
                                                      </div>
                                                    )}
                                                  </div>
                                                </div>
                                                {(!rec.usage_value || !rec.co2e_kg) && (
                                                  <div className="text-xs text-muted-foreground bg-muted/50 p-2 rounded">
                                                    <span className="font-medium">Extraction issues:</span> Unable to extract {!rec.usage_value && 'usage value'}{!rec.usage_value && !rec.co2e_kg && ', '}{!rec.co2e_kg && 'emissions calculation'}. Manual review needed.
                                                  </div>
                                                )}
                                              </div>
                                            ))}
                                          </div>
                                          <div className="text-sm font-semibold pt-2 border-t">
                                            Total: {file.emissions?.toFixed(2)} kg CO₂e
                                          </div>
                                        </div>
                                      ) : file.record_count > 15 ? (
                                        <div className="text-center py-8 space-y-2">
                                          <div className="text-lg font-semibold">
                                            This file contains {file.record_count} invoices
                                          </div>
                                          <div className="text-sm text-muted-foreground">
                                            Total emissions: {file.emissions?.toFixed(2)} kg CO₂e
                                          </div>
                                          <div className="text-xs text-muted-foreground">
                                            Individual invoice details are not shown for large batch files ({'>'}15 records)
                                          </div>
                                        </div>
                                      ) : isLoadingDetails ? (
                                        <div className="flex items-center justify-center py-8">
                                          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                        </div>
                                      ) : details ? (
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                          {/* Left Column - Extracted Data */}
                                          <div className="space-y-3">
                                            <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                                              <Package className="h-4 w-4 text-primary" />
                                              Extracted Data
                                            </div>
                                            <div className="space-y-2 pl-6 border-l-2 border-primary/20">
                                              {details.supplier && (
                                                <div className="flex justify-between text-sm">
                                                  <span className="text-muted-foreground">Supplier:</span>
                                                  <span className="font-medium">{details.supplier}</span>
                                                </div>
                                              )}
                                              {details.category && (
                                                <div className="flex justify-between text-sm">
                                                  <span className="text-muted-foreground">Category:</span>
                                                  <span className="font-medium capitalize">{details.category}</span>
                                                </div>
                                              )}
                                              {details.scope && (
                                                <div className="flex justify-between text-sm">
                                                  <span className="text-muted-foreground">Scope:</span>
                                                  <Badge variant="outline" className="font-normal">
                                                    Scope {details.scope}
                                                  </Badge>
                                                </div>
                                              )}
                                              {details.invoice_number && (
                                                <div className="flex justify-between text-sm">
                                                  <span className="text-muted-foreground">Invoice #:</span>
                                                  <span className="font-mono text-xs">{details.invoice_number}</span>
                                                </div>
                                              )}
                                              {details.usage_value && (
                                                <div className="flex justify-between text-sm">
                                                  <span className="text-muted-foreground">Consumption:</span>
                                                  <span className="font-medium">
                                                    {details.usage_value.toLocaleString()} {details.usage_unit || ''}
                                                  </span>
                                                </div>
                                              )}
                                              {details.amount_total && (
                                                <div className="flex justify-between text-sm">
                                                  <span className="text-muted-foreground">Amount:</span>
                                                  <span className="font-medium">
                                                    €{details.amount_total.toFixed(2)}
                                                  </span>
                                                </div>
                                              )}
                                              {details.period_start && details.period_end && (
                                                <div className="flex justify-between text-sm">
                                                  <span className="text-muted-foreground">Period:</span>
                                                  <span className="text-xs">
                                                    {new Date(details.period_start).toLocaleDateString()} - {new Date(details.period_end).toLocaleDateString()}
                                                  </span>
                                                </div>
                                              )}
                                            </div>
                                          </div>

                                          {/* Right Column - Calculation & Metadata */}
                                          <div className="space-y-3">
                                            {/* Emission Calculation */}
                                            <div className="space-y-2">
                                              <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                                                <Calculator className="h-4 w-4 text-sage" />
                                                Emission Calculation
                                              </div>
                                              <div className="pl-6 border-l-2 border-sage/20">
                                                {details.usage_value && details.emission_factor ? (
                                                  <div className="space-y-1">
                                                    <div className="text-sm text-muted-foreground font-mono">
                                                      {details.usage_value.toLocaleString()} {details.usage_unit} × {details.emission_factor} kg/unit
                                                    </div>
                                                    <div className="text-lg font-bold text-sage">
                                                      = {details.co2e_kg?.toFixed(2)} kg CO₂e
                                                    </div>
                                                  </div>
                                                ) : (
                                                  <div className="text-sm text-muted-foreground">No calculation data</div>
                                                )}
                                              </div>
                                            </div>

                                            {/* Confidence & Status */}
                                            <div className="space-y-2 pt-2">
                                              <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                                                <Clock className="h-4 w-4 text-gold" />
                                                Processing Info
                                              </div>
                                              <div className="pl-6 space-y-2 border-l-2 border-gold/20">
                                                {details.confidence !== undefined && (
                                                  <div className="flex items-center justify-between text-sm">
                                                    <span className="text-muted-foreground">Confidence:</span>
                                                    <div className="flex items-center gap-2">
                                                      {details.confidence >= 0.8 ? (
                                                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                                                      ) : details.confidence >= 0.6 ? (
                                                        <CheckCircle2 className="h-4 w-4 text-yellow-500" />
                                                      ) : (
                                                        <AlertCircle className="h-4 w-4 text-orange-500" />
                                                      )}
                                                      <span className="font-medium">{(details.confidence * 100).toFixed(0)}%</span>
                                                    </div>
                                                  </div>
                                                )}
                                                {details.meta && typeof details.meta === 'string' && (
                                                  <div className="text-xs text-muted-foreground">
                                                    <pre className="bg-muted/50 p-2 rounded overflow-x-auto">
                                                      {JSON.stringify(JSON.parse(details.meta), null, 2)}
                                                    </pre>
                                                  </div>
                                                )}
                                                {details.processed_at && (
                                                  <div className="flex justify-between text-xs text-muted-foreground">
                                                    <span>Processed:</span>
                                                    <span>{new Date(details.processed_at).toLocaleString()}</span>
                                                  </div>
                                                )}
                                              </div>
                                            </div>
                                          </div>
                                        </div>
                                      ) : (
                                        <div className="text-center py-4 text-sm text-muted-foreground">
                                          No details available
                                        </div>
                                      )}
                                    </div>
                                  </TableCell>
                                </TableRow>
                              )}
                            </>
                          );
                        })
                      ) : (
                        <TableRow>
                          <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
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
