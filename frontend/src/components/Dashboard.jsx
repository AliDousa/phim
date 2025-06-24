import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
    Activity,
    Beaker,
    Database,
    PlusCircle,
    ArrowRight,
    TrendingUp,
    TrendingDown,
    Brain,
    Zap,
    Globe,
    Clock,
    CheckCircle,
    AlertTriangle,
    Sparkles,
    BarChart3,
    Users,
    Calendar,
    Target
} from 'lucide-react';
import { Toaster, toast } from 'sonner';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, PieChart, Pie, Cell } from 'recharts';

// Enhanced mock data for demonstration
const mockData = {
    stats: {
        datasets: 24,
        simulations: 18,
        running: 3,
        accuracy: 94.7,
        predictions: 156,
        activeUsers: 42
    },
    recentSimulations: [
        {
            id: 1,
            name: "COVID-19 Variant Tracking",
            status: "completed",
            model: "SEIR-Extended",
            accuracy: 96.2,
            created_at: "2024-06-20T10:00:00Z",
            duration: "2h 34m",
            dataPoints: 50000
        },
        {
            id: 2,
            name: "Seasonal Flu Forecast 2024",
            status: "running",
            model: "ML-Ensemble",
            accuracy: 92.8,
            created_at: "2024-06-22T14:30:00Z",
            duration: "45m",
            dataPoints: 25000,
            progress: 67
        },
        {
            id: 3,
            name: "Vaccination Campaign Impact",
            status: "pending",
            model: "Agent-Based",
            accuracy: null,
            created_at: "2024-06-23T09:15:00Z",
            duration: null,
            dataPoints: 75000
        }
    ],
    chartData: Array.from({ length: 30 }, (_, i) => ({
        day: i + 1,
        infections: Math.floor(Math.random() * 1000) + 300 + Math.sin(i * 0.2) * 200,
        recovered: Math.floor(Math.random() * 800) + 150 + Math.sin(i * 0.15) * 150,
        deaths: Math.floor(Math.random() * 30) + 5 + Math.sin(i * 0.1) * 10,
        vaccinated: Math.floor(Math.random() * 500) + 100 + i * 20
    })),
    modelPerformance: [
        { name: 'SEIR', value: 35, color: '#3B82F6' },
        { name: 'ML-Based', value: 28, color: '#8B5CF6' },
        { name: 'Agent-Based', value: 22, color: '#10B981' },
        { name: 'Hybrid', value: 15, color: '#F59E0B' }
    ]
};

const getStatusBadgeVariant = (status) => {
    const variants = {
        completed: {
            variant: "default",
            className: "bg-emerald-500 text-emerald-50 border-0 shadow-lg shadow-emerald-500/25",
            icon: CheckCircle
        },
        running: {
            variant: "secondary",
            className: "bg-blue-500 text-blue-50 border-0 shadow-lg shadow-blue-500/25 animate-pulse",
            icon: Activity
        },
        pending: {
            variant: "outline",
            className: "bg-slate-500 text-slate-50 border-0 shadow-lg shadow-slate-500/25",
            icon: Clock
        },
        failed: {
            variant: "destructive",
            className: "bg-red-500 text-red-50 border-0 shadow-lg shadow-red-500/25",
            icon: AlertTriangle
        }
    };
    return variants[status] || variants.pending;
};

const StatCard = ({ title, value, change, changeType, icon: Icon, subtitle, color = "blue" }) => {
    const colorClasses = {
        blue: {
            bg: "from-blue-500/10 via-blue-500/5 to-transparent",
            border: "border-blue-200/30",
            icon: "bg-gradient-to-br from-blue-500 to-blue-600 text-white",
            text: "text-blue-600",
            accent: "text-blue-500"
        },
        emerald: {
            bg: "from-emerald-500/10 via-emerald-500/5 to-transparent",
            border: "border-emerald-200/30",
            icon: "bg-gradient-to-br from-emerald-500 to-emerald-600 text-white",
            text: "text-emerald-600",
            accent: "text-emerald-500"
        },
        purple: {
            bg: "from-purple-500/10 via-purple-500/5 to-transparent",
            border: "border-purple-200/30",
            icon: "bg-gradient-to-br from-purple-500 to-purple-600 text-white",
            text: "text-purple-600",
            accent: "text-purple-500"
        },
        orange: {
            bg: "from-orange-500/10 via-orange-500/5 to-transparent",
            border: "border-orange-200/30",
            icon: "bg-gradient-to-br from-orange-500 to-orange-600 text-white",
            text: "text-orange-600",
            accent: "text-orange-500"
        }
    };

    const classes = colorClasses[color];

    return (
        <Card className={`group relative overflow-hidden border-0 shadow-xl hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 ${classes.border} bg-white/80 backdrop-blur-sm`}>
            {/* Background Gradient */}
            <div className={`absolute inset-0 bg-gradient-to-br ${classes.bg} opacity-60`} />

            {/* Decorative Background Icon */}
            <div className="absolute -top-4 -right-4 w-24 h-24 opacity-10 rotate-12">
                <Icon className="w-full h-full" />
            </div>

            <CardHeader className="relative pb-3">
                <div className="flex items-start justify-between">
                    <div className="space-y-1">
                        <CardTitle className="text-sm font-semibold text-slate-600 uppercase tracking-wider">
                            {title}
                        </CardTitle>
                        {subtitle && (
                            <p className="text-xs text-slate-500 font-medium">{subtitle}</p>
                        )}
                    </div>
                    <div className={`p-3 rounded-xl ${classes.icon} shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                        <Icon className="h-6 w-6" />
                    </div>
                </div>
            </CardHeader>

            <CardContent className="relative pt-0">
                <div className="text-3xl font-bold text-slate-900 mb-3 group-hover:scale-105 transition-transform duration-300">
                    {value}
                </div>
                {change && (
                    <div className={`flex items-center gap-2 text-sm ${changeType === 'positive' ? 'text-emerald-600' : 'text-red-600'}`}>
                        {changeType === 'positive' ? (
                            <TrendingUp className="h-4 w-4" />
                        ) : (
                            <TrendingDown className="h-4 w-4" />
                        )}
                        <span className="font-semibold">{change}</span>
                        <span className="text-slate-500">vs last month</span>
                    </div>
                )}
            </CardContent>
        </Card>
    );
};

const SimulationCard = ({ simulation, onAction }) => {
    const statusConfig = getStatusBadgeVariant(simulation.status);
    const StatusIcon = statusConfig.icon;

    return (
        <Card className="group relative overflow-hidden border-0 shadow-xl hover:shadow-2xl transition-all duration-500 hover:-translate-y-1 bg-white/90 backdrop-blur-sm">
            {/* Status Indicator Bar */}
            <div className={`absolute top-0 left-0 right-0 h-1 ${simulation.status === 'completed' ? 'bg-emerald-500' :
                simulation.status === 'running' ? 'bg-blue-500' :
                    simulation.status === 'pending' ? 'bg-slate-400' : 'bg-red-500'
                }`} />

            <CardHeader className="pb-4">
                <div className="flex items-start justify-between">
                    <div className="space-y-2 flex-1">
                        <div className="flex items-center gap-3">
                            <CardTitle className="text-lg font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                                {simulation.name}
                            </CardTitle>
                            <Badge className={statusConfig.className}>
                                <StatusIcon className="w-3 h-3 mr-1" />
                                {simulation.status}
                            </Badge>
                        </div>

                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div className="flex items-center gap-2 text-slate-600">
                                <Brain className="w-4 h-4 text-purple-500" />
                                <span>{simulation.model}</span>
                            </div>
                            <div className="flex items-center gap-2 text-slate-600">
                                <Calendar className="w-4 h-4 text-blue-500" />
                                <span>{new Date(simulation.created_at).toLocaleDateString()}</span>
                            </div>
                            {simulation.accuracy && (
                                <div className="flex items-center gap-2 text-slate-600">
                                    <Target className="w-4 h-4 text-emerald-500" />
                                    <span>{simulation.accuracy}% accuracy</span>
                                </div>
                            )}
                            <div className="flex items-center gap-2 text-slate-600">
                                <Database className="w-4 h-4 text-orange-500" />
                                <span>{simulation.dataPoints.toLocaleString()} points</span>
                            </div>
                        </div>
                    </div>
                </div>
            </CardHeader>

            <CardContent className="pt-0">
                {simulation.status === 'running' && simulation.progress && (
                    <div className="mb-4 space-y-2">
                        <div className="flex justify-between text-sm font-medium">
                            <span className="text-slate-600">Progress</span>
                            <span className="text-blue-600">{simulation.progress}%</span>
                        </div>
                        <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-500 relative"
                                style={{ width: `${simulation.progress}%` }}
                            >
                                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse" />
                            </div>
                        </div>
                    </div>
                )}

                <div className="flex items-center gap-3">
                    {simulation.status === 'completed' && (
                        <Button
                            onClick={() => onAction('view', simulation.id)}
                            className="bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white border-0 shadow-lg hover:shadow-xl transition-all"
                        >
                            <ArrowRight className="w-4 h-4 mr-2" />
                            View Results
                        </Button>
                    )}
                    {simulation.status === 'running' && (
                        <Button
                            variant="outline"
                            onClick={() => onAction('pause', simulation.id)}
                            className="shadow-md hover:shadow-lg transition-all"
                        >
                            <Activity className="w-4 h-4 mr-2" />
                            Monitor
                        </Button>
                    )}
                    {simulation.status === 'pending' && (
                        <Button
                            onClick={() => onAction('start', simulation.id)}
                            className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white border-0 shadow-lg hover:shadow-xl transition-all"
                        >
                            <Zap className="w-4 h-4 mr-2" />
                            Start
                        </Button>
                    )}
                </div>
            </CardContent>
        </Card>
    );
};

export default function Dashboard({ setActiveView, onSelectSimulation }) {
    const [stats, setStats] = useState(mockData.stats);
    const [recentSimulations, setRecentSimulations] = useState(mockData.recentSimulations);
    const [isLoading, setIsLoading] = useState(false);

    // Simulate real-time updates for running simulations
    useEffect(() => {
        const interval = setInterval(() => {
            setRecentSimulations(prev => prev.map(sim => {
                if (sim.status === 'running' && sim.progress < 100) {
                    return { ...sim, progress: Math.min(sim.progress + Math.random() * 5, 100) };
                }
                return sim;
            }));
        }, 3000);

        return () => clearInterval(interval);
    }, []);

    const handleSimulationAction = (action, simulationId) => {
        switch (action) {
            case 'view':
                onSelectSimulation?.(simulationId);
                break;
            case 'pause':
                toast.info('Simulation monitoring dashboard opened');
                break;
            case 'start':
                toast.success('Simulation started successfully');
                break;
            default:
                break;
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20">
            <Toaster richColors position="top-right" />

            <div className="p-8 space-y-8 animate-fade-in">
                {/* Header Section */}
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                    <div className="space-y-3">
                        <h1 className="text-5xl font-bold bg-gradient-to-r from-slate-900 via-blue-900 to-purple-900 bg-clip-text text-transparent leading-tight">
                            Intelligence Dashboard
                        </h1>
                        <p className="text-xl text-slate-600 max-w-3xl leading-relaxed">
                            Real-time insights from your epidemiological models and predictive analytics
                        </p>
                    </div>

                    <div className="flex flex-col sm:flex-row gap-3">
                        <Button
                            variant="outline"
                            onClick={() => setActiveView('datasets')}
                            className="shadow-lg hover:shadow-xl transition-all border-slate-200"
                        >
                            <Database className="h-5 w-5 mr-2" />
                            Manage Data
                        </Button>
                        <Button
                            onClick={() => setActiveView('simulations')}
                            className="bg-gradient-to-r from-blue-500 via-blue-600 to-purple-600 hover:from-blue-600 hover:via-blue-700 hover:to-purple-700 text-white border-0 shadow-xl hover:shadow-2xl transition-all px-8 py-6 text-lg font-semibold"
                        >
                            <PlusCircle className="h-5 w-5 mr-3" />
                            New Simulation
                            <Sparkles className="h-4 w-4 ml-2" />
                        </Button>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    <StatCard
                        title="Total Datasets"
                        value={stats.datasets}
                        change="+12.5%"
                        changeType="positive"
                        icon={Database}
                        color="emerald"
                        subtitle="Validated sources"
                    />
                    <StatCard
                        title="Active Simulations"
                        value={stats.simulations}
                        change="+8.2%"
                        changeType="positive"
                        icon={Beaker}
                        color="blue"
                        subtitle="Running models"
                    />
                    <StatCard
                        title="AI Predictions"
                        value={stats.predictions}
                        change="+23.1%"
                        changeType="positive"
                        icon={Brain}
                        color="purple"
                        subtitle="Generated forecasts"
                    />
                    <StatCard
                        title="Model Accuracy"
                        value={`${stats.accuracy}%`}
                        change="+2.3%"
                        changeType="positive"
                        icon={Target}
                        color="orange"
                        subtitle="Average precision"
                    />
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                    {/* Recent Simulations */}
                    <div className="xl:col-span-2 space-y-6">
                        <Card className="border-0 shadow-xl bg-white/90 backdrop-blur-sm">
                            <CardHeader className="bg-gradient-to-r from-blue-50 via-purple-50 to-blue-50 border-b border-slate-200/60 rounded-t-lg">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="flex items-center gap-3 text-xl">
                                            <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl shadow-lg">
                                                <Activity className="h-5 w-5 text-white" />
                                            </div>
                                            Active Simulations
                                        </CardTitle>
                                        <CardDescription className="text-slate-600 mt-1">
                                            Monitor your epidemiological models and their real-time progress
                                        </CardDescription>
                                    </div>
                                    <Badge className="bg-blue-100 text-blue-700 border-0">
                                        {stats.running} Running
                                    </Badge>
                                </div>
                            </CardHeader>
                            <CardContent className="p-6">
                                <div className="space-y-4">
                                    {recentSimulations.map((simulation) => (
                                        <SimulationCard
                                            key={simulation.id}
                                            simulation={simulation}
                                            onAction={handleSimulationAction}
                                        />
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Analytics Panel */}
                    <div className="space-y-6">
                        {/* Model Distribution */}
                        <Card className="border-0 shadow-xl bg-white/90 backdrop-blur-sm">
                            <CardHeader className="bg-gradient-to-r from-emerald-50 to-blue-50 border-b border-slate-200/60 rounded-t-lg">
                                <CardTitle className="flex items-center gap-3">
                                    <div className="p-2 bg-gradient-to-br from-emerald-500 to-blue-600 rounded-xl shadow-lg">
                                        <BarChart3 className="h-5 w-5 text-white" />
                                    </div>
                                    Model Usage
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-6">
                                <ResponsiveContainer width="100%" height={200}>
                                    <PieChart>
                                        <Pie
                                            data={mockData.modelPerformance}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={40}
                                            outerRadius={80}
                                            paddingAngle={5}
                                            dataKey="value"
                                        >
                                            {mockData.modelPerformance.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip
                                            contentStyle={{
                                                background: 'rgba(255, 255, 255, 0.95)',
                                                border: 'none',
                                                borderRadius: '12px',
                                                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
                                            }}
                                        />
                                    </PieChart>
                                </ResponsiveContainer>

                                <div className="space-y-2 mt-4">
                                    {mockData.modelPerformance.map((model, index) => (
                                        <div key={index} className="flex items-center justify-between text-sm">
                                            <div className="flex items-center gap-2">
                                                <div
                                                    className="w-3 h-3 rounded-full"
                                                    style={{ backgroundColor: model.color }}
                                                />
                                                <span className="text-slate-700 font-medium">{model.name}</span>
                                            </div>
                                            <span className="text-slate-600">{model.value}%</span>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>

                        {/* Quick Trend */}
                        <Card className="border-0 shadow-xl bg-white/90 backdrop-blur-sm">
                            <CardHeader className="bg-gradient-to-r from-purple-50 to-orange-50 border-b border-slate-200/60 rounded-t-lg">
                                <CardTitle className="flex items-center gap-3">
                                    <div className="p-2 bg-gradient-to-br from-purple-500 to-orange-600 rounded-xl shadow-lg">
                                        <TrendingUp className="h-5 w-5 text-white" />
                                    </div>
                                    7-Day Trend
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-6">
                                <ResponsiveContainer width="100%" height={150}>
                                    <AreaChart data={mockData.chartData.slice(-7)}>
                                        <defs>
                                            <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.8} />
                                                <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.1} />
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
                                            stroke="#8B5CF6"
                                            strokeWidth={3}
                                            fillOpacity={1}
                                            fill="url(#trendGradient)"
                                        />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>
                    </div>
                </div>

                {/* Comprehensive Chart */}
                <Card className="border-0 shadow-xl bg-white/90 backdrop-blur-sm">
                    <CardHeader className="bg-gradient-to-r from-slate-50 via-blue-50 to-purple-50 border-b border-slate-200/60 rounded-t-lg">
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle className="text-xl text-slate-900">Epidemiological Trends</CardTitle>
                                <CardDescription className="text-slate-600 mt-1">
                                    30-day comprehensive overview of key health metrics and model predictions
                                </CardDescription>
                            </div>
                            <div className="flex items-center gap-2">
                                <Badge variant="outline" className="bg-white/80">Live Data</Badge>
                                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent className="p-6">
                        <ResponsiveContainer width="100%" height={400}>
                            <LineChart data={mockData.chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                                <XAxis
                                    dataKey="day"
                                    tick={{ fontSize: 12 }}
                                    axisLine={{ stroke: '#CBD5E1' }}
                                />
                                <YAxis
                                    tick={{ fontSize: 12 }}
                                    axisLine={{ stroke: '#CBD5E1' }}
                                />
                                <Tooltip
                                    contentStyle={{
                                        background: 'rgba(255, 255, 255, 0.95)',
                                        border: 'none',
                                        borderRadius: '12px',
                                        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
                                        backdropFilter: 'blur(8px)'
                                    }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="infections"
                                    stroke="#EF4444"
                                    strokeWidth={3}
                                    name="New Infections"
                                    dot={false}
                                    strokeDasharray="0"
                                />
                                <Line
                                    type="monotone"
                                    dataKey="recovered"
                                    stroke="#10B981"
                                    strokeWidth={3}
                                    name="Recovered"
                                    dot={false}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="vaccinated"
                                    stroke="#8B5CF6"
                                    strokeWidth={3}
                                    name="Vaccinated"
                                    dot={false}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="deaths"
                                    stroke="#6B7280"
                                    strokeWidth={2}
                                    name="Deaths"
                                    dot={false}
                                    strokeDasharray="5 5"
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}