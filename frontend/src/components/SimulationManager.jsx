import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Toaster, toast } from 'sonner';
import {
    Play,
    Pause,
    Square,
    Settings,
    BarChart3,
    Clock,
    Users,
    TrendingUp,
    AlertCircle,
    CheckCircle,
    Loader2,
    Plus,
    Edit,
    Trash2,
    Eye,
    Download,
    RefreshCw,
    Activity
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, Legend } from 'recharts';

// Model templates with parameters
const modelTemplates = {
    seir: {
        name: "SEIR Model",
        description: "Susceptible-Exposed-Infectious-Recovered compartmental model",
        parameters: [
            { name: "population", label: "Population Size", type: "number", default: 100000, min: 1000, max: 10000000 },
            { name: "beta", label: "Transmission Rate (β)", type: "slider", default: 0.3, min: 0.1, max: 1.0, step: 0.01 },
            { name: "sigma", label: "Incubation Rate (σ)", type: "slider", default: 0.2, min: 0.05, max: 0.5, step: 0.01 },
            { name: "gamma", label: "Recovery Rate (γ)", type: "slider", default: 0.1, min: 0.01, max: 0.3, step: 0.01 },
            { name: "timeHorizon", label: "Time Horizon (days)", type: "number", default: 365, min: 30, max: 1095 }
        ]
    },
    ml_forecast: {
        name: "ML Forecast",
        description: "Machine learning-based forecasting model",
        parameters: [
            { name: "ml_model_type", label: "ML Model", type: "select", options: ["ensemble", "random_forest", "gradient_boosting"], default: "ensemble" },
            { name: "target_column", label: "Target Variable", type: "select", options: ["new_cases", "deaths", "hospitalizations"], default: "new_cases" },
            { name: "forecast_horizon", label: "Forecast Days", type: "number", default: 30, min: 7, max: 365 },
            { name: "confidence_level", label: "Confidence Level", type: "slider", default: 0.95, min: 0.8, max: 0.99, step: 0.01 }
        ]
    },
    agent_based: {
        name: "Agent-Based Model",
        description: "Individual agent simulation for complex interactions",
        parameters: [
            { name: "population_size", label: "Population Size", type: "number", default: 10000, min: 1000, max: 100000 },
            { name: "transmission_probability", label: "Transmission Probability", type: "slider", default: 0.05, min: 0.01, max: 0.2, step: 0.01 },
            { name: "recovery_time", label: "Recovery Time (days)", type: "number", default: 14, min: 5, max: 30 },
            { name: "time_steps", label: "Simulation Steps", type: "number", default: 365, min: 30, max: 1095 },
            { name: "social_distancing", label: "Social Distancing", type: "switch", default: false }
        ]
    }
};

const StatusBadge = ({ status }) => {
    const config = {
        completed: { variant: "default", icon: CheckCircle, color: "text-green-600 bg-green-50 border-green-200" },
        running: { variant: "secondary", icon: Loader2, color: "text-blue-600 bg-blue-50 border-blue-200" },
        pending: { variant: "outline", icon: Clock, color: "text-gray-600 bg-gray-50 border-gray-200" },
        failed: { variant: "destructive", icon: AlertCircle, color: "text-red-600 bg-red-50 border-red-200" }
    };

    const { icon: Icon, color } = config[status] || config.pending;

    return (
        <Badge className={`${color} flex items-center gap-1 px-2 py-1`}>
            <Icon className={`w-3 h-3 ${status === 'running' ? 'animate-spin' : ''}`} />
            {status.charAt(0).toUpperCase() + status.slice(1)}
        </Badge>
    );
};

const ParameterField = ({ param, value, onChange }) => {
    const handleChange = (newValue) => {
        onChange(param.name, newValue);
    };

    switch (param.type) {
        case 'slider':
            return (
                <div className="space-y-2">
                    <div className="flex justify-between">
                        <Label>{param.label}</Label>
                        <span className="text-sm text-gray-500">{value}</span>
                    </div>
                    <Slider
                        value={[value]}
                        onValueChange={([newValue]) => handleChange(newValue)}
                        min={param.min}
                        max={param.max}
                        step={param.step}
                        className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-400">
                        <span>{param.min}</span>
                        <span>{param.max}</span>
                    </div>
                </div>
            );

        case 'select':
            return (
                <div className="space-y-2">
                    <Label>{param.label}</Label>
                    <Select value={value} onValueChange={handleChange}>
                        <SelectTrigger>
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            {param.options.map(option => (
                                <SelectItem key={option} value={option}>
                                    {option.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            );

        case 'switch':
            return (
                <div className="flex items-center justify-between">
                    <Label>{param.label}</Label>
                    <Switch checked={value} onCheckedChange={handleChange} />
                </div>
            );

        default:
            return (
                <div className="space-y-2">
                    <Label>{param.label}</Label>
                    <Input
                        type="number"
                        value={value}
                        onChange={(e) => handleChange(Number(e.target.value))}
                        min={param.min}
                        max={param.max}
                    />
                </div>
            );
    }
};

const CreateSimulationForm = ({ onSubmit, onCancel }) => {
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        model_type: 'seir',
        dataset_id: null,
        parameters: {}
    });

    const [datasets, setDatasets] = useState([]);
    const authToken = localStorage.getItem('authToken');

    useEffect(() => {
        // Fetch datasets for ML models
        const fetchDatasets = async () => {
            try {
                const response = await fetch('/api/datasets', {
                    headers: { 'Authorization': `Bearer ${authToken}` }
                });
                if (response.ok) {
                    const data = await response.json();
                    setDatasets(data.datasets || []);
                }
            } catch (error) {
                console.error('Failed to fetch datasets:', error);
            }
        };
        fetchDatasets();
    }, [authToken]);

    const currentTemplate = modelTemplates[formData.model_type];

    useEffect(() => {
        // Initialize parameters with defaults when model type changes
        const defaultParams = {};
        currentTemplate.parameters.forEach(param => {
            defaultParams[param.name] = param.default;
        });
        setFormData(prev => ({ ...prev, parameters: defaultParams }));
    }, [formData.model_type, currentTemplate]);

    const handleParameterChange = (paramName, value) => {
        setFormData(prev => ({
            ...prev,
            parameters: { ...prev.parameters, [paramName]: value }
        }));
    };

    const handleSubmit = () => {
        if (formData.name.trim()) {
            // For ML models, ensure dataset is selected
            if (formData.model_type === 'ml_forecast' && !formData.dataset_id) {
                toast.error('Please select a dataset for ML forecasting');
                return;
            }
            onSubmit(formData);
        } else {
            toast.error('Please enter a simulation name');
        }
    };

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                    <Label htmlFor="name">Simulation Name</Label>
                    <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="e.g., COVID-19 Analysis"
                        required
                    />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="model">Model Type</Label>
                    <Select value={formData.model_type} onValueChange={(value) => setFormData(prev => ({ ...prev, model_type: value }))}>
                        <SelectTrigger>
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            {Object.entries(modelTemplates).map(([key, template]) => (
                                <SelectItem key={key} value={key}>
                                    {template.name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            </div>

            <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe the purpose of this simulation..."
                    rows={3}
                />
            </div>

            {formData.model_type === 'ml_forecast' && (
                <div className="space-y-2">
                    <Label htmlFor="dataset">Dataset (required for ML)</Label>
                    <Select
                        value={formData.dataset_id || ''}
                        onValueChange={(value) => setFormData(prev => ({ ...prev, dataset_id: parseInt(value) }))}
                    >
                        <SelectTrigger>
                            <SelectValue placeholder="Select a dataset" />
                        </SelectTrigger>
                        <SelectContent>
                            {datasets.map(d => (
                                <SelectItem key={d.id} value={String(d.id)}>{d.name}</SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            )}

            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">{currentTemplate.name} Parameters</CardTitle>
                    <CardDescription>{currentTemplate.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {currentTemplate.parameters.map(param => (
                        <ParameterField
                            key={param.name}
                            param={param}
                            value={formData.parameters[param.name]}
                            onChange={handleParameterChange}
                        />
                    ))}
                </CardContent>
            </Card>

            <div className="flex gap-3 justify-end">
                <Button type="button" variant="outline" onClick={onCancel}>
                    Cancel
                </Button>
                <Button onClick={handleSubmit} className="bg-gradient-to-r from-blue-500 to-purple-600">
                    <Play className="w-4 h-4 mr-2" />
                    Start Simulation
                </Button>
            </div>
        </div>
    );
};

const SimulationCard = ({ simulation, onAction }) => {
    const chartData = React.useMemo(() => {
        if (simulation.status !== 'completed') return [];

        return Array.from({ length: 30 }, (_, i) => ({
            day: i + 1,
            infections: Math.floor(Math.random() * 1000) + 200,
            recovered: Math.floor(Math.random() * 800) + 100
        }));
    }, [simulation.id]);

    return (
        <Card className="hover:shadow-lg transition-shadow duration-200">
            <CardHeader>
                <div className="flex items-start justify-between">
                    <div className="space-y-1">
                        <CardTitle className="text-lg">{simulation.name}</CardTitle>
                        <CardDescription>{simulation.description}</CardDescription>
                    </div>
                    <StatusBadge status={simulation.status} />
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span className="flex items-center gap-1">
                        <BarChart3 className="w-4 h-4" />
                        {simulation.model_type}
                    </span>
                    <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {new Date(simulation.created_at).toLocaleDateString()}
                    </span>
                    {simulation.results?.r0 && (
                        <span className="flex items-center gap-1">
                            <TrendingUp className="w-4 h-4" />
                            R₀: {simulation.results.r0}
                        </span>
                    )}
                </div>
            </CardHeader>

            <CardContent className="space-y-4">
                {simulation.status === 'running' && (
                    <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                            <span>Progress</span>
                            <span>65%</span>
                        </div>
                        <Progress value={65} className="h-2" />
                    </div>
                )}

                {simulation.status === 'completed' && chartData.length > 0 && (
                    <div className="h-40">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id={`grad-${simulation.id}`} x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8} />
                                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1} />
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
                                    fill={`url(#grad-${simulation.id})`}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                )}

                <div className="flex items-center gap-2">
                    {simulation.status === 'running' && (
                        <Button size="sm" variant="outline" onClick={() => onAction('pause', simulation.id)}>
                            <Pause className="w-4 h-4" />
                        </Button>
                    )}
                    {simulation.status === 'pending' && (
                        <Button size="sm" onClick={() => onAction('start', simulation.id)}>
                            <Play className="w-4 h-4" />
                        </Button>
                    )}
                    {simulation.status === 'completed' && (
                        <>
                            <Button size="sm" variant="outline" onClick={() => onAction('view', simulation.id)}>
                                <Eye className="w-4 h-4" />
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => onAction('download', simulation.id)}>
                                <Download className="w-4 h-4" />
                            </Button>
                        </>
                    )}
                    <Button size="sm" variant="outline" onClick={() => onAction('duplicate', simulation.id)}>
                        <RefreshCw className="w-4 h-4" />
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => onAction('delete', simulation.id)}>
                        <Trash2 className="w-4 h-4 text-red-500" />
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
};

export default function SimulationManager({ onSelectSimulation }) {
    const [simulations, setSimulations] = useState([]);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const authToken = localStorage.getItem('authToken');

    const fetchSimulations = useCallback(async () => {
        setIsLoading(true);
        try {
            const response = await fetch('/api/simulations', {
                headers: { 'Authorization': `Bearer ${authToken}` }
            });
            const data = await response.json();
            if (response.ok) {
                setSimulations(data.simulations || []);
            } else {
                toast.error('Failed to fetch simulations');
            }
        } catch (error) {
            toast.error('Error fetching simulations');
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    }, [authToken]);

    useEffect(() => {
        fetchSimulations();
        // Poll for updates every 15 seconds
        const interval = setInterval(fetchSimulations, 15000);
        return () => clearInterval(interval);
    }, [fetchSimulations]);

    const handleCreateSimulation = async (formData) => {
        try {
            const response = await fetch('/api/simulations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`,
                },
                body: JSON.stringify(formData),
            });

            const result = await response.json();
            if (response.ok) {
                toast.success(`Simulation "${result.simulation.name}" created successfully.`);
                setSimulations(prev => [result.simulation, ...prev]);
                setShowCreateForm(false);
            } else {
                toast.error(`Failed to create simulation: ${result.error}`);
            }
        } catch (error) {
            toast.error('An error occurred while creating the simulation.');
            console.error(error);
        }
    };

    const handleSimulationAction = async (action, simulationId) => {
        switch (action) {
            case 'view':
                onSelectSimulation(simulationId);
                break;
            case 'pause':
                toast.info('Pause functionality not implemented yet');
                break;
            case 'start':
                toast.info('Start functionality not implemented yet');
                break;
            case 'delete':
                if (window.confirm('Are you sure you want to delete this simulation?')) {
                    try {
                        const response = await fetch(`/api/simulations/${simulationId}`, {
                            method: 'DELETE',
                            headers: { 'Authorization': `Bearer ${authToken}` }
                        });
                        if (response.ok) {
                            setSimulations(prev => prev.filter(sim => sim.id !== simulationId));
                            toast.success('Simulation deleted successfully');
                        } else {
                            toast.error('Failed to delete simulation');
                        }
                    } catch (error) {
                        toast.error('Error deleting simulation');
                    }
                }
                break;
            case 'duplicate':
                const original = simulations.find(sim => sim.id === simulationId);
                if (original) {
                    const duplicateData = {
                        name: `${original.name} (Copy)`,
                        description: original.description,
                        model_type: original.model_type,
                        dataset_id: original.dataset_id,
                        parameters: original.parameters
                    };
                    await handleCreateSimulation(duplicateData);
                }
                break;
            case 'download':
                toast.info('Download functionality not implemented yet');
                break;
        }
    };

    const stats = {
        total: simulations.length,
        running: simulations.filter(s => s.status === 'running').length,
        completed: simulations.filter(s => s.status === 'completed').length,
        pending: simulations.filter(s => s.status === 'pending').length
    };

    if (showCreateForm) {
        return (
            <div className="space-y-6">
                <Toaster richColors />
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Create New Simulation</h1>
                        <p className="text-gray-600">Configure your epidemiological model parameters</p>
                    </div>
                </div>
                <CreateSimulationForm
                    onSubmit={handleCreateSimulation}
                    onCancel={() => setShowCreateForm(false)}
                />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <Toaster richColors />
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Simulation Manager</h1>
                    <p className="text-gray-600">Create and monitor epidemiological simulations</p>
                </div>
                <Button onClick={() => setShowCreateForm(true)} className="bg-gradient-to-r from-blue-500 to-purple-600">
                    <Plus className="w-4 h-4 mr-2" />
                    New Simulation
                </Button>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                    <CardContent className="flex items-center justify-between p-4">
                        <div>
                            <p className="text-sm text-gray-600">Total</p>
                            <p className="text-2xl font-bold">{stats.total}</p>
                        </div>
                        <BarChart3 className="h-8 w-8 text-gray-400" />
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="flex items-center justify-between p-4">
                        <div>
                            <p className="text-sm text-gray-600">Running</p>
                            <p className="text-2xl font-bold text-blue-600">{stats.running}</p>
                        </div>
                        <Activity className="h-8 w-8 text-blue-400" />
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="flex items-center justify-between p-4">
                        <div>
                            <p className="text-sm text-gray-600">Completed</p>
                            <p className="text-2xl font-bold text-green-600">{stats.completed}</p>
                        </div>
                        <CheckCircle className="h-8 w-8 text-green-400" />
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="flex items-center justify-between p-4">
                        <div>
                            <p className="text-sm text-gray-600">Pending</p>
                            <p className="text-2xl font-bold text-gray-600">{stats.pending}</p>
                        </div>
                        <Clock className="h-8 w-8 text-gray-400" />
                    </CardContent>
                </Card>
            </div>

            {/* Simulations Grid */}
            {isLoading ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                    {[...Array(3)].map((_, i) => (
                        <Card key={i} className="animate-pulse">
                            <CardHeader>
                                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                            </CardHeader>
                            <CardContent>
                                <div className="h-32 bg-gray-200 rounded"></div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                    {simulations.map(simulation => (
                        <SimulationCard
                            key={simulation.id}
                            simulation={simulation}
                            onAction={handleSimulationAction}
                        />
                    ))}
                </div>
            )}

            {simulations.length === 0 && !isLoading && (
                <Card>
                    <CardContent className="flex flex-col items-center justify-center py-12">
                        <BarChart3 className="h-12 w-12 text-gray-400 mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No simulations yet</h3>
                        <p className="text-gray-600 text-center mb-4">
                            Create your first epidemiological simulation to get started with predictive modeling.
                        </p>
                        <Button onClick={() => setShowCreateForm(true)} className="bg-gradient-to-r from-blue-500 to-purple-600">
                            <Plus className="w-4 h-4 mr-2" />
                            Create First Simulation
                        </Button>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}