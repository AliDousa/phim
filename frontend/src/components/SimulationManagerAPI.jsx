import React, { useState, useEffect } from 'react';
import ApiService from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';
import {
    Play,
    Pause,
    Square,
    Settings,
    BarChart3,
    Database,
    Clock,
    Activity,
    TrendingUp,
    Users,
    Globe,
    Brain,
    Target,
    Zap,
    Eye,
    Trash2,
    Plus,
    ArrowLeft,
    Loader2,
    CheckCircle,
    AlertCircle,
    RefreshCw,
    Download,
    Calendar,
    MapPin
} from 'lucide-react';

const SimulationManagerAPI = () => {
    // State management
    const [simulations, setSimulations] = useState([]);
    const [datasets, setDatasets] = useState([]);
    const [loading, setLoading] = useState(false);
    const [creating, setCreating] = useState(false);
    const [currentView, setCurrentView] = useState('list'); // 'list', 'create', 'details'
    const [selectedSimulation, setSelectedSimulation] = useState(null);
    const [refreshing, setRefreshing] = useState(false);

    // Creation form state
    const [createForm, setCreateForm] = useState({
        name: '',
        description: '',
        model_type: '',
        dataset_id: 'none',
        parameters: {
            time_horizon: 365,
            time_steps: 365,
            population: 100000,
            beta: 0.3,          // transmission rate
            gamma: 0.1,         // recovery rate 
            sigma: 0.2,         // incubation rate (1/incubation_period)
            mu: 0.0,            // mortality rate
            initial_infected: 10,
            initial_exposed: 0
        }
    });

    // Load data on component mount
    useEffect(() => {
        loadSimulations();
        loadDatasets();
    }, []);

    const loadSimulations = async () => {
        try {
            setLoading(true);
            const response = await ApiService.getSimulations();
            setSimulations(Array.isArray(response) ? response : response.simulations || []);
        } catch (error) {
            toast.error(`Failed to load simulations: ${error.message}`);
            setSimulations([]);
        } finally {
            setLoading(false);
        }
    };

    const loadDatasets = async () => {
        try {
            const response = await ApiService.getDatasets();
            const datasetsData = Array.isArray(response) ? response : response.datasets || [];
            setDatasets(datasetsData.filter(d => d.status === 'completed'));
        } catch (error) {
            console.error('Failed to load datasets:', error);
            setDatasets([]);
        }
    };

    const refreshSimulations = async () => {
        setRefreshing(true);
        await loadSimulations();
        setRefreshing(false);
        toast.success('Simulations refreshed');
    };

    const handleCreateSimulation = async () => {
        if (!createForm.name.trim() || !createForm.model_type) {
            toast.error('Please provide simulation name and model type');
            return;
        }

        try {
            setCreating(true);
            const simulationData = {
                ...createForm,
                name: createForm.name.trim(),
                description: createForm.description.trim(),
                dataset_id: createForm.dataset_id === 'none' ? null : parseInt(createForm.dataset_id) || null,
                parameters: createForm.parameters
            };

            await ApiService.createSimulation(simulationData);
            
            // Reset form
            setCreateForm({
                name: '',
                description: '',
                model_type: '',
                dataset_id: 'none',
                parameters: {
                    time_horizon: 365,
                    time_steps: 365,
                    population: 100000,
                    beta: 0.3,
                    gamma: 0.1,
                    sigma: 0.2,
                    mu: 0.0,
                    initial_infected: 10,
                    initial_exposed: 0
                }
            });

            await loadSimulations();
            setCurrentView('list');
            toast.success('Simulation created successfully!');

        } catch (error) {
            toast.error(`Failed to create simulation: ${error.message}`);
        } finally {
            setCreating(false);
        }
    };

    const handleRunSimulation = async (simulation) => {
        try {
            await ApiService.runSimulation(simulation.id);
            await loadSimulations();
            toast.success(`Simulation "${simulation.name}" started`);
        } catch (error) {
            toast.error(`Failed to run simulation: ${error.message}`);
        }
    };

    const handleDeleteSimulation = async (simulation) => {
        if (!confirm(`Are you sure you want to delete "${simulation.name}"?`)) {
            return;
        }

        try {
            await ApiService.deleteSimulation(simulation.id);
            await loadSimulations();
            toast.success('Simulation deleted successfully');
        } catch (error) {
            toast.error(`Failed to delete simulation: ${error.message}`);
        }
    };

    const handleViewDetails = async (simulation) => {
        try {
            setLoading(true);
            const details = await ApiService.getSimulation(simulation.id);
            setSelectedSimulation(details);
            setCurrentView('details');
        } catch (error) {
            toast.error(`Failed to load simulation details: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const getStatusBadge = (status) => {
        const statusConfig = {
            'pending': { variant: 'secondary', icon: Clock, text: 'Pending' },
            'running': { variant: 'default', icon: Loader2, text: 'Running' },
            'completed': { variant: 'success', icon: CheckCircle, text: 'Completed' },
            'failed': { variant: 'destructive', icon: AlertCircle, text: 'Failed' }
        };
        
        const config = statusConfig[status] || statusConfig['pending'];
        const Icon = config.icon;
        
        return (
            <Badge variant={config.variant} className="flex items-center gap-1">
                <Icon className={`h-3 w-3 ${status === 'running' ? 'animate-spin' : ''}`} />
                {config.text}
            </Badge>
        );
    };

    const getModelIcon = (modelType) => {
        const icons = {
            'seir': Brain,
            'agent_based': Users,
            'network': Globe,
            'ml_forecast': TrendingUp
        };
        return icons[modelType] || Activity;
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'Unknown';
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatDuration = (seconds) => {
        if (!seconds) return 'Unknown';
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
        return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
    };

    // Render create simulation form
    if (currentView === 'create') {
        return (
            <div className="space-y-6">
                <div className="flex items-center gap-4">
                    <Button
                        variant="ghost"
                        onClick={() => setCurrentView('list')}
                        className="flex items-center gap-2"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Back to Simulations
                    </Button>
                    <h2 className="text-2xl font-bold">Create New Simulation</h2>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Form */}
                    <Card className="lg:col-span-2">
                        <CardHeader>
                            <CardTitle>Simulation Configuration</CardTitle>
                            <CardDescription>
                                Configure your epidemiological simulation parameters
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            {/* Basic Info */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label htmlFor="name">Simulation Name</Label>
                                    <Input
                                        id="name"
                                        value={createForm.name}
                                        onChange={(e) => setCreateForm(prev => ({ ...prev, name: e.target.value }))}
                                        placeholder="Enter simulation name"
                                        disabled={creating}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="model_type">Model Type</Label>
                                    <Select
                                        value={createForm.model_type}
                                        onValueChange={(value) => setCreateForm(prev => ({ ...prev, model_type: value }))}
                                        disabled={creating}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select model type" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="seir">SEIR Model</SelectItem>
                                            <SelectItem value="agent_based">Agent-Based Model</SelectItem>
                                            <SelectItem value="network">Network Model</SelectItem>
                                            <SelectItem value="ml_forecast">ML Forecast</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="description">Description</Label>
                                <Textarea
                                    id="description"
                                    value={createForm.description}
                                    onChange={(e) => setCreateForm(prev => ({ ...prev, description: e.target.value }))}
                                    placeholder="Describe your simulation objectives and methodology"
                                    disabled={creating}
                                />
                            </div>

                            {/* Dataset Selection */}
                            <div className="space-y-2">
                                <Label htmlFor="dataset">Dataset (Optional)</Label>
                                <Select
                                    value={createForm.dataset_id}
                                    onValueChange={(value) => setCreateForm(prev => ({ ...prev, dataset_id: value }))}
                                    disabled={creating}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select dataset" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="none">No dataset</SelectItem>
                                        {datasets.map((dataset) => (
                                            <SelectItem key={dataset.id} value={dataset.id.toString()}>
                                                {dataset.name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            {/* Parameters */}
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold">Model Parameters</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="time_horizon">Time Horizon (days)</Label>
                                        <Input
                                            id="time_horizon"
                                            type="number"
                                            value={createForm.parameters.time_horizon}
                                            onChange={(e) => setCreateForm(prev => ({
                                                ...prev,
                                                parameters: {
                                                    ...prev.parameters,
                                                    time_horizon: parseInt(e.target.value) || 365
                                                }
                                            }))}
                                            disabled={creating}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="population">Population Size</Label>
                                        <Input
                                            id="population"
                                            type="number"
                                            value={createForm.parameters.population}
                                            onChange={(e) => setCreateForm(prev => ({
                                                ...prev,
                                                parameters: {
                                                    ...prev.parameters,
                                                    population: parseInt(e.target.value) || 100000
                                                }
                                            }))}
                                            disabled={creating}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="beta">Transmission Rate (β)</Label>
                                        <Input
                                            id="beta"
                                            type="number"
                                            step="0.01"
                                            value={createForm.parameters.beta}
                                            onChange={(e) => setCreateForm(prev => ({
                                                ...prev,
                                                parameters: {
                                                    ...prev.parameters,
                                                    beta: parseFloat(e.target.value) || 0.3
                                                }
                                            }))}
                                            disabled={creating}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="gamma">Recovery Rate (γ)</Label>
                                        <Input
                                            id="gamma"
                                            type="number"
                                            step="0.01"
                                            value={createForm.parameters.gamma}
                                            onChange={(e) => setCreateForm(prev => ({
                                                ...prev,
                                                parameters: {
                                                    ...prev.parameters,
                                                    gamma: parseFloat(e.target.value) || 0.1
                                                }
                                            }))}
                                            disabled={creating}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="sigma">Incubation Rate (σ)</Label>
                                        <Input
                                            id="sigma"
                                            type="number"
                                            step="0.01"
                                            value={createForm.parameters.sigma}
                                            onChange={(e) => setCreateForm(prev => ({
                                                ...prev,
                                                parameters: {
                                                    ...prev.parameters,
                                                    sigma: parseFloat(e.target.value) || 0.2
                                                }
                                            }))}
                                            disabled={creating}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="initial_infected">Initial Infected</Label>
                                        <Input
                                            id="initial_infected"
                                            type="number"
                                            value={createForm.parameters.initial_infected}
                                            onChange={(e) => setCreateForm(prev => ({
                                                ...prev,
                                                parameters: {
                                                    ...prev.parameters,
                                                    initial_infected: parseInt(e.target.value) || 10
                                                }
                                            }))}
                                            disabled={creating}
                                        />
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Actions */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Actions</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <Button
                                onClick={handleCreateSimulation}
                                disabled={creating || !createForm.name.trim() || !createForm.model_type}
                                className="w-full"
                            >
                                {creating ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Creating...
                                    </>
                                ) : (
                                    <>
                                        <Plus className="mr-2 h-4 w-4" />
                                        Create Simulation
                                    </>
                                )}
                            </Button>
                            <Button
                                variant="outline"
                                onClick={() => setCurrentView('list')}
                                className="w-full"
                                disabled={creating}
                            >
                                Cancel
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    // Render simulation details
    if (currentView === 'details' && selectedSimulation) {
        return (
            <div className="space-y-6">
                <div className="flex items-center gap-4">
                    <Button
                        variant="ghost"
                        onClick={() => setCurrentView('list')}
                        className="flex items-center gap-2"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Back to Simulations
                    </Button>
                    <h2 className="text-2xl font-bold">{selectedSimulation.name}</h2>
                    {getStatusBadge(selectedSimulation.status)}
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Simulation Info */}
                    <Card className="lg:col-span-2">
                        <CardHeader>
                            <CardTitle>Simulation Details</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <Label className="text-sm font-medium">Description</Label>
                                <p className="text-sm text-muted-foreground mt-1">
                                    {selectedSimulation.description || 'No description provided'}
                                </p>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <Label className="text-sm font-medium">Model Type</Label>
                                    <p className="text-sm text-muted-foreground mt-1 capitalize">
                                        {selectedSimulation.model_type?.replace('_', ' ')}
                                    </p>
                                </div>
                                <div>
                                    <Label className="text-sm font-medium">Duration</Label>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        {formatDuration(selectedSimulation.execution_time)}
                                    </p>
                                </div>
                                <div>
                                    <Label className="text-sm font-medium">Created</Label>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        {formatDate(selectedSimulation.created_at)}
                                    </p>
                                </div>
                                <div>
                                    <Label className="text-sm font-medium">Completed</Label>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        {formatDate(selectedSimulation.completed_at)}
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Actions */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Actions</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            <Button
                                variant="outline"
                                className="w-full justify-start"
                                onClick={() => handleRunSimulation(selectedSimulation)}
                                disabled={selectedSimulation.status === 'running'}
                            >
                                <Play className="mr-2 h-4 w-4" />
                                Run Simulation
                            </Button>
                            <Button
                                variant="outline"
                                className="w-full justify-start"
                            >
                                <BarChart3 className="mr-2 h-4 w-4" />
                                View Results
                            </Button>
                            <Button
                                variant="outline"
                                className="w-full justify-start"
                            >
                                <Download className="mr-2 h-4 w-4" />
                                Export Data
                            </Button>
                            <Button
                                variant="destructive"
                                className="w-full justify-start"
                                onClick={() => handleDeleteSimulation(selectedSimulation)}
                            >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        );
    }

    // Render main simulations list
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h2 className="text-2xl font-bold">Simulation Management</h2>
                    <p className="text-muted-foreground">
                        Create and manage epidemiological simulations
                    </p>
                </div>
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        onClick={refreshSimulations}
                        disabled={refreshing}
                    >
                        <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                    <Button onClick={() => setCurrentView('create')}>
                        <Plus className="h-4 w-4 mr-2" />
                        New Simulation
                    </Button>
                </div>
            </div>

            {/* Loading State */}
            {loading && (
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin" />
                    <span className="ml-2">Loading simulations...</span>
                </div>
            )}

            {/* Empty State */}
            {!loading && simulations.length === 0 && (
                <Card>
                    <CardContent className="pt-6">
                        <div className="text-center py-12">
                            <Brain className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No simulations found</h3>
                            <p className="text-muted-foreground mb-4">
                                Get started by creating your first epidemiological simulation
                            </p>
                            <Button onClick={() => setCurrentView('create')}>
                                <Plus className="h-4 w-4 mr-2" />
                                Create Simulation
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Simulations Grid */}
            {!loading && simulations.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {simulations.map((simulation) => {
                        const ModelIcon = getModelIcon(simulation.model_type);
                        return (
                            <Card key={simulation.id} className="hover:shadow-md transition-shadow">
                                <CardHeader className="pb-3">
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-center gap-2">
                                            <ModelIcon className="h-5 w-5 text-blue-600" />
                                            <CardTitle className="text-lg">
                                                {simulation.name}
                                            </CardTitle>
                                        </div>
                                        {getStatusBadge(simulation.status)}
                                    </div>
                                    <CardDescription className="capitalize">
                                        {simulation.model_type?.replace('_', ' ')} Model
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <p className="text-sm text-muted-foreground line-clamp-2">
                                        {simulation.description || 'No description provided'}
                                    </p>
                                    
                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                        <div>
                                            <span className="font-medium">Created:</span>
                                            <span className="ml-1 text-muted-foreground">
                                                {formatDate(simulation.created_at)}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="font-medium">Duration:</span>
                                            <span className="ml-1 text-muted-foreground">
                                                {formatDuration(simulation.execution_time)}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="flex gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleViewDetails(simulation)}
                                            className="flex-1"
                                        >
                                            <Eye className="h-3 w-3 mr-1" />
                                            View
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleRunSimulation(simulation)}
                                            disabled={simulation.status === 'running'}
                                        >
                                            <Play className="h-3 w-3" />
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleDeleteSimulation(simulation)}
                                            className="text-red-600 hover:text-red-700"
                                        >
                                            <Trash2 className="h-3 w-3" />
                                        </Button>
                                    </div>
                                </CardContent>
                            </Card>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

export default SimulationManagerAPI;