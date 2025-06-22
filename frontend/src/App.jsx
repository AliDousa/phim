import React, { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
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
  Clock
} from 'lucide-react';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import SimulationManager from './components/SimulationManager';
import DatasetManager from './components/DatasetManager';
import VisualizationDashboard from './components/VisualizationDashboard';

// Sample data for demonstration
const sampleDashboardData = {
  stats: {
    totalDatasets: 12,
    activeSimulations: 3,
    completedAnalyses: 47,
    dataPoints: 125000
  },
  recentSimulations: [
    { id: 1, name: "COVID-19 Spread Analysis", status: "completed", progress: 100, model: "SEIR" },
    { id: 2, name: "Flu Season Forecast", status: "running", progress: 65, model: "ML" },
    { id: 3, name: "Vaccination Impact Study", status: "pending", progress: 0, model: "Agent-Based" }
  ],
  chartData: Array.from({ length: 30 }, (_, i) => ({
    day: i + 1,
    infections: Math.floor(Math.random() * 1000) + 500,
    recovered: Math.floor(Math.random() * 800) + 200,
    deaths: Math.floor(Math.random() * 50) + 10
  }))
};

const StatusBadge = ({ status }) => {
  const variants = {
    completed: { variant: "default", color: "bg-green-500", icon: CheckCircle },
    running: { variant: "secondary", color: "bg-blue-500", icon: Activity },
    pending: { variant: "outline", color: "bg-gray-500", icon: Clock },
    failed: { variant: "destructive", color: "bg-red-500", icon: AlertCircle }
  };

  const config = variants[status] || variants.pending;
  const IconComponent = config.icon;

  return (
    <Badge variant={config.variant} className="flex items-center gap-1">
      <div className={`w-2 h-2 rounded-full ${config.color}`} />
      <IconComponent className="w-3 h-3" />
      {status}
    </Badge>
  );
};

const MetricCard = ({ title, value, change, icon: Icon, trend = "up" }) => (
  <Card className="hover:shadow-md transition-shadow duration-200">
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
      <Icon className="h-4 w-4 text-gray-400" />
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      {change && (
        <p className={`text-xs flex items-center gap-1 mt-1 ${trend === 'up' ? 'text-green-600' : 'text-red-600'
          }`}>
          <TrendingUp className="h-3 w-3" />
          {change} from last month
        </p>
      )}
    </CardContent>
  </Card>
);

const Navigation = ({ activeView, setActiveView, isMobileMenuOpen, setIsMobileMenuOpen }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'simulations', label: 'Simulations', icon: Beaker },
    { id: 'datasets', label: 'Datasets', icon: Database },
    { id: 'visualize', label: 'Analytics', icon: BarChart3 }
  ];

  const NavButton = ({ item }) => (
    <Button
      variant={activeView === item.id ? 'default' : 'ghost'}
      className="w-full justify-start gap-3 h-11"
      onClick={() => {
        setActiveView(item.id);
        setIsMobileMenuOpen(false);
      }}
    >
      <item.icon className="h-4 w-4" />
      {item.label}
    </Button>
  );

  return (
    <>
      {/* Mobile Menu Button */}
      <div className="md:hidden fixed top-4 left-4 z-50">
        <Button
          variant="outline"
          size="icon"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="bg-white shadow-lg"
        >
          {isMobileMenuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </Button>
      </div>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-40 bg-black/50" onClick={() => setIsMobileMenuOpen(false)} />
      )}

      {/* Navigation Sidebar */}
      <nav className={`
        fixed md:relative inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 
        transform transition-transform duration-200 ease-in-out
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        flex flex-col
      `}>
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Activity className="h-4 w-4 text-white" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900">HealthSim</h2>
              <p className="text-xs text-gray-500">Intelligence Platform</p>
            </div>
          </div>
        </div>

        <div className="flex-1 p-4 space-y-2">
          {navItems.map((item) => (
            <NavButton key={item.id} item={item} />
          ))}
        </div>

        <div className="p-4 border-t border-gray-200">
          <div className="text-xs text-gray-500 text-center">
            Version 2.0.0
          </div>
        </div>
      </nav>
    </>
  );
};

const Dashboard = ({ onSelectSimulation }) => (
  <div className="space-y-6">
    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>
        <p className="text-gray-600">Monitor your epidemiological models and data insights</p>
      </div>
      <Button className="md:w-auto bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700">
        <Plus className="h-4 w-4 mr-2" />
        New Analysis
      </Button>
    </div>

    {/* Metrics Grid */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard
        title="Total Datasets"
        value={sampleDashboardData.stats.totalDatasets.toLocaleString()}
        change="+2.1%"
        icon={Database}
      />
      <MetricCard
        title="Active Simulations"
        value={sampleDashboardData.stats.activeSimulations.toLocaleString()}
        change="+12.5%"
        icon={Activity}
      />
      <MetricCard
        title="Completed Analyses"
        value={sampleDashboardData.stats.completedAnalyses.toLocaleString()}
        change="+8.2%"
        icon={BarChart3}
      />
      <MetricCard
        title="Data Points"
        value={`${Math.round(sampleDashboardData.stats.dataPoints / 1000)}K`}
        change="+15.3%"
        icon={TrendingUp}
      />
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Recent Simulations */}
      <div className="lg:col-span-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Beaker className="h-5 w-5" />
              Active Simulations
            </CardTitle>
            <CardDescription>
              Monitor your running epidemiological models
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {sampleDashboardData.recentSimulations.map((sim) => (
              <div key={sim.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="font-medium text-gray-900">{sim.name}</h4>
                    <StatusBadge status={sim.status} />
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span>Model: {sim.model}</span>
                    {sim.status === 'running' && (
                      <div className="flex items-center gap-2">
                        <Progress value={sim.progress} className="w-20 h-1" />
                        <span>{sim.progress}%</span>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm">
                    {sim.status === 'running' ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  </Button>
                  {sim.status === 'completed' && (
                    <Button variant="ghost" size="sm" onClick={() => onSelectSimulation(sim.id)}>
                      View Results
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Quick Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <LineChart className="h-5 w-5" />
            Trend Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={sampleDashboardData.chartData.slice(-7)}>
              <defs>
                <linearGradient id="colorInfections" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="infections"
                stroke="#3B82F6"
                fillOpacity={1}
                fill="url(#colorInfections)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>

    {/* Detailed Chart */}
    <Card>
      <CardHeader>
        <CardTitle>Epidemiological Trends</CardTitle>
        <CardDescription>
          30-day overview of key health metrics
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <RechartsLineChart data={sampleDashboardData.chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="day" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="infections" stroke="#EF4444" strokeWidth={2} name="Infections" />
            <Line type="monotone" dataKey="recovered" stroke="#10B981" strokeWidth={2} name="Recovered" />
            <Line type="monotone" dataKey="deaths" stroke="#6B7280" strokeWidth={2} name="Deaths" />
          </RechartsLineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  </div>
);

function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [selectedSimId, setSelectedSimId] = useState(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Mock auth token
  if (!localStorage.getItem('authToken')) {
    localStorage.setItem('authToken', 'dummy-dev-token');
  }

  const handleSelectSimulation = useCallback((simId) => {
    setSelectedSimId(simId);
    setActiveView('visualize');
  }, []);

  const renderContent = () => {
    switch (activeView) {
      case 'dashboard':
        return <Dashboard onSelectSimulation={handleSelectSimulation} />;
      case 'simulations':
        return <SimulationManager onSelectSimulation={handleSelectSimulation} />;
      case 'datasets':
        return <DatasetManager />;
      case 'visualize':
        return <VisualizationDashboard simulationId={selectedSimId} />;
      default:
        return <Dashboard onSelectSimulation={handleSelectSimulation} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation
        activeView={activeView}
        setActiveView={setActiveView}
        isMobileMenuOpen={isMobileMenuOpen}
        setIsMobileMenuOpen={setIsMobileMenuOpen}
      />

      <main className="md:ml-64 p-4 md:p-6 pt-16 md:pt-6">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;