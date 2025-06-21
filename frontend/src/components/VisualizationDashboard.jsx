import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Toaster, toast } from 'sonner';
import { Sigma, TrendingUp, Activity, BarChart, AlertTriangle, CheckCircle } from 'lucide-react';

const formatResultsForChart = (results, modelType) => {
  if (!results) return [];

  if (modelType === 'seir' && results.time) {
    return results.time.map((t, i) => ({
      day: Math.round(t),
      Susceptible: results.susceptible[i],
      Exposed: results.exposed[i],
      Infectious: results.infectious[i],
      Recovered: results.recovered[i],
    }));
  }

  if (modelType === 'ml_forecast' && results.predictions) {
    const horizon = results.predictions.length;
    return Array.from({ length: horizon }, (_, i) => ({
      day: i + 1,
      Prediction: results.predictions[i],
      'Lower Bound': results.confidence_intervals?.lower?.[i],
      'Upper Bound': results.confidence_intervals?.upper?.[i],
    }));
  }

  return [];
};

const MetricCard = ({ title, value, icon, description }) => (
  <Card>
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium">{title}</CardTitle>
      {icon}
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
      <p className="text-xs text-muted-foreground">{description}</p>
    </CardContent>
  </Card>
);

export default function VisualizationDashboard({ simulationId }) {
  const [simulation, setSimulation] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const authToken = localStorage.getItem('authToken');

  useEffect(() => {
    if (!simulationId) {
      setIsLoading(false);
      return;
    }

    const fetchSimulationData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(`/api/simulations/${simulationId}`, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await response.json();
        if (response.ok) {
          setSimulation(data.simulation);
        } else {
          setError(data.error || 'Failed to fetch simulation results.');
          toast.error(data.error || 'Failed to fetch simulation results.');
        }
      } catch (err) {
        setError('An error occurred while fetching data.');
        toast.error('An error occurred while fetching data.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSimulationData();
  }, [simulationId, authToken]);

  if (isLoading) {
    return <div className="p-6 space-y-4"><Skeleton className="h-8 w-1/2" /><div className="grid gap-4 md:grid-cols-3"><Skeleton className="h-24 w-full" /><Skeleton className="h-24 w-full" /><Skeleton className="h-24 w-full" /></div><Skeleton className="h-96 w-full" /></div>;
  }

  if (error) {
    return <div className="flex flex-col items-center justify-center h-full p-6"><AlertTriangle className="h-12 w-12 text-destructive" /><p className="mt-4 text-lg text-destructive">Error: {error}</p></div>;
  }

  if (!simulation) {
    return <div className="flex flex-col items-center justify-center h-full p-6"><CheckCircle className="h-12 w-12 text-primary" /><p className="mt-4 text-lg text-muted-foreground">Select a completed simulation to view its results.</p></div>;
  }

  const chartData = formatResultsForChart(simulation.results, simulation.model_type);
  const metrics = simulation.metrics || {};
  const results = simulation.results || {};

  return (
    <div className="p-4 md:p-6 space-y-6">
      <Toaster richColors />
      <div>
        <h1 className="text-3xl font-bold">Simulation Results: {simulation.name}</h1>
        <p className="text-muted-foreground">{simulation.description}</p>
      </div>

      {/* Key Metrics Panel */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {simulation.model_type === 'seir' && (
          <>
            <MetricCard title="R₀ (Reproduction No.)" value={metrics.r0?.toFixed(2) || 'N/A'} icon={<Sigma className="h-4 w-4 text-muted-foreground" />} description="Basic reproduction number" />
            <MetricCard title="Peak Infections" value={metrics.max_infections?.toLocaleString() || 'N/A'} icon={<TrendingUp className="h-4 w-4 text-muted-foreground" />} description={`Occurred on day ${metrics.peak_day}`} />
            <MetricCard title="Total Infected" value={metrics.final_recovered?.toLocaleString() || 'N/A'} icon={<Activity className="h-4 w-4 text-muted-foreground" />} description="Total individuals recovered" />
          </>
        )}
        {simulation.model_type === 'ml_forecast' && results.metrics && (
          <>
            <MetricCard title="MAE" value={results.metrics.mae?.toFixed(2) || 'N/A'} icon={<BarChart className="h-4 w-4 text-muted-foreground" />} description="Mean Absolute Error" />
            <MetricCard title="RMSE" value={results.metrics.rmse?.toFixed(2) || 'N/A'} icon={<BarChart className="h-4 w-4 text-muted-foreground" />} description="Root Mean Squared Error" />
            <MetricCard title="R² Score" value={results.metrics.r2?.toFixed(3) || 'N/A'} icon={<CheckCircle className="h-4 w-4 text-muted-foreground" />} description="Model fit score" />
          </>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{simulation.model_type.toUpperCase()} Model Visualization</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            {simulation.model_type === 'seir' ? (
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorInfectious" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#ff8042" stopOpacity={0.8} /><stop offset="95%" stopColor="#ff8042" stopOpacity={0} /></linearGradient>
                  <linearGradient id="colorRecovered" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#82ca9d" stopOpacity={0.8} /><stop offset="95%" stopColor="#82ca9d" stopOpacity={0} /></linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" label={{ value: 'Days', position: 'insideBottom', offset: -5 }} />
                <YAxis width={80} label={{ value: 'Population', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="Infectious" stroke="#ff8042" fillOpacity={1} fill="url(#colorInfectious)" />
                <Area type="monotone" dataKey="Recovered" stroke="#82ca9d" fillOpacity={1} fill="url(#colorRecovered)" />
              </AreaChart>
            ) : (
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" label={{ value: 'Days into Future', position: 'insideBottom', offset: -5 }} />
                <YAxis width={80} label={{ value: 'Value', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="Prediction" stroke="#8884d8" strokeWidth={2} dot={false} />
                {chartData[0]?.['Lower Bound'] !== undefined && <Line type="monotone" dataKey="Lower Bound" stroke="#ccc" strokeDasharray="5 5" dot={false} />}
                {chartData[0]?.['Upper Bound'] !== undefined && <Line type="monotone" dataKey="Upper Bound" stroke="#ccc" strokeDasharray="5 5" dot={false} />}
              </LineChart>
            )}
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}