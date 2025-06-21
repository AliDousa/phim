import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Activity, Beaker, Database, PlusCircle, ArrowRight } from 'lucide-react';
import { Toaster, toast } from 'sonner';

// Helper to get a badge color based on status
const getStatusBadgeVariant = (status) => {
    switch (status) {
        case 'completed': return 'success';
        case 'running': return 'secondary';
        case 'failed': return 'destructive';
        default: return 'outline';
    }
};

export default function Dashboard({ setActiveView, onSelectSimulation }) {
    const [stats, setStats] = useState({ datasets: 0, simulations: 0, running: 0 });
    const [recentSimulations, setRecentSimulations] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const authToken = localStorage.getItem('authToken');

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                const [simulationsRes, datasetsRes] = await Promise.all([
                    fetch('/api/simulations', { headers: { 'Authorization': `Bearer ${authToken}` } }),
                    fetch('/api/datasets', { headers: { 'Authorization': `Bearer ${authToken}` } })
                ]);

                const simulationsData = await simulationsRes.json();
                const datasetsData = await datasetsRes.json();

                if (simulationsRes.ok && simulationsData.simulations) {
                    const sims = simulationsData.simulations;
                    setStats(prev => ({
                        ...prev,
                        simulations: sims.length,
                        running: sims.filter(s => s.status === 'running').length
                    }));
                    // Sort by creation date descending and take the top 5
                    setRecentSimulations(sims.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 5));
                } else {
                    toast.error("Could not load simulation stats.");
                }

                if (datasetsRes.ok && datasetsData.datasets) {
                    setStats(prev => ({ ...prev, datasets: datasetsData.datasets.length }));
                } else {
                    toast.error("Could not load dataset stats.");
                }

            } catch (error) {
                toast.error('An error occurred while fetching dashboard data.');
                console.error(error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, [authToken]);

    return (
        <div className="p-4 md:p-6 space-y-6">
            <Toaster richColors />
            <h1 className="text-3xl font-bold">Platform Dashboard</h1>

            {/* Stat Cards */}
            <div className="grid gap-4 md:grid-cols-3">
                {isLoading ? (
                    Array.from({ length: 3 }).map((_, i) => <Card key={i}><CardHeader><Skeleton className="h-6 w-1/2" /></CardHeader><CardContent><Skeleton className="h-10 w-3/4" /></CardContent></Card>)
                ) : (
                    <>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Total Datasets</CardTitle>
                                <Database className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{stats.datasets}</div>
                                <p className="text-xs text-muted-foreground">Managed datasets</p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Total Simulations</CardTitle>
                                <Beaker className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{stats.simulations}</div>
                                <p className="text-xs text-muted-foreground">Analyses performed</p>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Simulations in Progress</CardTitle>
                                <Activity className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{stats.running}</div>
                                <p className="text-xs text-muted-foreground">Currently running models</p>
                            </CardContent>
                        </Card>
                    </>
                )}
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                {/* Recent Activity */}
                <Card>
                    <CardHeader>
                        <CardTitle>Recent Activity</CardTitle>
                        <CardDescription>Your 5 most recently created simulations.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {isLoading ? (
                            Array.from({ length: 5 }).map((_, i) => <div key={i} className="flex items-center justify-between p-2"><Skeleton className="h-5 w-1/2" /><Skeleton className="h-5 w-1/4" /></div>)
                        ) : (
                            <div className="space-y-4">
                                {recentSimulations.map(sim => (
                                    <div key={sim.id} className="flex items-center">
                                        <div className="flex-1">
                                            <p className="font-medium">{sim.name}</p>
                                            <p className="text-sm text-muted-foreground">{sim.model_type.toUpperCase()} - {new Date(sim.created_at).toLocaleDateString()}</p>
                                        </div>
                                        <Badge variant={getStatusBadgeVariant(sim.status)}>{sim.status}</Badge>
                                        {sim.status === 'completed' && (
                                            <Button variant="ghost" size="sm" className="ml-2" onClick={() => onSelectSimulation(sim.id)}>
                                                View <ArrowRight className="h-4 w-4 ml-1" />
                                            </Button>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Quick Actions */}
                <Card>
                    <CardHeader>
                        <CardTitle>Quick Actions</CardTitle>
                        <CardDescription>Jump directly to common tasks.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <Button className="w-full justify-start" onClick={() => setActiveView('datasets')}>
                            <PlusCircle className="mr-2 h-4 w-4" /> Upload New Dataset
                        </Button>
                        <Button className="w-full justify-start" onClick={() => setActiveView('simulations')}>
                            <Beaker className="mr-2 h-4 w-4" /> Create New Simulation
                        </Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}