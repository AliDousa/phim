import React, { useState, useCallback, useEffect } from 'react';
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
    Upload,
    FileText,
    Database,
    CheckCircle,
    AlertCircle,
    Trash2,
    Eye,
    Download,
    Plus,
    Filter,
    Search,
    Calendar,
    BarChart3,
    MapPin,
    Users,
    TrendingUp,
    FileSpreadsheet,
    File,
    Loader2,
    Cloud,
    Shield,
    Zap,
    Brain,
    Globe,
    Target,
    Clock,
    ArrowLeft,
    X,
    Sparkles,
    Activity,
    RefreshCw
} from 'lucide-react';

// Enhanced column mapping configuration
const columnMappingOptions = {
    required: [
        {
            id: 'timestamp_col',
            label: 'Date/Time Column',
            description: 'The temporal dimension of your data',
            icon: Calendar,
            examples: ['date', 'timestamp', 'time', 'report_date']
        },
        {
            id: 'location_col',
            label: 'Location Column',
            description: 'Geographic identifier (region, state, county, etc.)',
            icon: MapPin,
            examples: ['location', 'region', 'state', 'county', 'country']
        },
        {
            id: 'new_cases_col',
            label: 'New Cases Column',
            description: 'Number of new cases reported',
            icon: TrendingUp,
            examples: ['new_cases', 'cases', 'daily_cases', 'infections']
        },
        {
            id: 'new_deaths_col',
            label: 'New Deaths Column',
            description: 'Number of new deaths reported',
            icon: Activity,
            examples: ['new_deaths', 'deaths', 'daily_deaths', 'fatalities']
        }
    ],
    optional: [
        {
            id: 'population_col',
            label: 'Population Column',
            description: 'Population size for the location',
            icon: Users,
            examples: ['population', 'pop', 'total_population']
        },
        {
            id: 'hospitalizations_col',
            label: 'Hospitalizations',
            description: 'Number of hospitalizations',
            icon: Shield,
            examples: ['hospitalizations', 'hospital_admissions', 'hosp']
        },
        {
            id: 'recoveries_col',
            label: 'Recoveries',
            description: 'Number of recoveries',
            icon: CheckCircle,
            examples: ['recoveries', 'recovered', 'healed']
        },
        {
            id: 'tests_col',
            label: 'Tests Conducted',
            description: 'Number of tests performed',
            icon: Target,
            examples: ['tests', 'tests_conducted', 'testing']
        }
    ]
};

const DatasetManagerAPI = () => {
    // State management
    const [datasets, setDatasets] = useState([]);
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [currentView, setCurrentView] = useState('list'); // 'list', 'upload', 'details'
    const [selectedDataset, setSelectedDataset] = useState(null);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterStatus, setFilterStatus] = useState('all');
    const [refreshing, setRefreshing] = useState(false);

    // Upload form state
    const [uploadForm, setUploadForm] = useState({
        name: '',
        description: '',
        data_type: 'time_series',
        tags: '',
        file: null,
        columnMapping: {}
    });

    // Load datasets on component mount
    useEffect(() => {
        loadDatasets();
    }, []);

    const loadDatasets = async () => {
        try {
            setLoading(true);
            const response = await ApiService.getDatasets();
            setDatasets(Array.isArray(response) ? response : response.datasets || []);
        } catch (error) {
            toast.error(`Failed to load datasets: ${error.message}`);
            setDatasets([]);
        } finally {
            setLoading(false);
        }
    };

    const refreshDatasets = async () => {
        setRefreshing(true);
        await loadDatasets();
        setRefreshing(false);
        toast.success('Datasets refreshed');
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            // Validate file type
            const allowedTypes = ['text/csv', 'application/json', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
            const allowedExtensions = ['.csv', '.json', '.xlsx'];
            
            const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
            
            if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
                toast.error('Please upload a CSV, JSON, or Excel file');
                return;
            }

            // Validate file size (100MB limit)
            if (file.size > 100 * 1024 * 1024) {
                toast.error('File size must be less than 100MB');
                return;
            }

            setUploadForm(prev => ({
                ...prev,
                file,
                name: prev.name || file.name.replace(/\.[^/.]+$/, '')
            }));
            
            toast.success(`File "${file.name}" selected`);
        }
    };

    const handleUpload = async () => {
        if (!uploadForm.file || !uploadForm.name.trim()) {
            toast.error('Please provide both a file and dataset name');
            return;
        }

        try {
            setUploading(true);
            setUploadProgress(0);

            const formData = new FormData();
            formData.append('file', uploadForm.file);
            formData.append('name', uploadForm.name.trim());
            formData.append('data_type', uploadForm.data_type);
            formData.append('description', uploadForm.description.trim());
            formData.append('tags', uploadForm.tags.trim());
            
            // Add column mapping (required by backend)
            const defaultColumnMapping = {
                timestamp_col: 'date',
                location_col: 'location', 
                new_cases_col: 'new_cases',
                new_deaths_col: 'new_deaths',
                population_col: 'population'
            };
            const columnMapping = Object.keys(uploadForm.columnMapping).length > 0 
                ? uploadForm.columnMapping 
                : defaultColumnMapping;
            formData.append('column_mapping', JSON.stringify(columnMapping));

            // Simulate upload progress
            const progressInterval = setInterval(() => {
                setUploadProgress(prev => {
                    if (prev >= 90) {
                        clearInterval(progressInterval);
                        return prev;
                    }
                    return prev + 10;
                });
            }, 200);

            const response = await ApiService.uploadDataset(formData);
            
            clearInterval(progressInterval);
            setUploadProgress(100);

            // Reset form
            setUploadForm({
                name: '',
                description: '',
                tags: '',
                file: null,
                columnMapping: {}
            });

            // Refresh datasets list
            await loadDatasets();
            
            setCurrentView('list');
            toast.success('Dataset uploaded successfully!');

        } catch (error) {
            toast.error(`Upload failed: ${error.message}`);
        } finally {
            setUploading(false);
            setUploadProgress(0);
        }
    };

    const handleDelete = async (dataset) => {
        if (!confirm(`Are you sure you want to delete "${dataset.name}"?`)) {
            return;
        }

        try {
            await ApiService.deleteDataset(dataset.id);
            await loadDatasets();
            toast.success('Dataset deleted successfully');
        } catch (error) {
            toast.error(`Failed to delete dataset: ${error.message}`);
        }
    };

    const handleValidate = async (dataset) => {
        try {
            setLoading(true);
            await ApiService.validateDataset(dataset.id);
            await loadDatasets();
            toast.success('Dataset validation completed');
        } catch (error) {
            toast.error(`Validation failed: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleViewDetails = async (dataset) => {
        try {
            setLoading(true);
            const details = await ApiService.getDataset(dataset.id);
            setSelectedDataset(details);
            setCurrentView('details');
        } catch (error) {
            toast.error(`Failed to load dataset details: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Filter datasets based on search and status
    const filteredDatasets = datasets.filter(dataset => {
        const matchesSearch = dataset.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            dataset.description?.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = filterStatus === 'all' || dataset.status === filterStatus;
        return matchesSearch && matchesStatus;
    });

    const getStatusBadge = (status) => {
        const statusConfig = {
            'processing': { variant: 'secondary', icon: Loader2, text: 'Processing' },
            'completed': { variant: 'default', icon: CheckCircle, text: 'Ready' },
            'failed': { variant: 'destructive', icon: AlertCircle, text: 'Failed' },
            'validating': { variant: 'outline', icon: Clock, text: 'Validating' }
        };
        
        const config = statusConfig[status] || statusConfig['processing'];
        const Icon = config.icon;
        
        return (
            <Badge variant={config.variant} className="flex items-center gap-1">
                <Icon className={`h-3 w-3 ${status === 'processing' || status === 'validating' ? 'animate-spin' : ''}`} />
                {config.text}
            </Badge>
        );
    };

    const formatFileSize = (bytes) => {
        if (!bytes) return 'Unknown';
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
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

    // Render upload form
    if (currentView === 'upload') {
        return (
            <div className="space-y-6">
                <div className="flex items-center gap-4">
                    <Button
                        variant="ghost"
                        onClick={() => setCurrentView('list')}
                        className="flex items-center gap-2"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Back to Datasets
                    </Button>
                    <h2 className="text-2xl font-bold">Upload New Dataset</h2>
                </div>

                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Upload className="h-5 w-5" />
                            Dataset Upload
                        </CardTitle>
                        <CardDescription>
                            Upload epidemiological data for analysis and modeling
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {/* File Upload */}
                        <div className="space-y-2">
                            <Label htmlFor="file">Data File</Label>
                            <Input
                                id="file"
                                type="file"
                                accept=".csv,.json,.xlsx"
                                onChange={handleFileChange}
                                disabled={uploading}
                            />
                            <p className="text-sm text-muted-foreground">
                                Supported formats: CSV, JSON, Excel (.xlsx) - Max size: 100MB
                            </p>
                        </div>

                        {/* Basic Info */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="name">Dataset Name</Label>
                                <Input
                                    id="name"
                                    value={uploadForm.name}
                                    onChange={(e) => setUploadForm(prev => ({ ...prev, name: e.target.value }))}
                                    placeholder="Enter dataset name"
                                    disabled={uploading}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="data_type">Data Type</Label>
                                <select
                                    id="data_type"
                                    value={uploadForm.data_type}
                                    onChange={(e) => setUploadForm(prev => ({ ...prev, data_type: e.target.value }))}
                                    disabled={uploading}
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    <option value="time_series">Time Series</option>
                                    <option value="cross_sectional">Cross-sectional</option>
                                    <option value="spatial">Spatial</option>
                                </select>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="tags">Tags</Label>
                                <Input
                                    id="tags"
                                    value={uploadForm.tags}
                                    onChange={(e) => setUploadForm(prev => ({ ...prev, tags: e.target.value }))}
                                    placeholder="covid-19, surveillance, regional"
                                    disabled={uploading}
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="description">Description</Label>
                            <Textarea
                                id="description"
                                value={uploadForm.description}
                                onChange={(e) => setUploadForm(prev => ({ ...prev, description: e.target.value }))}
                                placeholder="Describe the dataset, its source, and key characteristics"
                                disabled={uploading}
                            />
                        </div>

                        {/* Upload Progress */}
                        {uploading && (
                            <div className="space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span>Uploading...</span>
                                    <span>{uploadProgress}%</span>
                                </div>
                                <Progress value={uploadProgress} className="w-full" />
                            </div>
                        )}

                        {/* Upload Button */}
                        <Button
                            onClick={handleUpload}
                            disabled={!uploadForm.file || !uploadForm.name.trim() || uploading}
                            className="w-full"
                        >
                            {uploading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Uploading...
                                </>
                            ) : (
                                <>
                                    <Upload className="mr-2 h-4 w-4" />
                                    Upload Dataset
                                </>
                            )}
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Render dataset details
    if (currentView === 'details' && selectedDataset) {
        return (
            <div className="space-y-6">
                <div className="flex items-center gap-4">
                    <Button
                        variant="ghost"
                        onClick={() => setCurrentView('list')}
                        className="flex items-center gap-2"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Back to Datasets
                    </Button>
                    <h2 className="text-2xl font-bold">{selectedDataset.name}</h2>
                    {getStatusBadge(selectedDataset.status)}
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Dataset Info */}
                    <Card className="lg:col-span-2">
                        <CardHeader>
                            <CardTitle>Dataset Information</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <Label className="text-sm font-medium">Description</Label>
                                <p className="text-sm text-muted-foreground mt-1">
                                    {selectedDataset.description || 'No description provided'}
                                </p>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <Label className="text-sm font-medium">File Size</Label>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        {formatFileSize(selectedDataset.file_size)}
                                    </p>
                                </div>
                                <div>
                                    <Label className="text-sm font-medium">Records</Label>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        {selectedDataset.total_records?.toLocaleString() || 'Unknown'}
                                    </p>
                                </div>
                                <div>
                                    <Label className="text-sm font-medium">Uploaded</Label>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        {formatDate(selectedDataset.created_at)}
                                    </p>
                                </div>
                                <div>
                                    <Label className="text-sm font-medium">Last Modified</Label>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        {formatDate(selectedDataset.updated_at)}
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
                                onClick={() => handleValidate(selectedDataset)}
                                disabled={loading}
                            >
                                <CheckCircle className="mr-2 h-4 w-4" />
                                Validate Data
                            </Button>
                            <Button
                                variant="outline"
                                className="w-full justify-start"
                            >
                                <Download className="mr-2 h-4 w-4" />
                                Download
                            </Button>
                            <Button
                                variant="destructive"
                                className="w-full justify-start"
                                onClick={() => handleDelete(selectedDataset)}
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

    // Render main datasets list
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h2 className="text-2xl font-bold">Dataset Management</h2>
                    <p className="text-muted-foreground">
                        Upload, manage, and analyze epidemiological datasets
                    </p>
                </div>
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        onClick={refreshDatasets}
                        disabled={refreshing}
                    >
                        <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                    <Button onClick={() => setCurrentView('upload')}>
                        <Plus className="h-4 w-4 mr-2" />
                        Upload Dataset
                    </Button>
                </div>
            </div>

            {/* Filters */}
            <Card>
                <CardContent className="pt-6">
                    <div className="flex flex-col sm:flex-row gap-4">
                        <div className="flex-1">
                            <div className="relative">
                                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="Search datasets..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="pl-10"
                                />
                            </div>
                        </div>
                        <Select value={filterStatus} onValueChange={setFilterStatus}>
                            <SelectTrigger className="w-full sm:w-48">
                                <SelectValue placeholder="Filter by status" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Status</SelectItem>
                                <SelectItem value="processing">Processing</SelectItem>
                                <SelectItem value="completed">Completed</SelectItem>
                                <SelectItem value="failed">Failed</SelectItem>
                                <SelectItem value="validating">Validating</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </CardContent>
            </Card>

            {/* Loading State */}
            {loading && (
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin" />
                    <span className="ml-2">Loading datasets...</span>
                </div>
            )}

            {/* Empty State */}
            {!loading && filteredDatasets.length === 0 && (
                <Card>
                    <CardContent className="pt-6">
                        <div className="text-center py-12">
                            <Database className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">No datasets found</h3>
                            <p className="text-muted-foreground mb-4">
                                {searchTerm || filterStatus !== 'all' 
                                    ? 'No datasets match your current filters'
                                    : 'Get started by uploading your first dataset'
                                }
                            </p>
                            {!searchTerm && filterStatus === 'all' && (
                                <Button onClick={() => setCurrentView('upload')}>
                                    <Plus className="h-4 w-4 mr-2" />
                                    Upload Dataset
                                </Button>
                            )}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Datasets Grid */}
            {!loading && filteredDatasets.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredDatasets.map((dataset) => (
                        <Card key={dataset.id} className="hover:shadow-md transition-shadow">
                            <CardHeader className="pb-3">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1 min-w-0">
                                        <CardTitle className="text-lg truncate">
                                            {dataset.name}
                                        </CardTitle>
                                        <div className="flex items-center gap-2 mt-2">
                                            {getStatusBadge(dataset.status)}
                                            <span className="text-xs text-muted-foreground">
                                                {formatDate(dataset.created_at)}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <p className="text-sm text-muted-foreground line-clamp-2">
                                    {dataset.description || 'No description provided'}
                                </p>
                                
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                    <div>
                                        <span className="font-medium">Size:</span>
                                        <span className="ml-1 text-muted-foreground">
                                            {formatFileSize(dataset.file_size)}
                                        </span>
                                    </div>
                                    <div>
                                        <span className="font-medium">Records:</span>
                                        <span className="ml-1 text-muted-foreground">
                                            {dataset.total_records?.toLocaleString() || 'Unknown'}
                                        </span>
                                    </div>
                                </div>

                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleViewDetails(dataset)}
                                        className="flex-1"
                                    >
                                        <Eye className="h-3 w-3 mr-1" />
                                        View
                                    </Button>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleValidate(dataset)}
                                        disabled={dataset.status === 'processing'}
                                    >
                                        <CheckCircle className="h-3 w-3" />
                                    </Button>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleDelete(dataset)}
                                        className="text-red-600 hover:text-red-700"
                                    >
                                        <Trash2 className="h-3 w-3" />
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
};

export default DatasetManagerAPI;