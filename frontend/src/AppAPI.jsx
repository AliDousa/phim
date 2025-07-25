import React, { useState, useCallback, useEffect } from 'react';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import AuthPage from '@/components/auth/AuthPage';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import Header from '@/components/layout/Header';
import SimulationManagerAPI from '@/components/SimulationManagerAPI';
import DatasetManagerAPI from '@/components/DatasetManagerAPI';
import VisualizationDashboard from '@/components/VisualizationDashboard';
import ApiService from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Toaster } from 'sonner';
import {
  LayoutDashboard,
  Beaker,
  Database,
  Activity,
  TrendingUp,
  Users,
  AlertCircle,
  Menu,
  X,
  Plus,
  Play,
  Pause,
  BarChart3,
  LineChart,
  CheckCircle,
  Clock,
  Sparkles,
  Brain,
  Globe,
  Zap,
  Settings,
  Loader2,
  RefreshCw
} from 'lucide-react';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

const StatusBadge = ({ status }) => {
  const variants = {
    completed: {
      variant: "default",
      color: "bg-emerald-500 text-emerald-50",
      icon: CheckCircle,
      glow: "shadow-emerald-500/20"
    },
    running: {
      variant: "secondary", 
      color: "bg-blue-500 text-blue-50",
      icon: Activity,
      glow: "shadow-blue-500/20"
    },
    pending: {
      variant: "outline",
      color: "bg-slate-500 text-slate-50",
      icon: Clock,
      glow: "shadow-slate-500/20"
    },
    failed: {
      variant: "destructive",
      color: "bg-red-500 text-red-50",
      icon: AlertCircle,
      glow: "shadow-red-500/20"
    }
  };

  const config = variants[status] || variants.pending;
  const IconComponent = config.icon;

  return (
    <Badge className={`${config.color} ${config.glow} shadow-lg border-0 px-3 py-1 flex items-center gap-2 font-medium`}>
      <div className="w-2 h-2 rounded-full bg-current animate-pulse" />
      <IconComponent className="w-3 h-3" />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
};

const MetricCard = ({ title, value, change, icon: Icon, trend = "up", subtitle, color = "blue", loading = false }) => {
  const colorClasses = {
    blue: "from-blue-500/10 to-blue-600/5 border-blue-200/50 text-blue-600",
    emerald: "from-emerald-500/10 to-emerald-600/5 border-emerald-200/50 text-emerald-600",
    purple: "from-purple-500/10 to-purple-600/5 border-purple-200/50 text-purple-600",
    orange: "from-orange-500/10 to-orange-600/5 border-orange-200/50 text-orange-600"
  };

  return (
    <Card className="group relative overflow-hidden border-0 shadow-xl hover:shadow-2xl transition-all duration-500 hover:-translate-y-1">
      <div className={`absolute inset-0 bg-gradient-to-br ${colorClasses[color]} opacity-60`} />
      <div className="absolute top-0 right-0 w-32 h-32 opacity-10">
        <Icon className="w-full h-full transform rotate-12 scale-150" />
      </div>
      <CardHeader className="relative flex flex-row items-center justify-between space-y-0 pb-3">
        <div className="space-y-1">
          <CardTitle className="text-sm font-semibold text-slate-600 uppercase tracking-wide">{title}</CardTitle>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-xl bg-white/80 backdrop-blur-sm ${colorClasses[color]} shadow-lg`}>
          {loading ? (
            <Loader2 className="h-6 w-6 animate-spin" />
          ) : (
            <Icon className="h-6 w-6" />
          )}
        </div>
      </CardHeader>
      <CardContent className="relative">
        {loading ? (
          <div className="space-y-2">
            <div className="h-8 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4" />
          </div>
        ) : (
          <>
            <div className="text-3xl font-bold text-slate-900 mb-2">{value}</div>
            {change && (
              <div className={`flex items-center gap-2 text-sm ${trend === 'up' ? 'text-emerald-600' : 'text-red-600'}`}>
                <TrendingUp className={`h-4 w-4 ${trend === 'down' ? 'rotate-180' : ''}`} />
                <span className="font-medium">{change}</span>
                <span className="text-slate-500">vs last month</span>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

const Navigation = ({ activeView, setActiveView, isMobileMenuOpen, setIsMobileMenuOpen }) => {
  const navItems = [
    { id: 'dashboard', label: 'Overview', icon: LayoutDashboard, color: 'text-blue-600' },
    { id: 'simulations', label: 'Simulations', icon: Beaker, color: 'text-purple-600' },
    { id: 'datasets', label: 'Datasets', icon: Database, color: 'text-emerald-600' },
    { id: 'visualize', label: 'Analytics', icon: BarChart3, color: 'text-orange-600' }
  ];

  const NavButton = ({ item }) => (
    <Button
      variant={activeView === item.id ? 'default' : 'ghost'}
      className={`w-full justify-start gap-4 h-12 text-left transition-all duration-300 group relative overflow-hidden ${activeView === item.id
        ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/25'
        : 'hover:bg-slate-50 text-slate-700 hover:text-slate-900'
        }`}
      onClick={() => {
        setActiveView(item.id);
        setIsMobileMenuOpen(false);
      }}
    >
      {activeView === item.id && (
        <div className="absolute inset-0 bg-gradient-to-r from-blue-400/20 to-blue-600/20 animate-pulse" />
      )}
      <item.icon className={`h-5 w-5 relative z-10 ${activeView === item.id ? 'text-white' : item.color}`} />
      <span className="relative z-10 font-medium">{item.label}</span>
      {activeView === item.id && (
        <div className="absolute right-2 w-2 h-2 bg-white rounded-full animate-pulse" />
      )}
    </Button>
  );

  return (
    <>
      {/* Mobile Menu Button */}
      <div className="md:hidden fixed top-6 left-6 z-50">
        <Button
          variant="outline"
          size="icon"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="bg-white/95 backdrop-blur-sm shadow-xl border-0 hover:shadow-2xl transition-all duration-300"
        >
          {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </div>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Navigation Sidebar */}
      <nav className={`
        fixed md:relative inset-y-0 left-0 z-50 w-80 bg-white/95 backdrop-blur-xl border-r border-slate-200/60
        transform transition-all duration-500 ease-out
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        flex flex-col shadow-2xl md:shadow-xl
      `}>
        {/* Header */}
        <div className="p-8 border-b border-slate-200/60 bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 via-purple-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-400 rounded-full border-2 border-white animate-pulse" />
            </div>
            <div>
              <h2 className="font-bold text-xl text-slate-900">PHIP</h2>
              <p className="text-sm text-slate-600 font-medium">Intelligence Platform</p>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <div className="flex-1 p-6 space-y-2">
          {navItems.map((item) => (
            <NavButton key={item.id} item={item} />
          ))}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-slate-200/60 bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 bg-gradient-to-br from-emerald-400 to-emerald-500 rounded-lg flex items-center justify-center">
              <Zap className="h-4 w-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">AI-Powered</p>
              <p className="text-xs text-slate-600">Version 2.1.0</p>
            </div>
          </div>
          <Button variant="outline" size="sm" className="w-full">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>
        </div>
      </nav>
    </>
  );
};

const Dashboard = ({ onSelectSimulation }) => {
  const [stats, setStats] = useState({
    totalDatasets: 0,
    activeSimulations: 0,
    completedAnalyses: 0,
    dataPoints: 0,
    accuracy: 0,
    predictions: 0
  });
  const [simulations, setSimulations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Generate chart data (this could come from API in the future)
  const chartData = Array.from({ length: 30 }, (_, i) => ({
    day: i + 1,
    infections: Math.floor(Math.random() * 1000) + 500 + Math.sin(i * 0.3) * 200,
    recovered: Math.floor(Math.random() * 800) + 200 + Math.sin(i * 0.2) * 150,
    deaths: Math.floor(Math.random() * 50) + 10 + Math.sin(i * 0.1) * 20
  }));

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load datasets and simulations in parallel
      const [datasetsResponse, simulationsResponse] = await Promise.all([
        ApiService.getDatasets().catch(() => ({ datasets: [] })),
        ApiService.getSimulations().catch(() => ({ simulations: [] }))
      ]);

      const datasets = Array.isArray(datasetsResponse) ? datasetsResponse : datasetsResponse.datasets || [];
      const sims = Array.isArray(simulationsResponse) ? simulationsResponse : simulationsResponse.simulations || [];
      
      setSimulations(sims.slice(0, 3)); // Show top 3 recent simulations

      // Calculate stats
      const completedSims = sims.filter(s => s.status === 'completed');
      const activeSims = sims.filter(s => s.status === 'running');
      
      setStats({
        totalDatasets: datasets.length,
        activeSimulations: activeSims.length,
        completedAnalyses: completedSims.length,
        dataPoints: datasets.reduce((sum, d) => sum + (d.total_records || 0), 0),
        accuracy: completedSims.length > 0 ? 94.2 : 0, // Mock accuracy
        predictions: completedSims.length * 3 // Mock predictions
      });

    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshDashboard = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20">
      <div className="p-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="space-y-2">
            <h1 className="text-4xl font-bold text-slate-900 bg-gradient-to-r from-slate-900 via-blue-900 to-purple-900 bg-clip-text text-transparent">
              Dashboard Overview
            </h1>
            <p className="text-lg text-slate-600 max-w-2xl">
              Monitor your epidemiological models and gain insights from real-time data analysis
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={refreshDashboard}
              disabled={refreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button className="lg:w-auto bg-gradient-to-r from-blue-500 via-blue-600 to-purple-600 hover:from-blue-600 hover:via-blue-700 hover:to-purple-700 text-white border-0 shadow-xl hover:shadow-2xl transition-all duration-300 px-8 py-6 text-lg font-semibold">
              <Plus className="h-5 w-5 mr-3" />
              New Analysis
              <Sparkles className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Total Datasets"
            value={stats.totalDatasets.toLocaleString()}
            change="+12.5%"
            icon={Database}
            color="emerald"
            subtitle="Validated sources"
            loading={loading}
          />
          <MetricCard
            title="Active Simulations"
            value={stats.activeSimulations.toLocaleString()}
            change="+8.2%"
            icon={Activity}
            color="blue"
            subtitle="Running models"
            loading={loading}
          />
          <MetricCard
            title="Predictions Generated"
            value={stats.predictions.toLocaleString()}
            change="+23.1%"
            icon={Brain}
            color="purple"
            subtitle="AI forecasts"
            loading={loading}
          />
          <MetricCard
            title="Model Accuracy"
            value={`${stats.accuracy}%`}
            change="+2.3%"
            icon={TrendingUp}
            color="orange"
            subtitle="Average precision"
            loading={loading}
          />
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          {/* Recent Simulations */}
          <div className="xl:col-span-2">
            <Card className="border-0 shadow-xl bg-white/80 backdrop-blur-sm">
              <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 border-b border-slate-200/60">
                <CardTitle className="flex items-center gap-3 text-xl">
                  <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
                    <Beaker className="h-5 w-5 text-white" />
                  </div>
                  Recent Simulations
                </CardTitle>
                <CardDescription className="text-slate-600">
                  Monitor your latest epidemiological models and their progress
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6 space-y-4">
                {loading ? (
                  <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="p-5 bg-slate-100 rounded-xl animate-pulse">
                        <div className="h-6 bg-slate-200 rounded mb-2" />
                        <div className="h-4 bg-slate-200 rounded w-3/4" />
                      </div>
                    ))}
                  </div>
                ) : simulations.length === 0 ? (
                  <div className="text-center py-8">
                    <Brain className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">No simulations found. Create your first simulation to get started.</p>
                  </div>
                ) : (
                  simulations.map((sim) => (
                    <div key={sim.id} className="group p-5 bg-gradient-to-r from-slate-50/80 to-white rounded-xl border border-slate-200/60 hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                      <div className="flex items-center justify-between mb-4">
                        <div className="space-y-2">
                          <div className="flex items-center gap-3">
                            <h4 className="font-semibold text-slate-900 text-lg">{sim.name}</h4>
                            <StatusBadge status={sim.status} />
                          </div>
                          <div className="flex items-center gap-6 text-sm text-slate-600">
                            <span className="flex items-center gap-2">
                              <Globe className="w-4 h-4" />
                              Model: {sim.model_type?.replace('_', ' ') || 'Unknown'}
                            </span>
                            <span className="flex items-center gap-2">
                              <Clock className="w-4 h-4" />
                              {new Date(sim.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {sim.status === 'running' && (
                            <Button variant="outline" size="sm" className="shadow-md hover:shadow-lg transition-all">
                              <Pause className="h-4 w-4" />
                            </Button>
                          )}
                          {sim.status === 'completed' && (
                            <Button
                              variant="default"
                              size="sm"
                              onClick={() => onSelectSimulation(sim.id)}
                              className="bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 shadow-md hover:shadow-lg transition-all"
                            >
                              View Results
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* Trend Analysis */}
          <Card className="border-0 shadow-xl bg-white/80 backdrop-blur-sm">
            <CardHeader className="bg-gradient-to-r from-emerald-50 to-blue-50 border-b border-slate-200/60">
              <CardTitle className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-emerald-500 to-blue-600 rounded-lg">
                  <LineChart className="h-5 w-5 text-white" />
                </div>
                Trend Analysis
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <ResponsiveContainer width="100%" height={240}>
                <AreaChart data={chartData.slice(-7)}>
                  <defs>
                    <linearGradient id="colorInfections" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      background: 'rgba(255, 255, 255, 0.95)',
                      border: 'none',
                      borderRadius: '12px',
                      boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="infections"
                    stroke="#3B82F6"
                    strokeWidth={3}
                    fillOpacity={1}
                    fill="url(#colorInfections)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Chart */}
        <Card className="border-0 shadow-xl bg-white/80 backdrop-blur-sm">
          <CardHeader className="bg-gradient-to-r from-purple-50 to-blue-50 border-b border-slate-200/60">
            <CardTitle className="text-xl">Epidemiological Trends</CardTitle>
            <CardDescription>
              30-day comprehensive overview of key health metrics and predictions
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            <ResponsiveContainer width="100%" height={400}>
              <RechartsLineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(255, 255, 255, 0.95)',
                    border: 'none',
                    borderRadius: '12px',
                    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Line type="monotone" dataKey="infections" stroke="#EF4444" strokeWidth={3} name="Infections" dot={false} />
                <Line type="monotone" dataKey="recovered" stroke="#10B981" strokeWidth={3} name="Recovered" dot={false} />
                <Line type="monotone" dataKey="deaths" stroke="#6B7280" strokeWidth={3} name="Deaths" dot={false} />
              </RechartsLineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

const AppContent = () => {
  const { isAuthenticated } = useAuth();
  const [activeView, setActiveView] = useState('dashboard');
  const [selectedSimId, setSelectedSimId] = useState(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleSelectSimulation = useCallback((simId) => {
    setSelectedSimId(simId);
    setActiveView('visualize');
  }, []);

  const renderContent = () => {
    switch (activeView) {
      case 'dashboard':
        return <Dashboard onSelectSimulation={handleSelectSimulation} />;
      case 'simulations':
        return <SimulationManagerAPI onSelectSimulation={handleSelectSimulation} />;
      case 'datasets':
        return <DatasetManagerAPI />;
      case 'visualize':
        return <VisualizationDashboard simulationId={selectedSimId} />;
      default:
        return <Dashboard onSelectSimulation={handleSelectSimulation} />;
    }
  };

  if (!isAuthenticated) {
    return <AuthPage />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20">
      <Header />
      <div className="flex">
        <Navigation
          activeView={activeView}
          setActiveView={setActiveView}
          isMobileMenuOpen={isMobileMenuOpen}
          setIsMobileMenuOpen={setIsMobileMenuOpen}
        />
        <main className="flex-1 md:ml-80 transition-all duration-300">
          <ProtectedRoute>
            {renderContent()}
          </ProtectedRoute>
        </main>
      </div>
    </div>
  );
};

function AppAPI() {
  return (
    <AuthProvider>
      <AppContent />
      <Toaster position="top-right" />
    </AuthProvider>
  );
}

export default AppAPI;