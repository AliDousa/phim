import React, { useState, useEffect, useCallback } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Toaster, toast } from 'sonner';

// Helper to get a badge color based on status
const getStatusBadgeVariant = (status) => {
    switch (status) {
        case 'completed': return 'success';
        case 'running': return 'secondary';
        case 'failed': return 'destructive';
        case 'pending': return 'outline';
        default: return 'default';
    }
};

// Defines the parameters for each model type
const modelParametersConfig = {
    seir: [
        { name: 'beta', label: 'Beta (Transmission Rate)', type: 'number', defaultValue: 0.5 },
        { name: 'sigma', label: 'Sigma (Incubation Rate)', type: 'number', defaultValue: 0.2 },
        { name: 'gamma', label: 'Gamma (Recovery Rate)', type: 'number', defaultValue: 0.1 },
        { name: 'population', label: 'Population', type: 'number', defaultValue: 100000 },
        { name: 'time_horizon', label: 'Time Horizon (days)', type: 'number', defaultValue: 365 },
    ],
    ml_forecast: [
        { name: 'ml_model_type', label: 'ML Model', type: 'select', options: ['ensemble', 'random_forest', 'gradient_boosting'], defaultValue: 'ensemble' },
        { name: 'target_column', label: 'Target Column', type: 'select', options: ['infectious', 'new_cases', 'deaths'], defaultValue: 'new_cases' },
        { name: 'forecast_horizon', label: 'Forecast Horizon (days)', type: 'number', defaultValue: 30 },
    ],
    // Add other models like agent_based or network here
};

export default function SimulationManager({ onSelectSimulation }) {
    const [simulations, setSimulations] = useState([]);
    const [datasets, setDatasets] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    // Form state
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [modelType, setModelType] = useState('seir');
    const [datasetId, setDatasetId] = useState('');
    const [parameters, setParameters] = useState({});

    const authToken = localStorage.getItem('authToken'); // Assume token is stored in localStorage

    // Fetch initial data for simulations and datasets
    const fetchData = useCallback(async () => {
        setIsLoading(true);
        try {
            const [simulationsRes, datasetsRes] = await Promise.all([
                fetch('/api/simulations', { headers: { 'Authorization': `Bearer ${authToken}` } }),
                fetch('/api/datasets', { headers: { 'Authorization': `Bearer ${authToken}` } })
            ]);
            const simulationsData = await simulationsRes.json();
            const datasetsData = await datasetsRes.json();

            if (simulationsRes.ok) {
                setSimulations(simulationsData.simulations || []);
            } else {
                toast.error('Failed to fetch simulations:', simulationsData.error);
            }
            if (datasetsRes.ok) {
                setDatasets(datasetsData.datasets || []);
            } else {
                toast.error('Failed to fetch datasets:', datasetsData.error);
            }
        } catch (error) {
            toast.error('An error occurred while fetching data.');
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    }, [authToken]);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 15000); // Poll for status updates every 15 seconds
        return () => clearInterval(interval);
    }, [fetchData]);

    // Update parameters state when modelType changes
    useEffect(() => {
        const defaultConfig = modelParametersConfig[modelType] || [];
        const defaultParams = defaultConfig.reduce((acc, param) => {
            acc[param.name] = param.defaultValue;
            return acc;
        }, {});
        setParameters(defaultParams);
    }, [modelType]);

    const handleParameterChange = (name, value) => {
        setParameters(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!name || !modelType || (modelType === 'ml_forecast' && !datasetId)) {
            toast.error("Please fill in all required fields.");
            return;
        }

        const payload = {
            name,
            description,
            model_type: modelType,
            dataset_id: modelType.includes('forecast') ? parseInt(datasetId, 10) : null,
            parameters,
        };

        try {
            const response = await fetch('/api/simulations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`,
                },
                body: JSON.stringify(payload),
            });

            const result = await response.json();
            if (response.ok) {
                toast.success(`Simulation "${result.simulation.name}" created successfully.`);
                setSimulations(prev => [result.simulation, ...prev]);
                // Reset form
                setName('');
                setDescription('');
            } else {
                toast.error(`Failed to create simulation: ${result.error}`);
            }
        } catch (error) {
            toast.error("An error occurred while creating the simulation.");
            console.error(error);
        }
    };

    const renderParameterFields = () => {
        const config = modelParametersConfig[modelType] || [];
        return config.map(param => (
            <div key={param.name}>
                <Label htmlFor={param.name}>{param.label}</Label>
                {param.type === 'select' ? (
                    <Select value={parameters[param.name] || ''} onValueChange={(value) => handleParameterChange(param.name, value)}>
                        <SelectTrigger>
                            <SelectValue placeholder={`Select ${param.label}`} />
                        </SelectTrigger>
                        <SelectContent>
                            {param.options.map(opt => <SelectItem key={opt} value={opt}>{opt}</SelectItem>)}
                        </SelectContent>
                    </Select>
                ) : (
                    <Input
                        id={param.name}
                        type={param.type}
                        value={parameters[param.name] || ''}
                        onChange={(e) => handleParameterChange(param.name, e.target.type === 'number' ? parseFloat(e.target.value) : e.target.value)}
                    />
                )}
            </div>
        ));
    };


    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-4 md:p-6">
            <Toaster richColors />
            <div className="lg:col-span-1">
                <Card>
                    <CardHeader>
                        <CardTitle>Create New Simulation</CardTitle>
                        <CardDescription>Configure and launch a new epidemiological model.</CardDescription>
                    </CardHeader>
                    <form onSubmit={handleSubmit}>
                        <CardContent className="space-y-4">
                            <div>
                                <Label htmlFor="name">Simulation Name</Label>
                                <Input id="name" placeholder="e.g., Regional Flu Forecast" value={name} onChange={e => setName(e.target.value)} required />
                            </div>
                            <div>
                                <Label htmlFor="description">Description</Label>
                                <Textarea id="description" placeholder="A brief description of the simulation's purpose." value={description} onChange={e => setDescription(e.target.value)} />
                            </div>
                            <div>
                                <Label htmlFor="modelType">Model Type</Label>
                                <Select value={modelType} onValueChange={setModelType}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select a model" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="seir">SEIR Model</SelectItem>
                                        <SelectItem value="ml_forecast">ML Forecast</SelectItem>
                                        <SelectItem value="agent_based" disabled>Agent Based (coming soon)</SelectItem>
                                        <SelectItem value="network" disabled>Network Model (coming soon)</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            {modelType.includes('forecast') && (
                                <div>
                                    <Label htmlFor="dataset">Dataset (for ML)</Label>
                                    <Select value={datasetId} onValueChange={setDatasetId} required>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select a dataset" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {datasets.map(d => <SelectItem key={d.id} value={String(d.id)}>{d.name}</SelectItem>)}
                                        </SelectContent>
                                    </Select>
                                </div>
                            )}

                            <div className="space-y-2 pt-4">
                                <h4 className="font-medium">Model Parameters</h4>
                                {renderParameterFields()}
                            </div>

                        </CardContent>
                        <CardFooter>
                            <Button type="submit" className="w-full">Launch Simulation</Button>
                        </CardFooter>
                    </form>
                </Card>
            </div>

            <div className="lg:col-span-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Simulation History</CardTitle>
                        <CardDescription>List of all your past and present simulations.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Name</TableHead>
                                    <TableHead>Model</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Created At</TableHead>
                                    <TableHead>Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {isLoading ? (
                                    <TableRow><TableCell colSpan="5" className="text-center">Loading simulations...</TableCell></TableRow>
                                ) : (
                                    simulations.map(sim => (
                                        <TableRow key={sim.id}>
                                            <TableCell className="font-medium">{sim.name}</TableCell>
                                            <TableCell>{sim.model_type}</TableCell>
                                            <TableCell><Badge variant={getStatusBadgeVariant(sim.status)}>{sim.status}</Badge></TableCell>
                                            <TableCell>{new Date(sim.created_at).toLocaleString()}</TableCell>
                                            <TableCell>
                                                <Button variant="outline" size="sm" onClick={() => onSelectSimulation(sim.id)} disabled={sim.status !== 'completed'}>
                                                    View Results
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}