import React, { useState, useEffect } from 'react'
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Users, 
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3,
  Download,
  RefreshCw
} from 'lucide-react'

// Sample data for demonstrations
const generateSEIRData = () => {
  const data = []
  for (let day = 0; day <= 365; day += 7) {
    const t = day / 365
    const susceptible = 100000 * Math.exp(-2 * t)
    const exposed = 5000 * Math.sin(Math.PI * t) * Math.exp(-t)
    const infectious = 3000 * Math.sin(Math.PI * t * 1.5) * Math.exp(-0.5 * t)
    const recovered = 100000 - susceptible - exposed - infectious
    
    data.push({
      day,
      date: new Date(2024, 0, day + 1).toLocaleDateString(),
      susceptible: Math.max(0, Math.round(susceptible)),
      exposed: Math.max(0, Math.round(exposed)),
      infectious: Math.max(0, Math.round(infectious)),
      recovered: Math.max(0, Math.round(recovered))
    })
  }
  return data
}

const generateForecastData = () => {
  const data = []
  const baseDate = new Date()
  
  for (let i = 0; i < 30; i++) {
    const date = new Date(baseDate)
    date.setDate(date.getDate() + i)
    
    const trend = Math.sin(i * 0.2) * 50 + 100 + i * 2
    const actual = i < 20 ? trend + (Math.random() - 0.5) * 20 : null
    const predicted = i >= 15 ? trend + (Math.random() - 0.5) * 10 : null
    const upperBound = predicted ? predicted + 15 : null
    const lowerBound = predicted ? Math.max(0, predicted - 15) : null
    
    data.push({
      date: date.toLocaleDateString(),
      day: i + 1,
      actual: actual ? Math.round(actual) : null,
      predicted: predicted ? Math.round(predicted) : null,
      upperBound: upperBound ? Math.round(upperBound) : null,
      lowerBound: lowerBound ? Math.round(lowerBound) : null
    })
  }
  return data
}

const generateRegionalData = () => [
  { region: 'North', cases: 1250, deaths: 45, recovered: 1100, population: 50000 },
  { region: 'South', cases: 890, deaths: 32, recovered: 780, population: 45000 },
  { region: 'East', cases: 1450, deaths: 58, recovered: 1200, population: 60000 },
  { region: 'West', cases: 720, deaths: 28, recovered: 650, population: 40000 },
  { region: 'Central', cases: 980, deaths: 38, recovered: 850, population: 55000 }
]

const generateModelComparisonData = () => [
  { model: 'SEIR', accuracy: 0.85, r2: 0.78, mae: 12.5, rmse: 18.3 },
  { model: 'Agent-Based', accuracy: 0.82, r2: 0.75, mae: 15.2, rmse: 21.1 },
  { model: 'Network', accuracy: 0.88, r2: 0.81, mae: 11.8, rmse: 16.9 },
  { model: 'ML Ensemble', accuracy: 0.91, r2: 0.86, mae: 9.2, rmse: 14.5 }
]

// Color schemes
const COLORS = {
  susceptible: '#3b82f6',
  exposed: '#f59e0b',
  infectious: '#ef4444',
  recovered: '#10b981',
  predicted: '#8b5cf6',
  actual: '#06b6d4'
}

const PIE_COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6']

// Chart Components
function SEIRChart({ data }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Activity className="h-5 w-5" />
          <span>SEIR Model Simulation</span>
        </CardTitle>
        <CardDescription>
          Susceptible-Exposed-Infectious-Recovered compartmental model over time
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="day" 
              label={{ value: 'Days', position: 'insideBottom', offset: -5 }}
            />
            <YAxis 
              label={{ value: 'Population', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              formatter={(value, name) => [value.toLocaleString(), name]}
              labelFormatter={(day) => `Day ${day}`}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="susceptible"
              stackId="1"
              stroke={COLORS.susceptible}
              fill={COLORS.susceptible}
              fillOpacity={0.6}
              name="Susceptible"
            />
            <Area
              type="monotone"
              dataKey="exposed"
              stackId="1"
              stroke={COLORS.exposed}
              fill={COLORS.exposed}
              fillOpacity={0.6}
              name="Exposed"
            />
            <Area
              type="monotone"
              dataKey="infectious"
              stackId="1"
              stroke={COLORS.infectious}
              fill={COLORS.infectious}
              fillOpacity={0.6}
              name="Infectious"
            />
            <Area
              type="monotone"
              dataKey="recovered"
              stackId="1"
              stroke={COLORS.recovered}
              fill={COLORS.recovered}
              fillOpacity={0.6}
              name="Recovered"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

function ForecastChart({ data }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <TrendingUp className="h-5 w-5" />
          <span>ML Forecasting with Uncertainty</span>
        </CardTitle>
        <CardDescription>
          Machine learning predictions with confidence intervals
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="day"
              label={{ value: 'Days', position: 'insideBottom', offset: -5 }}
            />
            <YAxis 
              label={{ value: 'Cases', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              formatter={(value, name) => [
                value ? value.toLocaleString() : 'N/A', 
                name
              ]}
              labelFormatter={(day) => `Day ${day}`}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="upperBound"
              stroke="none"
              fill={COLORS.predicted}
              fillOpacity={0.2}
              name="Confidence Interval"
            />
            <Area
              type="monotone"
              dataKey="lowerBound"
              stroke="none"
              fill="#ffffff"
              fillOpacity={1}
            />
            <Line
              type="monotone"
              dataKey="actual"
              stroke={COLORS.actual}
              strokeWidth={2}
              dot={{ r: 4 }}
              name="Actual Cases"
              connectNulls={false}
            />
            <Line
              type="monotone"
              dataKey="predicted"
              stroke={COLORS.predicted}
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ r: 4 }}
              name="Predicted Cases"
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

function RegionalChart({ data }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <BarChart3 className="h-5 w-5" />
          <span>Regional Distribution</span>
        </CardTitle>
        <CardDescription>
          Cases, deaths, and recoveries by region
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="region" />
            <YAxis />
            <Tooltip 
              formatter={(value, name) => [value.toLocaleString(), name]}
            />
            <Legend />
            <Bar dataKey="cases" fill={COLORS.exposed} name="Total Cases" />
            <Bar dataKey="recovered" fill={COLORS.recovered} name="Recovered" />
            <Bar dataKey="deaths" fill={COLORS.infectious} name="Deaths" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

function ModelComparisonChart({ data }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <CheckCircle className="h-5 w-5" />
          <span>Model Performance Comparison</span>
        </CardTitle>
        <CardDescription>
          Accuracy metrics for different epidemiological models
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={data} layout="horizontal">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" domain={[0, 1]} />
            <YAxis dataKey="model" type="category" width={100} />
            <Tooltip 
              formatter={(value, name) => [
                typeof value === 'number' ? value.toFixed(3) : value, 
                name
              ]}
            />
            <Legend />
            <Bar dataKey="accuracy" fill={COLORS.susceptible} name="Accuracy" />
            <Bar dataKey="r2" fill={COLORS.recovered} name="R² Score" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

function MetricsOverview({ data }) {
  const totalCases = data.reduce((sum, region) => sum + region.cases, 0)
  const totalDeaths = data.reduce((sum, region) => sum + region.deaths, 0)
  const totalRecovered = data.reduce((sum, region) => sum + region.recovered, 0)
  const totalPopulation = data.reduce((sum, region) => sum + region.population, 0)
  
  const mortalityRate = ((totalDeaths / totalCases) * 100).toFixed(2)
  const recoveryRate = ((totalRecovered / totalCases) * 100).toFixed(2)
  const incidenceRate = ((totalCases / totalPopulation) * 100000).toFixed(1)
  
  const pieData = [
    { name: 'Recovered', value: totalRecovered, color: COLORS.recovered },
    { name: 'Active', value: totalCases - totalRecovered - totalDeaths, color: COLORS.exposed },
    { name: 'Deaths', value: totalDeaths, color: COLORS.infectious }
  ]
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Key Metrics</CardTitle>
          <CardDescription>
            Summary statistics across all regions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {totalCases.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600">Total Cases</div>
            </div>
            
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {recoveryRate}%
              </div>
              <div className="text-sm text-gray-600">Recovery Rate</div>
            </div>
            
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                {mortalityRate}%
              </div>
              <div className="text-sm text-gray-600">Mortality Rate</div>
            </div>
            
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {incidenceRate}
              </div>
              <div className="text-sm text-gray-600">per 100k</div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Case Distribution</CardTitle>
          <CardDescription>
            Breakdown of case outcomes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value) => [value.toLocaleString(), 'Cases']}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}

// Main Visualization Dashboard Component
export default function VisualizationDashboard() {
  const [seirData, setSeirData] = useState([])
  const [forecastData, setForecastData] = useState([])
  const [regionalData, setRegionalData] = useState([])
  const [modelData, setModelData] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(new Date())
  
  useEffect(() => {
    // Simulate data loading
    const loadData = () => {
      setLoading(true)
      setTimeout(() => {
        setSeirData(generateSEIRData())
        setForecastData(generateForecastData())
        setRegionalData(generateRegionalData())
        setModelData(generateModelComparisonData())
        setLastUpdated(new Date())
        setLoading(false)
      }, 1000)
    }
    
    loadData()
  }, [])
  
  const refreshData = () => {
    setSeirData(generateSEIRData())
    setForecastData(generateForecastData())
    setRegionalData(generateRegionalData())
    setModelData(generateModelComparisonData())
    setLastUpdated(new Date())
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading visualizations...</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Data Visualizations</h2>
          <p className="text-gray-600">
            Last updated: {lastUpdated.toLocaleString()}
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={refreshData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>
      
      {/* Metrics Overview */}
      <MetricsOverview data={regionalData} />
      
      {/* Main Charts */}
      <Tabs defaultValue="seir" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="seir">SEIR Model</TabsTrigger>
          <TabsTrigger value="forecast">Forecasting</TabsTrigger>
          <TabsTrigger value="regional">Regional</TabsTrigger>
          <TabsTrigger value="models">Model Comparison</TabsTrigger>
        </TabsList>
        
        <TabsContent value="seir">
          <SEIRChart data={seirData} />
        </TabsContent>
        
        <TabsContent value="forecast">
          <ForecastChart data={forecastData} />
        </TabsContent>
        
        <TabsContent value="regional">
          <RegionalChart data={regionalData} />
        </TabsContent>
        
        <TabsContent value="models">
          <ModelComparisonChart data={modelData} />
        </TabsContent>
      </Tabs>
      
      {/* Status Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span className="font-medium">Data Quality</span>
              <Badge variant="outline" className="ml-auto">Excellent</Badge>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Activity className="h-5 w-5 text-blue-500" />
              <span className="font-medium">Model Status</span>
              <Badge variant="outline" className="ml-auto">Running</Badge>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-orange-500" />
              <span className="font-medium">Last Sync</span>
              <Badge variant="outline" className="ml-auto">2 min ago</Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

