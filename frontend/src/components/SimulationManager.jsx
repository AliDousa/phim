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
    Activity,
    Brain,
    Sparkles,
    Zap,
    Globe,
    Target,
    Calendar,
    Database,
    ArrowLeft,
    Save,
    Copy
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, Legend } from 'recharts';

// Enhanced model templates with more sophisticated parameters
const modelTemplates = {
    seir: {
        name: "SEIR Model",
        description: "Susceptible-Exposed-Infectious-Recovered compartmental model with advanced epidemiological parameters",
        category: "Compartmental",
        complexity: "Medium",
        accuracy: "High",
        icon: Users,
        color: "blue",
        parameters: [
            { name: "population", label: "Population Size", type: "number", default: 100000, min: 1000, max: 10000000, unit: "people" },
            { name: "beta", label: "Transmission Rate (β)", type: "slider", default: 0.3, min: 0.1, max: 1.0, step: 0.01, description: "Contact rate that leads to infection" },
            { name: "sigma", label: "Incubation Rate (σ)", type: "slider", default: 0.2, min: 0.05, max: 0.5, step: 0.01, description: "Rate at which exposed become infectious" },
            { name: "gamma", label: "Recovery Rate (γ)", type: "slider", default: 0.1, min: 0.01, max: 0.3, step: 0.01, description: "Rate at which infectious recover" },
            { name: "timeHorizon", label: "Time Horizon", type: "number", default: 365, min: 30, max: 1095, unit: "days" },
            { name: "initialInfected", label: "Initial Infected", type: "number", default: 10, min: 1, max: 1000, unit: "people" }
        ]
    },
    ml_forecast: {
        name: "ML Forecast",
        description: "Advanced machine learning ensemble model with deep learning capabilities for epidemic forecasting",
        category: "Machine Learning",
        complexity: "High",
        accuracy: "Very High",
        icon: Brain,
        color: "purple",
        parameters: [
            { name: "ml_model_type", label: "ML Architecture", type: "select", options: ["ensemble", "lstm", "transformer", "random_forest", "gradient_boosting"], default: "ensemble", description: "Neural network architecture" },
            { name: "target_column", label: "Target Variable", type: "select", options: ["new_cases", "deaths", "hospitalizations", "icu_admissions"], default: "new_cases" },
            { name: "forecast_horizon", label: "Forecast Horizon", type: "number", default: 30, min: 7, max: 365, unit: "days" },
            { name: "confidence_level", label: "Confidence Level", type: "slider", default: 0.95, min: 0.8, max: 0.99, step: 0.01, description: "Statistical confidence interval" },
            { name: "training_window", label: "Training Window", type: "number", default: 180, min: 30, max: 730, unit: "days" },
            { name: "cross_validation", label: "Cross Validation", type: "switch", default: true, description: "Enable time series cross-validation" }
        ]
    },
    agent_based: {
        name: "Agent-Based Model",
        description: "Complex multi-agent simulation modeling individual behavior and social network interactions",
        category: "Complex Systems",
        complexity: "Very High",
        accuracy: "High",
        icon: Globe,
        color: "emerald",
        parameters: [
            { name: "population_size", label: "Agent Population", type: "number", default: 10000, min: 1000, max: 100000, unit: "agents" },
            { name: "transmission_probability", label: "Transmission Probability", type: "slider", default: 0.05, min: 0.01, max: 0.2, step: 0.01, description: "Per-contact infection probability" },
            { name: "recovery_time", label: "Recovery Time", type: "number", default: 14, min: 5, max: 30, unit: "days" },
            { name: "time_steps", label: "Simulation Steps", type: "number", default: 365, min: 30, max: 1095, unit: "days" },
            { name: "social_distancing", label: "Social Distancing", type: "switch", default: false, description: "Enable social distancing measures" },
            { name: "mobility_reduction", label: "Mobility Reduction", type: "slider", default: 0.0, min: 0.0, max: 0.9, step: 0.1, description: "Reduction in agent mobility" },
            { name: "network_type", label: "Social Network", type: "select", options: ["random", "small_world", "scale_free", "spatial"], default: "small_world" }
        ]
    },
    hybrid: {
        name: "Hybrid AI-Mechanistic",
        description: "Next-generation hybrid model combining mechanistic understanding with AI-driven insights",
        category: "Hybrid AI",
        complexity: "Expert",
        accuracy: "Exceptional",
        icon: Sparkles,
        color: "orange",
        parameters: [
            { name: "mechanistic_weight", label: "Mechanistic Weight", type: "slider", default: 0.6, min: 0.1, max: 0.9, step: 0.1, description: "Balance between mechanistic and AI components" },
            { name: "ai_ensemble_size", label: "AI Ensemble Size", type: "number", default: 5, min: 3, max: 10, unit: "models" },
            { name: "update_frequency", label: "Model Update Frequency", type: "select", options: ["daily", "weekly", "bi-weekly"], default: "weekly" },
            { name: "uncertainty_quantification", label: "Uncertainty Quantification", type: "switch", default: true, description: "Enable advanced uncertainty estimation" },
            { name: "real_time_adaptation", label: "Real-time Adaptation", type: "switch", default: true, description: "Adapt to incoming data streams" }
        ]
    }
};

const StatusBadge = ({ status }) => {
    const config = {
        completed: {
            icon: CheckCircle,
            className: "bg-emerald-500 text-emerald-50 border-0 shadow-lg shadow-emerald-500/25",
            dot: "bg-emerald-400"
        },
        running: {
            icon: Activity,
            className: "bg-blue-500 text-blue-50 border-0 shadow-lg shadow-blue-500/25 animate-pulse",
            dot: "bg-blue-400 animate-pulse"
        },
        pending: {
            icon: Clock,
            className: "bg-slate-500 text-slate-50 border-0 shadow-lg shadow-slate-500/25",
            dot: "bg-slate-400"
        },
        failed: {
            icon: AlertCircle,
            className: "bg-red-500 text-red-50 border-0 shadow-lg shadow-red-500/25",
            dot: "bg-red-400"
        }
    };

    const { icon: Icon, className, dot } = config[status] || config.pending;

    return (
        <Badge className={`${className} flex items-center gap-2 px-3 py-1 font-medium`}>
            <div className={`w-2 h-2 rounded-full ${dot}`} />
            <Icon className="w-3 h-3" />
            {status.charAt(0).toUpperCase() + status.slice(1)}
        </Badge>
    );
};

const ParameterField = ({ param, value, onChange }) => {
    const handleChange = (newValue) => {
        onChange(param.name, newValue);
    };

    const renderField = () => {
        switch (param.type) {
            case 'slider':
                return (
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <Label className="font-medium">{param.label}</Label>
                            <div className="text-sm font-mono bg-slate-100 px-2 py-1 rounded">
                                {value}{param.unit && ` ${param.unit}`}
                            </div>
                        </div>
                        <Slider
                            value={[value]}
                            onValueChange={([newValue]) => handleChange(newValue)}
                            min={param.min}
                            max={param.max}
                            step={param.step}
                            className="w-full"
                        />
                        <div className="flex justify-between text-xs text-slate-500">
                            <span>{param.min}</span>
                            <span>{param.max}</span>
                        </div>
                        {param.description && (
                            <p className="text-xs text-slate-500 mt-1">{param.description}</p>
                        )}
                    </div>
                );

            case 'select':
                return (
                    <div className="space-y-2">
                        <Label className="font-medium">{param.label}</Label>
                        <Select value={value} onValueChange={handleChange}>
                            <SelectTrigger className="bg-white shadow-sm">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                {param.options.map(option => (
                                    <SelectItem key={option} value={option}>
                                        {option.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                        {param.description && (
                            <p className="text-xs text-slate-500">{param.description}</p>
                        )}
                    </div>
                );

            case 'switch':
                return (
                    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div>
                            <Label className="font-medium">{param.label}</Label>
                            {param.description && (
                                <p className="text-xs text-slate-500 mt-1">{param.description}</p>
                            )}
                        </div>
                        <Switch checked={value} onCheckedChange={handleChange} />
                    </div>
                );

            default:
                return (
                    <div className="space-y-2">
                        <Label className="font-medium">{param.label}</Label>
                        <div className="relative">
                            <Input
                                type="number"
                                value={value}
                                onChange={(e) => handleChange(Number(e.target.value))}
                                min={param.min}
                                max={param.max}
                                className="bg-white shadow-sm pr-12"
                            />
                            {param.unit && (
                                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-slate-500">
                                    {param.unit}
                                </span>
                            )}
                        </div>
                        {param.description && (
                            <p className="text-xs text-slate-500">{param.description}</p>
                        )}
                    </div>
                );
        }
    };

    return (
        <div className="space-y-2">
            {renderField()}
        </div>
    );
};

const ModelCard = ({ modelKey, template, isSelected, onSelect }) => {
    const colorClasses = {
        blue: "from-blue-500/10 to-blue-600/5 border-blue-200/50 text-blue-600",
        purple: "from-purple-500/10 to-purple-600/5 border-purple-200/50 text-purple-600",
        emerald: "from-emerald-500/10 to-emerald-600/5 border-emerald-200/50 text-emerald-600",
        orange: "from-orange-500/10 to-orange-600/5 border-orange-200/50 text-orange-600"
    };

    const Icon = template.icon;

    return (
        <Card
            className={`cursor-pointer transition-all duration-300 hover:shadow-xl hover:-translate-y-1 ${isSelected
                ? 'ring-2 ring-blue-500 shadow-xl border-blue-200'
                : 'hover:shadow-lg border-slate-200'
                }`}
            onClick={() => onSelect(modelKey)}
        >
            <div className={`absolute inset-0 bg-gradient-to-br ${colorClasses[template.color]} opacity-60 rounded-lg`} />
            <CardHeader className="relative pb-3">
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                        <div className={`p-3 rounded-xl bg-gradient-to-br ${colorClasses[template.color].includes('blue') ? 'from-blue-500 to-blue-600' :
                            colorClasses[template.color].includes('purple') ? 'from-purple-500 to-purple-600' :
                                colorClasses[template.color].includes('emerald') ? 'from-emerald-500 to-emerald-600' :
                                    'from-orange-500 to-orange-600'
                            } text-white shadow-lg`}>
                            <Icon className="h-6 w-6" />
                        </div>
                        <div>
                            <CardTitle className="text-lg">{template.name}</CardTitle>
                            <p className="text-sm text-slate-600">{template.category}</p>
                        </div>
                    </div>
                    {isSelected && (
                        <CheckCircle className="h-5 w-5 text-blue-500" />
                    )}
                </div>
            </CardHeader>
            <CardContent className="relative">
                <p className="text-sm text-slate-700 mb-4">{template.description}</p>
                <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1">
                            <Target className="h-3 w-3" />
                            {template.accuracy}
                        </span>
                        <span className="flex items-center gap-1">
                            <Settings className="h-3 w-3" />
                            {template.complexity}
                        </span>
                    </div>
                    <Badge variant="outline" className="text-xs">
                        {template.parameters.length} params
                    </Badge>
                </div>
            </CardContent>
        </Card>
    );
};

const CreateSimulationForm = ({ onSubmit, onCancel }) => {
    const [step, setStep] = useState(1);
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        model_type: '',
        dataset_id: null,
        parameters: {}
    });
    const [datasets, setDatasets] = useState([]);

    const currentTemplate = formData.model_type ? modelTemplates[formData.model_type] : null;

    // Initialize parameters when model type changes
    useEffect(() => {
        if (currentTemplate) {
            const defaultParams = {};
            currentTemplate.parameters.forEach(param => {
                defaultParams[param.name] = param.default;
            });
            setFormData(prev => ({ ...prev, parameters: defaultParams }));
        }
    }, [formData.model_type, currentTemplate]);

    const handleParameterChange = (paramName, value) => {
        setFormData(prev => ({
            ...prev,
            parameters: { ...prev.parameters, [paramName]: value }
        }));
    };

    const handleNext = () => {
        if (step === 1 && !formData.model_type) {
            toast.error('Please select a model type');
            return;
        }
        if (step === 2 && !formData.name.trim()) {
            toast.error('Please enter a simulation name');
            return;
        }
        setStep(step + 1);
    };

    const handleSubmit = () => {
        if (formData.model_type === 'ml_forecast' && !formData.dataset_id) {
            toast.error('Please select a dataset for ML forecasting');
            return;
        }
        onSubmit(formData);
    };

    const renderStepContent = () => {
        switch (step) {
            case 1:
                return (
                    <div className="space-y-6">
                        <div className="text-center">
                            <h3 className="text-2xl font-bold text-slate-900 mb-2">Choose Your Model</h3>
                            <p className="text-slate-600">Select the epidemiological modeling approach that best fits your analysis needs</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {Object.entries(modelTemplates).map(([key, template]) => (
                                <ModelCard
                                    key={key}
                                    modelKey={key}
                                    template={template}
                                    isSelected={formData.model_type === key}
                                    onSelect={(modelKey) => setFormData(prev => ({ ...prev, model_type: modelKey }))}
                                />
                            ))}
                        </div>
                    </div>
                );

            case 2:
                return (
                    <div className="space-y-6">
                        <div className="text-center">
                            <h3 className="text-2xl font-bold text-slate-900 mb-2">Simulation Details</h3>
                            <p className="text-slate-600">Configure your simulation settings and metadata</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <Label htmlFor="name" className="font-medium">Simulation Name</Label>
                                <Input
                                    id="name"
                                    value={formData.name}
                                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                                    placeholder="e.g., COVID-19 Winter Wave Analysis"
                                    className="bg-white shadow-sm"
                                />
                            </div>

                            <div className="space-y-2">
                                <Label className="font-medium">Selected Model</Label>
                                <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                                    {currentTemplate && (
                                        <>
                                            <currentTemplate.icon className="h-5 w-5 text-slate-600" />
                                            <span className="font-medium">{currentTemplate.name}</span>
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="description" className="font-medium">Description</Label>
                            <Textarea
                                id="description"
                                value={formData.description}
                                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                                placeholder="Describe the purpose and scope of this simulation..."
                                rows={4}
                                className="bg-white shadow-sm"
                            />
                        </div>

                        {formData.model_type === 'ml_forecast' && (
                            <div className="space-y-2">
                                <Label className="font-medium">Dataset (required for ML)</Label>
                                <Select
                                    value={formData.dataset_id ? String(formData.dataset_id) : ''}
                                    onValueChange={(value) => setFormData(prev => ({ ...prev, dataset_id: parseInt(value) }))}
                                >
                                    <SelectTrigger className="bg-white shadow-sm">
                                        <SelectValue placeholder="Select a dataset" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="1">COVID-19 Regional Data (50K records)</SelectItem>
                                        <SelectItem value="2">Influenza Surveillance (25K records)</SelectItem>
                                        <SelectItem value="3">Multi-Disease Dataset (100K records)</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        )}
                    </div>
                );

            case 3:
                return (
                    <div className="space-y-6">
                        <div className="text-center">
                            <h3 className="text-2xl font-bold text-slate-900 mb-2">Model Parameters</h3>
                            <p className="text-slate-600">Fine-tune your {currentTemplate?.name} parameters</p>
                        </div>

                        {currentTemplate && (
                            <Card className="border-0 shadow-xl bg-white/90 backdrop-blur-sm">
                                <CardHeader className="bg-gradient-to-r from-slate-50 to-blue-50 border-b border-slate-200/60">
                                    <CardTitle className="flex items-center gap-3">
                                        <currentTemplate.icon className="h-5 w-5" />
                                        {currentTemplate.name} Configuration
                                    </CardTitle>
                                    <CardDescription>{currentTemplate.description}</CardDescription>
                                </CardHeader>
                                <CardContent className="p-6 space-y-6">
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
                        )}
                    </div>
                );

            default:
                return null;
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20 p-8">
            <div className="max-w-6xl mx-auto space-y-8">
                {/* Progress Header */}
                <div className="flex items-center justify-between">
                    <Button
                        variant="outline"
                        onClick={step === 1 ? onCancel : () => setStep(step - 1)}
                        className="shadow-lg"
                    >
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        {step === 1 ? 'Cancel' : 'Back'}
                    </Button>

                    <div className="flex items-center gap-4">
                        {[1, 2, 3].map((stepNum) => (
                            <div key={stepNum} className="flex items-center gap-2">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-medium ${step >= stepNum
                                    ? 'bg-blue-500 text-white'
                                    : 'bg-slate-200 text-slate-500'
                                    }`}>
                                    {stepNum}
                                </div>
                                {stepNum < 3 && (
                                    <div className={`w-12 h-0.5 ${step > stepNum ? 'bg-blue-500' : 'bg-slate-200'}`} />
                                )}
                            </div>
                        ))}
                    </div>

                    <div className="w-20" /> {/* Spacer */}
                </div>

                {/* Step Content */}
                <div className="animate-fade-in">
                    {renderStepContent()}
                </div>

                {/* Action Buttons */}
                <div className="flex justify-center gap-4">
                    {step < 3 ? (
                        <Button
                            onClick={handleNext}
                            disabled={step === 1 && !formData.model_type}
                            className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white border-0 shadow-xl hover:shadow-2xl px-8 py-6 text-lg font-semibold"
                        >
                            Continue
                            <ArrowRight className="w-5 h-5 ml-2" />
                        </Button>
                    ) : (
                        <div className="flex gap-4">
                            <Button
                                variant="outline"
                                onClick={() => setStep(2)}
                                className="shadow-lg px-6"
                            >
                                <Edit className="w-4 h-4 mr-2" />
                                Review Details
                            </Button>
                            <Button
                                onClick={handleSubmit}
                                className="bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white border-0 shadow-xl hover:shadow-2xl px-8 py-6 text-lg font-semibold"
                            >
                                <Play className="w-5 h-5 mr-2" />
                                Launch Simulation
                                <Sparkles className="w-4 w-4 ml-2" />
                            </Button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

// Simulation Card Component (simplified for space)
const SimulationCard = ({ simulation, onAction }) => {
    const mockChartData = Array.from({ length: 10 }, (_, i) => ({
        day: i + 1,
        value: Math.floor(Math.random() * 100) + 50
    }));

    return (
        <Card className="group relative overflow-hidden border-0 shadow-xl hover:shadow-2xl transition-all duration-500 hover:-translate-y-1 bg-white/90 backdrop-blur-sm">
            <div className={`absolute top-0 left-0 right-0 h-1 ${simulation.status === 'completed' ? 'bg-emerald-500' :
                simulation.status === 'running' ? 'bg-blue-500' :
                    'bg-slate-400'
                }`} />

            <CardHeader className="pb-4">
                <div className="flex items-start justify-between">
                    <div className="space-y-2 flex-1">
                        <div className="flex items-center gap-3">
                            <CardTitle className="text-lg font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                                {simulation.name}
                            </CardTitle>
                            <StatusBadge status={simulation.status} />
                        </div>

                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div className="flex items-center gap-2 text-slate-600">
                                <Brain className="w-4 h-4 text-purple-500" />
                                <span>{simulation.model_type}</span>
                            </div>
                            <div className="flex items-center gap-2 text-slate-600">
                                <Calendar className="w-4 h-4 text-blue-500" />
                                <span>{new Date(simulation.created_at).toLocaleDateString()}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </CardHeader>

            <CardContent className="space-y-4">
                {simulation.status === 'running' && (
                    <div className="space-y-2">
                        <div className="flex justify-between text-sm font-medium">
                            <span className="text-slate-600">Progress</span>
                            <span className="text-blue-600">65%</span>
                        </div>
                        <Progress value={65} className="h-2" />
                    </div>
                )}

                {simulation.status === 'completed' && (
                    <div className="h-32">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={mockChartData}>
                                <defs>
                                    <linearGradient id={`grad-${simulation.id}`} x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8} />
                                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1} />
                                    </linearGradient>
                                </defs>
                                <Area
                                    type="monotone"
                                    dataKey="value"
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
                    {simulation.status === 'completed' && (
                        <Button size="sm" onClick={() => onAction('view', simulation.id)}
                            className="bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white border-0">
                            <Eye className="w-4 h-4 mr-2" />
                            View Results
                        </Button>
                    )}
                    <Button size="sm" variant="outline" onClick={() => onAction('duplicate', simulation.id)}>
                        <Copy className="w-4 h-4" />
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
    const [simulations, setSimulations] = useState([
        {
            id: 1,
            name: "COVID-19 Variant Analysis",
            status: "completed",
            model_type: "SEIR",
            created_at: "2024-06-20T10:00:00Z"
        },
        {
            id: 2,
            name: "Seasonal Flu Forecast",
            status: "running",
            model_type: "ML-Ensemble",
            created_at: "2024-06-22T14:30:00Z"
        },
        {
            id: 3,
            name: "Multi-pathogen Model",
            status: "pending",
            model_type: "Agent-Based",
            created_at: "2024-06-23T09:15:00Z"
        }
    ]);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    const handleCreateSimulation = async (formData) => {
        const newSimulation = {
            id: Date.now(),
            name: formData.name,
            description: formData.description,
            model_type: formData.model_type,
            status: 'pending',
            created_at: new Date().toISOString(),
            parameters: formData.parameters
        };

        setSimulations(prev => [newSimulation, ...prev]);
        setShowCreateForm(false);
        toast.success(`Simulation "${formData.name}" created successfully!`);
    };

    const handleSimulationAction = (action, simulationId) => {
        switch (action) {
            case 'view':
                onSelectSimulation?.(simulationId);
                break;
            case 'delete':
                if (confirm('Are you sure you want to delete this simulation?')) {
                    setSimulations(prev => prev.filter(sim => sim.id !== simulationId));
                    toast.success('Simulation deleted successfully');
                }
                break;
            case 'duplicate':
                const original = simulations.find(sim => sim.id === simulationId);
                if (original) {
                    const duplicate = {
                        ...original,
                        id: Date.now(),
                        name: `${original.name} (Copy)`,
                        status: 'pending',
                        created_at: new Date().toISOString()
                    };
                    setSimulations(prev => [duplicate, ...prev]);
                    toast.success('Simulation duplicated successfully');
                }
                break;
            default:
                toast.info(`${action} action triggered`);
        }
    };

    if (showCreateForm) {
        return (
            <CreateSimulationForm
                onSubmit={handleCreateSimulation}
                onCancel={() => setShowCreateForm(false)}
            />
        );
    }

    const stats = {
        total: simulations.length,
        running: simulations.filter(s => s.status === 'running').length,
        completed: simulations.filter(s => s.status === 'completed').length,
        pending: simulations.filter(s => s.status === 'pending').length
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20">
            <Toaster richColors position="top-right" />

            <div className="p-8 space-y-8">
                {/* Header */}
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                    <div className="space-y-3">
                        <h1 className="text-5xl font-bold bg-gradient-to-r from-slate-900 via-blue-900 to-purple-900 bg-clip-text text-transparent leading-tight">
                            Simulation Manager
                        </h1>
                        <p className="text-xl text-slate-600 max-w-3xl">
                            Create, monitor, and manage your epidemiological simulations with advanced AI-powered models
                        </p>
                    </div>
                    <Button
                        onClick={() => setShowCreateForm(true)}
                        className="bg-gradient-to-r from-blue-500 via-blue-600 to-purple-600 hover:from-blue-600 hover:via-blue-700 hover:to-purple-700 text-white border-0 shadow-xl hover:shadow-2xl transition-all px-8 py-6 text-lg font-semibold"
                    >
                        <Plus className="h-5 w-5 mr-3" />
                        New Simulation
                        <Sparkles className="h-4 w-4 ml-2" />
                    </Button>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                    {[
                        { title: "Total Simulations", value: stats.total, icon: BarChart3, color: "blue" },
                        { title: "Running", value: stats.running, icon: Activity, color: "emerald" },
                        { title: "Completed", value: stats.completed, icon: CheckCircle, color: "purple" },
                        { title: "Pending", value: stats.pending, icon: Clock, color: "orange" }
                    ].map((stat, index) => (
                        <Card key={index} className="border-0 shadow-xl bg-white/90 backdrop-blur-sm hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
                            <CardContent className="flex items-center justify-between p-6">
                                <div>
                                    <p className="text-sm font-medium text-slate-600 uppercase tracking-wide">{stat.title}</p>
                                    <p className="text-3xl font-bold text-slate-900">{stat.value}</p>
                                </div>
                                <div className={`p-3 rounded-xl bg-gradient-to-br ${stat.color === 'blue' ? 'from-blue-500 to-blue-600' :
                                    stat.color === 'emerald' ? 'from-emerald-500 to-emerald-600' :
                                        stat.color === 'purple' ? 'from-purple-500 to-purple-600' :
                                            'from-orange-500 to-orange-600'
                                    } text-white shadow-lg`}>
                                    <stat.icon className="h-6 w-6" />
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>

                {/* Simulations Grid */}
                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-2xl font-bold text-slate-900">Your Simulations</h2>
                        <Badge className="bg-blue-100 text-blue-700 border-0">
                            {simulations.length} Total
                        </Badge>
                    </div>

                    {simulations.length === 0 ? (
                        <Card className="border-0 shadow-xl bg-white/90 backdrop-blur-sm">
                            <CardContent className="flex flex-col items-center justify-center py-16">
                                <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mb-6">
                                    <Beaker className="h-12 w-12 text-white" />
                                </div>
                                <h3 className="text-2xl font-bold text-slate-900 mb-2">No simulations yet</h3>
                                <p className="text-slate-600 text-center mb-6 max-w-md">
                                    Get started by creating your first epidemiological simulation with our advanced AI-powered models
                                </p>
                                <Button
                                    onClick={() => setShowCreateForm(true)}
                                    className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white border-0 shadow-xl hover:shadow-2xl"
                                >
                                    <Plus className="w-5 h-5 mr-2" />
                                    Create First Simulation
                                </Button>
                            </CardContent>
                        </Card>
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
                </div>
            </div>
        </div>
    );
}