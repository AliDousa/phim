import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  ComposedChart
} from 'recharts';
import { Toaster, toast } from 'sonner';
import {
  Sigma,
  TrendingUp,
  Activity,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  Brain,
  Target,
  Globe,
  Zap,
  Download,
  Share,
  Settings,
  Play,
  Pause,
  RotateCcw,
  Maximize,
  Calendar,
  MapPin,
  Users,
  Clock,
  Sparkles,
  Eye,
  ArrowUp,
  ArrowDown,
  TrendingDown,
  Info,
  Filter,
  RefreshCw
} from 'lucide-react';

// Enhanced mock data for different model types
const generateMockResults = (modelType, simulationId) => {
  const baseData = Array.from({ length: 90 }, (_, i) => ({
    day: i + 1,
    date: new Date(2024, 0, i + 1).toLocaleDateString(),
    susceptible: Math.max(0, 100000 - i * 500 - Math.random() * 1000),
    exposed: Math.max(0, 200 + Math.sin(i * 0.1) * 100 + Math.random() * 50),
    infectious: Math.max(0, 500 + Math.sin(i * 0.15) * 200 + Math.random() * 100),
    recovered: Math.min(100000, i * 400 + Math.random() * 200),
    deaths: Math.min(5000, i * 10 + Math.random() * 5),
    newCases: Math.max(0, 100 + Math.sin(i * 0.2) * 50 + Math.random() * 30),
    hospitalizations: Math.max(0, 50 + Math.sin(i * 0.12) * 25 + Math.random() * 15),
    icu: Math.max(0, 10 + Math.sin(i * 0.18) * 8 + Math.random() * 5),
    tests: Math.max(0, 500 + Math.random() * 200),
    positivityRate: Math.min(1, Math.max(0, 0.05 + Math.sin(i * 0.1) * 0.03 + Math.random() * 0.02)),
    rEffective: Math.max(0.3, 1.2 - i * 0.008 + Math.sin(i * 0.05) * 0.2 + Math.random() * 0.1)
  }));

  const metrics = {
    r0: 2.8 + Math.random() * 0.4,
    rEffective: baseData[baseData.length - 1].rEffective,
    peakDay: 45 + Math.floor(Math.random() * 20),
    maxInfections: Math.max(...baseData.map(d => d.infectious)),
    totalInfected: baseData[baseData.length - 1].recovered + baseData[baseData.length - 1].deaths,
    finalMortality: (baseData[baseData.length - 1].deaths / (baseData[baseData.length - 1].recovered + baseData[baseData.length - 1].deaths)) * 100,
    peakHospitalizations: Math.max(...baseData.map(d => d.hospitalizations)),
    attackRate: (baseData[baseData.length - 1].recovered + baseData[baseData.length - 1].deaths) / 100000 * 100,
    doubling_time: 7 + Math.random() * 5,
    generation_time: 5 + Math.random() * 2
  };

  if (modelType === 'ml_forecast') {
    return {
      type: 'ml_forecast',
      data: baseData.slice(-30).map((d, i) => ({
        ...d,
        prediction: d.newCases * (0.9 + Math.random() * 0.2),
        confidence_lower: d.newCases * 0.7,
        confidence_upper: d.newCases * 1.3,
        forecast_day: i + 1
      })),
      metrics: {
        ...metrics,
        mae: 12.5 + Math.random() * 5,
        rmse: 18.2 + Math.random() * 7,
        r2: 0.85 + Math.random() * 0.1,
        mape: 8.5 + Math.random() * 3
      },
      featureImportance: [
        { feature: 'Previous Cases', importance: 0.35 },
        { feature: 'Day of Week', importance: 0.18 },
        { feature: 'Temperature', importance: 0.15 },
        { feature: 'Mobility', importance: 0.12 },
        { feature: 'Policy Index', importance: 0.10 },
        { feature: 'Testing Rate', importance: 0.10 }
      ]
    };
  }

  return {
    type: modelType,
    data: baseData,
    metrics,
    interventions: [
      { day: 20, type: 'social_distancing', intensity: 0.6, label: 'Social Distancing' },
      { day: 40, type: 'mask_mandate', intensity: 0.8, label: 'Mask Mandate' },
      { day: 60, type: 'vaccination', intensity: 0.4, label: 'Vaccination Campaign' }
    ]
  };
};

const MetricCard = ({ title, value, change, changeType, icon: Icon, subtitle, color = "blue", size = "default" }) => {
  const colorClasses = {
    blue: {
      bg: "from-blue-500/10 via-blue-500/5 to-transparent",
      icon: "bg-gradient-to-br from-blue-500 to-blue-600 text-white",
      text: "text-blue-600"
    },
    emerald: {
      bg: "from-emerald-500/10 via-emerald-500/5 to-transparent",
      icon: "bg-gradient-to-br from-emerald-500 to-emerald-600 text-white",
      text: "text-emerald-600"
    },
    red: {
      bg: "from-red-500/10 via-red-500/5 to-transparent",
      icon: "bg-gradient-to-br from-red-500 to-red-600 text-white",
      text: "text-red-600"
    },
    purple: {
      bg: "from-purple-500/10 via-purple-500/5 to-transparent",
      icon: "bg-gradient-to-br from-purple-500 to-purple-600 text-white",
      text: "text-purple-600"
    }
  };

  const sizeClasses = size === "large" ? "p-8" : "p-6";
  const titleSize = size === "large" ? "text-base" : "text-sm";
  const valueSize = size === "large" ? "text-4xl" : "text-2xl";
  const iconSize = size === "large" ? "h-8 w-8" : "h-6 w-6";

  const classes = colorClasses[color];

  return (
    <Card className="group relative overflow-hidden border-0 shadow-xl hover:shadow-2xl transition-all duration-500 hover:-translate-y-1 bg-white/90 backdrop-blur-sm">
      <div className={`absolute inset-0 bg-gradient-to-br ${classes.bg} opacity-60`} />
      <div className="absolute -top-4 -right-4 w-20 h-20 opacity-10 rotate-12">
        <Icon className="w-full h-full" />
      </div>

      <CardContent className={`relative ${sizeClasses}`}>
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className={`${titleSize} font-semibold text-slate-600 uppercase tracking-wider`}>{title}</p>
            {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
          </div>
          <div className={`p-3 rounded-xl ${classes.icon} shadow-lg group-hover:scale-110 transition-transform duration-300`}>
            <Icon className={iconSize} />
          </div>
        </div>

        <div className={`${valueSize} font-bold text-slate-900 mb-2 group-hover:scale-105 transition-transform duration-300`}>
          {value}
        </div>

        {change && (
          <div className={`flex items-center gap-2 text-sm ${changeType === 'positive' ? 'text-emerald-600' : changeType === 'negative' ? 'text-red-600' : 'text-slate-600'}`}>
            {changeType === 'positive' && <ArrowUp className="h-4 w-4" />}
            {changeType === 'negative' && <ArrowDown className="h-4 w-4" />}
            {changeType === 'neutral' && <TrendingUp className="h-4 w-4" />}
            <span className="font-semibold">{change}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const ChartCard = ({ title, children, controls, fullscreen = false }) => {
  const [isFullscreen, setIsFullscreen] = useState(false);

  return (
    <Card className={`border-0 shadow-xl bg-white/90 backdrop-blur-sm ${isFullscreen ? 'fixed inset-4 z-50' : ''}`}>
      <CardHeader className="bg-gradient-to-r from-slate-50 to-blue-50 border-b border-slate-200/60">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{title}</CardTitle>
          <div className="flex items-center gap-2">
            {controls}
            {fullscreen && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsFullscreen(!isFullscreen)}
              >
                <Maximize className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className={`${isFullscreen ? 'p-8' : 'p-6'}`}>
        {children}
      </CardContent>
      {isFullscreen && (
        <div className="absolute top-4 right-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsFullscreen(false)}
          >
            ✕
          </Button>
        </div>
      )}
    </Card>
  );
};

const InterventionOverlay = ({ interventions, width, height, xScale }) => {
  if (!interventions || !xScale) return null;

  return (
    <g>
      {interventions.map((intervention, index) => (
        <g key={index}>
          <line
            x1={xScale(intervention.day)}
            y1={0}
            x2={xScale(intervention.day)}
            y2={height}
            stroke="#8B5CF6"
            strokeWidth={2}
            strokeDasharray="5,5"
            opacity={0.7}
          />
          <text
            x={xScale(intervention.day) + 5}
            y={20}
            fill="#8B5CF6"
            fontSize={12}
            fontWeight="bold"
          >
            {intervention.label}
          </text>
        </g>
      ))}
    </g>
  );
};

export default function VisualizationDashboard({ simulationId }) {
  const [simulation, setSimulation] = useState(null);
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [timeRange, setTimeRange] = useState([1, 90]);
  const [selectedMetrics, setSelectedMetrics] = useState(['infectious', 'recovered']);
  const [showInterventions, setShowInterventions] = useState(true);
  const [chartType, setChartType] = useState('line');

  useEffect(() => {
    if (!simulationId) {
      setIsLoading(false);
      return;
    }

    const fetchSimulationData = async () => {
      setIsLoading(true);
      try {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Mock simulation data
        const mockSim = {
          id: simulationId,
          name: "COVID-19 Variant Analysis",
          description: "Advanced SEIR model analyzing new variant spread patterns",
          model_type: "seir",
          status: "completed",
          created_at: "2024-06-20T10:00:00Z",
          parameters: {
            population: 100000,
            beta: 0.3,
            sigma: 0.2,
            gamma: 0.1
          }
        };

        const mockResults = generateMockResults(mockSim.model_type, simulationId);

        setSimulation(mockSim);
        setResults(mockResults);
      } catch (error) {
        toast.error('Failed to load simulation results');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSimulationData();
  }, [simulationId]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20 p-8">
        <div className="space-y-6">
          <Skeleton className="h-12 w-1/2" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    );
  }

  if (!simulation || !results) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20 flex items-center justify-center">
        <div className="text-center">
          <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
            <Brain className="h-12 w-12 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">No Simulation Selected</h2>
          <p className="text-slate-600 max-w-md">
            Please select a completed simulation from the Simulation Manager to view detailed results and analytics.
          </p>
        </div>
      </div>
    );
  }

  const filteredData = results.data.filter(d => d.day >= timeRange[0] && d.day <= timeRange[1]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20">
      <Toaster richColors position="top-right" />

      <div className="p-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 via-blue-900 to-purple-900 bg-clip-text text-transparent">
                {simulation.name}
              </h1>
              <Badge className="bg-emerald-500 text-white border-0 px-3 py-1">
                <CheckCircle className="w-3 h-3 mr-1" />
                Completed
              </Badge>
            </div>
            <p className="text-lg text-slate-600 max-w-3xl">{simulation.description}</p>
            <div className="flex items-center gap-4 text-sm text-slate-500">
              <span className="flex items-center gap-1">
                <Brain className="w-4 h-4" />
                {simulation.model_type.toUpperCase()} Model
              </span>
              <span className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                {new Date(simulation.created_at).toLocaleDateString()}
              </span>
              <span className="flex items-center gap-1">
                <Users className="w-4 h-4" />
                Population: {simulation.parameters?.population?.toLocaleString()}
              </span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <Button variant="outline" className="shadow-lg">
              <Download className="w-4 h-4 mr-2" />
              Export Results
            </Button>
            <Button variant="outline" className="shadow-lg">
              <Share className="w-4 h-4 mr-2" />
              Share Analysis
            </Button>
            <Button className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white border-0 shadow-xl">
              <RefreshCw className="w-4 h-4 mr-2" />
              Re-run Simulation
            </Button>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="R₀ (Basic Reproduction)"
            value={results.metrics.r0?.toFixed(2)}
            change={results.metrics.r0 > 1 ? "Above threshold" : "Below threshold"}
            changeType={results.metrics.r0 > 1 ? "negative" : "positive"}
            icon={Sigma}
            color={results.metrics.r0 > 1 ? "red" : "emerald"}
            subtitle="Reproduction number"
          />
          <MetricCard
            title="Peak Infections"
            value={results.metrics.maxInfections?.toLocaleString()}
            change={`Day ${results.metrics.peakDay}`}
            changeType="neutral"
            icon={TrendingUp}
            color="purple"
            subtitle="Maximum daily infections"
          />
          <MetricCard
            title="Attack Rate"
            value={`${results.metrics.attackRate?.toFixed(1)}%`}
            change={`${results.metrics.totalInfected?.toLocaleString()} total`}
            changeType="neutral"
            icon={Target}
            color="blue"
            subtitle="Population infected"
          />
          <MetricCard
            title="Current R(t)"
            value={results.metrics.rEffective?.toFixed(2)}
            change={results.metrics.rEffective < results.metrics.r0 ? "Decreasing" : "Stable"}
            changeType={results.metrics.rEffective < results.metrics.r0 ? "positive" : "neutral"}
            icon={Activity}
            color={results.metrics.rEffective < 1 ? "emerald" : "red"}
            subtitle="Effective reproduction"
          />
        </div>

        {/* Controls */}
        <Card className="border-0 shadow-xl bg-white/90 backdrop-blur-sm">
          <CardHeader className="bg-gradient-to-r from-slate-50 to-blue-50 border-b border-slate-200/60">
            <CardTitle className="flex items-center gap-3">
              <Settings className="h-5 w-5" />
              Visualization Controls
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="space-y-2">
                <Label>Time Range (Days)</Label>
                <Slider
                  value={timeRange}
                  onValueChange={setTimeRange}
                  min={1}
                  max={90}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-slate-500">
                  <span>Day {timeRange[0]}</span>
                  <span>Day {timeRange[1]}</span>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Chart Type</Label>
                <Select value={chartType} onValueChange={setChartType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="line">Line Chart</SelectItem>
                    <SelectItem value="area">Area Chart</SelectItem>
                    <SelectItem value="bar">Bar Chart</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Display Options</Label>
                <div className="flex items-center space-x-2">
                  <Switch
                    checked={showInterventions}
                    onCheckedChange={setShowInterventions}
                  />
                  <Label className="text-sm">Show Interventions</Label>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Quick Filters</Label>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => setTimeRange([1, 30])}>
                    First Month
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => setTimeRange([30, 60])}>
                    Peak Period
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Main Visualization */}
        <ChartCard
          title="Epidemic Dynamics Over Time"
          fullscreen={true}
          controls={
            <div className="flex gap-2">
              <Badge variant="outline">
                <Eye className="w-3 h-3 mr-1" />
                {filteredData.length} days
              </Badge>
            </div>
          }
        >
          <ResponsiveContainer width="100%" height={500}>
            {chartType === 'area' ? (
              <AreaChart data={filteredData}>
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
                <Legend />
                <Area type="monotone" dataKey="susceptible" stackId="1" stroke="#94A3B8" fill="#94A3B8" fillOpacity={0.6} name="Susceptible" />
                <Area type="monotone" dataKey="exposed" stackId="1" stroke="#F59E0B" fill="#F59E0B" fillOpacity={0.6} name="Exposed" />
                <Area type="monotone" dataKey="infectious" stackId="1" stroke="#EF4444" fill="#EF4444" fillOpacity={0.6} name="Infectious" />
                <Area type="monotone" dataKey="recovered" stackId="1" stroke="#10B981" fill="#10B981" fillOpacity={0.6} name="Recovered" />
              </AreaChart>
            ) : chartType === 'bar' ? (
              <BarChart data={filteredData.filter((_, i) => i % 5 === 0)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="newCases" fill="#3B82F6" name="New Cases" />
                <Bar dataKey="hospitalizations" fill="#8B5CF6" name="Hospitalizations" />
                <Bar dataKey="deaths" fill="#EF4444" name="Deaths" />
              </BarChart>
            ) : (
              <LineChart data={filteredData}>
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
                <Legend />
                <Line type="monotone" dataKey="infectious" stroke="#EF4444" strokeWidth={3} name="Infectious" dot={false} />
                <Line type="monotone" dataKey="recovered" stroke="#10B981" strokeWidth={3} name="Recovered" dot={false} />
                <Line type="monotone" dataKey="exposed" stroke="#F59E0B" strokeWidth={2} name="Exposed" dot={false} strokeDasharray="5 5" />
                <Line type="monotone" dataKey="deaths" stroke="#6B7280" strokeWidth={2} name="Deaths" dot={false} />
              </LineChart>
            )}
          </ResponsiveContainer>
        </ChartCard>

        {/* Secondary Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* R(t) Evolution */}
          <ChartCard title="Effective Reproduction Number R(t)">
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={filteredData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line type="monotone" dataKey="rEffective" stroke="#8B5CF6" strokeWidth={3} name="R(t)" />
                <Line
                  type="monotone"
                  dataKey={() => 1}
                  stroke="#EF4444"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="Threshold (R=1)"
                  dot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Testing and Positivity */}
          <ChartCard title="Testing Metrics">
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={filteredData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar yAxisId="left" dataKey="tests" fill="#3B82F6" name="Daily Tests" opacity={0.7} />
                <Line yAxisId="right" type="monotone" dataKey="positivityRate" stroke="#EF4444" strokeWidth={3} name="Positivity Rate" />
              </ComposedChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* ML Model Specific Charts */}
        {results.type === 'ml_forecast' && (
          <div className="space-y-8">
            <ChartCard title="Forecast vs Actual">
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={results.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis dataKey="forecast_day" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Area dataKey="confidence_upper" stroke="none" fill="#3B82F6" fillOpacity={0.1} />
                  <Area dataKey="confidence_lower" stroke="none" fill="#ffffff" fillOpacity={1} />
                  <Line type="monotone" dataKey="newCases" stroke="#10B981" strokeWidth={3} name="Actual" />
                  <Line type="monotone" dataKey="prediction" stroke="#3B82F6" strokeWidth={3} name="Prediction" strokeDasharray="5 5" />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <ChartCard title="Feature Importance">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={results.featureImportance} layout="horizontal">
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis type="number" tick={{ fontSize: 12 }} />
                    <YAxis dataKey="feature" type="category" tick={{ fontSize: 12 }} width={100} />
                    <Tooltip />
                    <Bar dataKey="importance" fill="#8B5CF6" />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <div className="grid grid-cols-2 gap-4">
                <MetricCard
                  title="MAE"
                  value={results.metrics.mae?.toFixed(1)}
                  subtitle="Mean Absolute Error"
                  icon={Target}
                  color="blue"
                  size="default"
                />
                <MetricCard
                  title="R² Score"
                  value={results.metrics.r2?.toFixed(3)}
                  subtitle="Model Fit"
                  icon={CheckCircle}
                  color="emerald"
                  size="default"
                />
                <MetricCard
                  title="RMSE"
                  value={results.metrics.rmse?.toFixed(1)}
                  subtitle="Root Mean Squared Error"
                  icon={BarChart3}
                  color="purple"
                  size="default"
                />
                <MetricCard
                  title="MAPE"
                  value={`${results.metrics.mape?.toFixed(1)}%`}
                  subtitle="Mean Absolute Percentage Error"
                  icon={TrendingUp}
                  color="red"
                  size="default"
                />
              </div>
            </div>
          </div>
        )}

        {/* Model Parameters */}
        <Card className="border-0 shadow-xl bg-white/90 backdrop-blur-sm">
          <CardHeader className="bg-gradient-to-r from-purple-50 to-blue-50 border-b border-slate-200/60">
            <CardTitle className="flex items-center gap-3">
              <Brain className="h-5 w-5" />
              Model Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {Object.entries(simulation.parameters || {}).map(([key, value]) => (
                <div key={key} className="text-center p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm font-medium text-slate-600 uppercase tracking-wide">{key.replace('_', ' ')}</p>
                  <p className="text-xl font-bold text-slate-900 mt-1">{typeof value === 'number' ? value.toLocaleString() : value}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}