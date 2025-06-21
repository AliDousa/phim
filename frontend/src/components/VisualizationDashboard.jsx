import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx';
import { Button } from '@/components/ui/button.jsx';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert.jsx';
import { Skeleton } from '@/components/ui/skeleton.jsx';
import { 
  BarChart3, Download, RefreshCw, AlertCircle, Inbox, LineChart as LineChartIcon, Eye
} from 'lucide-react';

// This is a placeholder for your actual JWT token.
const MOCK_JWT_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...";

// --- Reusable Chart Components ---

// A generic component for displaying loading or empty states for charts
const ChartPlaceholder = ({ message, icon: Icon }) => (
  <Card>
    <CardContent className="h-[400px] flex flex-col items-center justify-center text-center">
      <Icon className="h-12 w-12 text-gray-400 mb-4" />
      <p className="font-medium text-gray-600">{message}</p>
    </CardContent>
  </Card>
);

// Chart for regional data, now powered by fetched data
function RegionalChart({ data, isLoading }) {
  if (isLoading) return <Skeleton className="h-[460px] w-full" />;
  if (!data || data.length === 0) {
    return <ChartPlaceholder message="No regional data to display for this dataset." icon={BarChart3} />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <BarChart3 className="h-5 w-5" />
          <span>Regional Distribution</span>
        </CardTitle>
        <CardDescription>Total cases and deaths by region</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="region" />
            <YAxis />
            <Tooltip formatter={(value) => value.toLocaleString()} />
            <Legend />
            <Bar dataKey="cases" fill="#f59e0b" name="Total Cases" />
            <Bar dataKey="deaths" fill="#ef4444" name="Total Deaths" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

// Chart for daily trends, now powered by fetched data
function DailyTrendChart({ data, isLoading }) {
  if (isLoading) return <Skeleton className="h-[460px] w-full" />;
  if (!data || data.length === 0) {
    return <ChartPlaceholder message="No time-series data available." icon={LineChartIcon} />;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <LineChartIcon className="h-5 w-5" />
          <span>Daily Trends</span>
        </CardTitle>
        <CardDescription>New cases and deaths over time</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip formatter={(value) => value.toLocaleString()} />
            <Legend />
            <Line type="monotone" dataKey="new_cases" name="New Cases" stroke="#f59e0b" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="new_deaths" name="New Deaths" stroke="#ef4444" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}


// Overview of key metrics, now powered by fetched data
function MetricsOverview({ data, isLoading }) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-32 w-full" />)}
      </div>
    );
  }
  if (!data || data.totalCases === 0) {
    return <ChartPlaceholder message="No data to calculate key metrics." icon={Eye} />;
  }
  
  const pieData = [
    { name: 'Active Cases', value: data.activeCases, color: '#f59e0b' },
    { name: 'Deaths', value: data.totalDeaths, color: '#ef4444' }
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
       <Card>
        <CardHeader>
          <CardTitle>Key Metrics</CardTitle>
          <CardDescription>Summary statistics for the selected dataset</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{data.totalCases.toLocaleString()}</div>
              <div className="text-sm text-gray-600">Total Cases</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">{data.totalDeaths.toLocaleString()}</div>
              <div className="text-sm text-gray-600">Total Deaths</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">{data.activeCases.toLocaleString()}</div>
              <div className="text-sm text-gray-600">Active Cases</div>
            </div>
            <div className="text-center p-4 bg-red-100 rounded-lg">
              <div className="text-2xl font-bold text-red-700">{data.mortalityRate}%</div>
              <div className="text-sm text-gray-600">Mortality Rate</div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Case Distribution</CardTitle>
          <CardDescription>Breakdown of case outcomes</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                {pieData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
              </Pie>
              <Tooltip formatter={(value) => value.toLocaleString()} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}


// --- Main Visualization Dashboard Component ---
export default function VisualizationDashboard() {
  // State for managing datasets and selection
  const [datasets, setDatasets] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const [isListLoading, setIsListLoading] = useState(true);
  const [listError, setListError] = useState(null);

  // State for managing data of the selected dataset
  const [dataPoints, setDataPoints] = useState([]);
  const [isDataLoading, setIsDataLoading] = useState(false);
  const [dataError, setDataError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  
  // Fetch the list of available datasets on component mount
  const fetchDatasetList = useCallback(async () => {
    setIsListLoading(true);
    setListError(null);
    try {
      const response = await fetch('/api/datasets', {
        headers: { 'Authorization': `Bearer ${MOCK_JWT_TOKEN}` }
      });
      if (!response.ok) throw new Error('Failed to fetch dataset list.');
      const data = await response.json();
      setDatasets(data.datasets || []);
    } catch (err) {
      setListError(err.message);
    } finally {
      setIsListLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDatasetList();
  }, [fetchDatasetList]);

  // Fetch data for the selected dataset
  const fetchDatasetData = useCallback(async (datasetId) => {
    if (!datasetId) {
      setDataPoints([]);
      return;
    }
    setIsDataLoading(true);
    setDataError(null);
    try {
      // Fetch all data points for the selected dataset
      const response = await fetch(`/api/datasets/${datasetId}/data?limit=10000`, { // Adjust limit as needed
        headers: { 'Authorization': `Bearer ${MOCK_JWT_TOKEN}` }
      });
      if (!response.ok) throw new Error('Failed to fetch data for the selected dataset.');
      const data = await response.json();
      setDataPoints(data.data_points || []);
      setLastUpdated(new Date());
    } catch (err) {
      setDataError(err.message);
    } finally {
      setIsDataLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedDatasetId) {
      fetchDatasetData(selectedDatasetId);
    }
  }, [selectedDatasetId, fetchDatasetData]);

  // --- Data Processing with useMemo for performance ---
  
  const regionalData = useMemo(() => {
    if (!dataPoints) return [];
    const regions = {};
    dataPoints.forEach(p => {
      if (!regions[p.location]) {
        regions[p.location] = { region: p.location, cases: 0, deaths: 0 };
      }
      regions[p.location].cases += p.new_cases || 0;
      regions[p.location].deaths += p.new_deaths || 0;
    });
    return Object.values(regions);
  }, [dataPoints]);

  const dailyData = useMemo(() => {
    if (!dataPoints) return [];
    const daily = {};
    dataPoints.forEach(p => {
      const date = new Date(p.timestamp).toLocaleDateString();
      if (!daily[date]) {
        daily[date] = { date, new_cases: 0, new_deaths: 0 };
      }
      daily[date].new_cases += p.new_cases || 0;
      daily[date].new_deaths += p.new_deaths || 0;
    });
    return Object.values(daily).sort((a,b) => new Date(a.date) - new Date(b.date));
  }, [dataPoints]);

  const keyMetrics = useMemo(() => {
    if (!dataPoints || dataPoints.length === 0) return null;
    const totalCases = regionalData.reduce((sum, r) => sum + r.cases, 0);
    const totalDeaths = regionalData.reduce((sum, r) => sum + r.deaths, 0);
    const mortalityRate = totalCases > 0 ? ((totalDeaths / totalCases) * 100).toFixed(2) : 0;
    const activeCases = totalCases - totalDeaths; // Simplified for this example

    return { totalCases, totalDeaths, mortalityRate, activeCases };
  }, [regionalData]);

  // --- Event Handlers ---
  const handleRefresh = () => {
    if (selectedDatasetId) {
      fetchDatasetData(selectedDatasetId);
    }
  };

  const handleExport = () => {
    if (!selectedDatasetId) {
      alert("Please select a dataset to export.");
      return;
    }
    window.open(`/api/datasets/${selectedDatasetId}/export?format=csv`);
  };

  // --- Render Logic ---
  if (isListLoading) {
    return <div className="p-6"><Skeleton className="h-12 w-1/2" /></div>;
  }

  if (listError) {
    return (
      <Alert variant="destructive" className="m-6">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{listError}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="w-full md:w-1/3">
          <Select onValueChange={setSelectedDatasetId} value={selectedDatasetId}>
            <SelectTrigger>
              <SelectValue placeholder="Select a dataset to visualize..." />
            </SelectTrigger>
            <SelectContent>
              {datasets.length > 0 ? (
                datasets.map(d => <SelectItem key={d.id} value={d.id.toString()}>{d.name}</SelectItem>)
              ) : (
                <div className="p-4 text-center text-sm text-gray-500">No datasets found.</div>
              )}
            </SelectContent>
          </Select>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={handleRefresh} disabled={!selectedDatasetId || isDataLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isDataLoading ? 'animate-spin' : ''}`} />
            {isDataLoading ? 'Loading...' : 'Refresh'}
          </Button>
          <Button variant="outline" onClick={handleExport} disabled={!selectedDatasetId}>
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>
      
      {dataError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error Loading Data</AlertTitle>
          <AlertDescription>{dataError}</AlertDescription>
        </Alert>
      )}

      {/* Conditional Rendering based on selection */}
      {!selectedDatasetId ? (
        <div className="flex flex-col items-center justify-center p-16 text-center border-2 border-dashed rounded-lg">
          <Inbox className="h-16 w-16 text-gray-300 mb-4" />
          <p className="font-medium text-lg">Please select a dataset</p>
          <p className="text-sm text-gray-500">Choose a dataset from the dropdown above to view visualizations.</p>
        </div>
      ) : (
        <div className="space-y-6">
          <MetricsOverview data={keyMetrics} isLoading={isDataLoading} />
          <RegionalChart data={regionalData} isLoading={isDataLoading} />
          <DailyTrendChart data={dailyData} isLoading={isDataLoading} />
        </div>
      )}
    </div>
  );
}