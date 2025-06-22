import React, { useState, useCallback, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Toaster, toast } from 'sonner';
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
    Loader2
} from 'lucide-react';

// Column mapping configuration
const columnMappingOptions = {
    required: [
        { id: 'timestamp_col', label: 'Date/Time Column', description: 'The temporal dimension of your data' },
        { id: 'location_col', label: 'Location Column', description: 'Geographic identifier (region, state, county, etc.)' },
        { id: 'new_cases_col', label: 'New Cases Column', description: 'Number of new cases reported' },
        { id: 'new_deaths_col', label: 'New Deaths Column', description: 'Number of new deaths reported' }
    ],
    optional: [
        { id: 'population_col', label: 'Population Column', description: 'Population size for the location' },
        { id: 'hospitalizations_col', label: 'Hospitalizations', description: 'Number of hospitalizations' },
        { id: 'recoveries_col', label: 'Recoveries', description: 'Number of recoveries' },
        { id: 'tests_col', label: 'Tests Conducted', description: 'Number of tests performed' }
    ]
};

const DatasetCard = ({ dataset, onAction }) => {
    const getTypeIcon = (type) => {
        switch (type) {
            case 'time_series': return <TrendingUp className="w-4 h-4" />;
            case 'cross_sectional': return <BarChart3 className="w-4 h-4" />;
            case 'spatial': return <MapPin className="w-4 h-4" />;
            default: return <FileText className="w-4 h-4" />;
        }
    };

    const getFileIcon = (filename) => {
        if (filename.endsWith('.csv')) return <FileSpreadsheet className="w-4 h-4 text-green-600" />;
        if (filename.endsWith('.json')) return <File className="w-4 h-4 text-blue-600" />;
        return <FileText className="w-4 h-4 text-gray-600" />;
    };

    return (
        <Card className="hover:shadow-lg transition-shadow duration-200">
            <CardHeader>
                <div className="flex items-start justify-between">
                    <div className="space-y-1 flex-1">
                        <div className="flex items-center gap-2">
                            <CardTitle className="text-lg">{dataset.name}</CardTitle>
                            {dataset.is_validated ? (
                                <CheckCircle className="w-4 h-4 text-green-500" />
                            ) : (
                                <AlertCircle className="w-4 h-4 text-orange-500" />
                            )}
                        </div>
                        <CardDescription>{dataset.description}</CardDescription>
                    </div>
                    <Badge variant="outline" className="flex items-center gap-1">
                        {getTypeIcon(dataset.data_type)}
                        {dataset.data_type.replace('_', ' ')}
                    </Badge>
                </div>
            </CardHeader>

            <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="flex items-center gap-2">
                        {getFileIcon(dataset.source)}
                        <span className="text-gray-600 truncate">{dataset.source}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Database className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-600">{dataset.record_count?.toLocaleString() || 0} records</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-600">{new Date(dataset.upload_date).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Users className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-600">User {dataset.user_id}</span>
                    </div>
                </div>

                {dataset.validation_errors && (
                    <div className="p-3 bg-orange-50 border border-orange-200 rounded-md">
                        <div className="flex items-center gap-2 text-orange-800">
                            <AlertCircle className="w-4 h-4" />
                            <span className="text-sm font-medium">Validation Issues</span>
                        </div>
                        <p className="text-sm text-orange-700 mt-1">{dataset.validation_errors}</p>
                    </div>
                )}

                <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" onClick={() => onAction('view', dataset.id)}>
                        <Eye className="w-4 h-4" />
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => onAction('download', dataset.id)}>
                        <Download className="w-4 h-4" />
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => onAction('delete', dataset.id)}>
                        <Trash2 className="w-4 h-4 text-red-500" />
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
};

const UploadWizard = ({ onComplete, onCancel }) => {
    const [step, setStep] = useState(1);
    const [uploadData, setUploadData] = useState({
        name: '',
        description: '',
        data_type: 'time_series',
        file: null,
        headers: [],
        columnMapping: {}
    });
    const [dragActive, setDragActive] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [isProcessing, setIsProcessing] = useState(false);

    const authToken = localStorage.getItem('authToken');

    const handleFileChange = useCallback(async (file) => {
        if (file) {
            setUploadData(prev => ({ ...prev, file }));
            setIsProcessing(true);

            try {
                // Get file headers
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch('/api/datasets/get-headers', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${authToken}` },
                    body: formData,
                });

                if (response.ok) {
                    const result = await response.json();
                    setUploadData(prev => ({ ...prev, headers: result.headers }));
                    setStep(2);
                    toast.success('File headers detected successfully!');
                } else {
                    const error = await response.json();
                    toast.error(`Error reading file: ${error.error}`);
                }
            } catch (error) {
                toast.error('Could not read file headers');
                console.error(error);
            } finally {
                setIsProcessing(false);
            }
        }
    }, [authToken]);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setDragActive(false);
        const file = e.dataTransfer.files[0];
        if (file && (file.type === 'text/csv' || file.type === 'application/json' || file.name.endsWith('.csv') || file.name.endsWith('.json'))) {
            handleFileChange(file);
        } else {
            toast.error('Please upload a CSV or JSON file');
        }
    }, [handleFileChange]);

    const handleSubmit = async () => {
        setStep(3);
        setUploadProgress(0);

        try {
            const formData = new FormData();
            formData.append('file', uploadData.file);
            formData.append('name', uploadData.name);
            formData.append('description', uploadData.description);
            formData.append('data_type', uploadData.data_type);
            formData.append('column_mapping', JSON.stringify(uploadData.columnMapping));

            // Simulate upload progress
            const progressInterval = setInterval(() => {
                setUploadProgress(prev => {
                    if (prev >= 90) {
                        clearInterval(progressInterval);
                        return 90;
                    }
                    return prev + Math.random() * 10;
                });
            }, 200);

            const response = await fetch('/api/datasets', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${authToken}` },
                body: formData,
            });

            clearInterval(progressInterval);
            setUploadProgress(100);

            if (response.ok) {
                const result = await response.json();
                setTimeout(() => {
                    onComplete(result.dataset);
                    toast.success('Dataset uploaded successfully!');
                }, 500);
            } else {
                const error = await response.json();
                toast.error(`Upload failed: ${error.error}`);
                setStep(2); // Go back to column mapping
            }
        } catch (error) {
            toast.error('An unexpected error occurred during upload');
            setStep(2);
        }
    };

    if (step === 1) {
        return (
            <div className="space-y-6">
                <div>
                    <h3 className="text-lg font-semibold mb-2">Upload Dataset</h3>
                    <p className="text-gray-600">Upload your epidemiological data file (CSV or JSON)</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Label>Dataset Name</Label>
                        <Input
                            value={uploadData.name}
                            onChange={(e) => setUploadData(prev => ({ ...prev, name: e.target.value }))}
                            placeholder="e.g., COVID-19 Regional Data"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label>Data Type</Label>
                        <Select value={uploadData.data_type} onValueChange={(value) => setUploadData(prev => ({ ...prev, data_type: value }))}>
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="time_series">Time Series</SelectItem>
                                <SelectItem value="cross_sectional">Cross-sectional</SelectItem>
                                <SelectItem value="spatial">Spatial</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                <div className="space-y-2">
                    <Label>Description</Label>
                    <Textarea
                        value={uploadData.description}
                        onChange={(e) => setUploadData(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="Describe your dataset..."
                        rows={3}
                    />
                </div>

                <div
                    className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                        }`}
                    onDragEnter={() => setDragActive(true)}
                    onDragLeave={() => setDragActive(false)}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={handleDrop}
                >
                    {isProcessing ? (
                        <div className="flex flex-col items-center">
                            <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
                            <h4 className="text-lg font-medium mb-2">Processing File...</h4>
                            <p className="text-gray-600">Reading file structure and detecting columns</p>
                        </div>
                    ) : (
                        <>
                            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                            <h4 className="text-lg font-medium mb-2">Drop your file here</h4>
                            <p className="text-gray-600 mb-4">or click to browse</p>
                            <Input
                                type="file"
                                accept=".csv,.json"
                                onChange={(e) => handleFileChange(e.target.files[0])}
                                className="max-w-xs mx-auto"
                            />
                            <p className="text-sm text-gray-500 mt-2">Supports CSV and JSON files up to 100MB</p>
                        </>
                    )}
                </div>

                <div className="flex justify-end gap-3">
                    <Button variant="outline" onClick={onCancel}>Cancel</Button>
                </div>
            </div>
        );
    }

    if (step === 2) {
        const requiredMapped = columnMappingOptions.required.every(field => uploadData.columnMapping[field.id]);

        return (
            <div className="space-y-6">
                <div>
                    <h3 className="text-lg font-semibold mb-2">Map Your Columns</h3>
                    <p className="text-gray-600">Match your data columns to our standard format</p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-base">Required Fields</CardTitle>
                            <CardDescription>These fields are required for analysis</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {columnMappingOptions.required.map(field => (
                                <div key={field.id} className="space-y-2">
                                    <Label>{field.label}</Label>
                                    <Select
                                        value={uploadData.columnMapping[field.id] || ''}
                                        onValueChange={(value) => setUploadData(prev => ({
                                            ...prev,
                                            columnMapping: { ...prev.columnMapping, [field.id]: value }
                                        }))}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select column" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {uploadData.headers.map(header => (
                                                <SelectItem key={header} value={header}>{header}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    <p className="text-xs text-gray-500">{field.description}</p>
                                </div>
                            ))}
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle className="text-base">Optional Fields</CardTitle>
                            <CardDescription>Additional data for enhanced analysis</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {columnMappingOptions.optional.map(field => (
                                <div key={field.id} className="space-y-2">
                                    <Label>{field.label}</Label>
                                    <Select
                                        value={uploadData.columnMapping[field.id] || ''}
                                        onValueChange={(value) => setUploadData(prev => ({
                                            ...prev,
                                            columnMapping: { ...prev.columnMapping, [field.id]: value || undefined }
                                        }))}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select column (optional)" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="">None</SelectItem>
                                            {uploadData.headers.map(header => (
                                                <SelectItem key={header} value={header}>{header}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    <p className="text-xs text-gray-500">{field.description}</p>
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                </div>

                <div className="flex justify-between">
                    <Button variant="outline" onClick={() => setStep(1)}>Back</Button>
                    <Button
                        onClick={handleSubmit}
                        disabled={!requiredMapped}
                        className="bg-gradient-to-r from-blue-500 to-purple-600"
                    >
                        Upload Dataset
                    </Button>
                </div>
            </div>
        );
    }

    if (step === 3) {
        return (
            <div className="space-y-6">
                <div className="text-center">
                    <h3 className="text-lg font-semibold mb-2">Processing Upload</h3>
                    <p className="text-gray-600">Validating and importing your dataset...</p>
                </div>

                <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                        <span>Upload Progress</span>
                        <span>{Math.round(uploadProgress)}%</span>
                    </div>
                    <Progress value={uploadProgress} className="h-2" />
                </div>

                <div className="flex items-center justify-center py-8">
                    <div className="text-center">
                        <Loader2 className="w-16 h-16 text-blue-500 animate-spin mx-auto mb-4" />
                        <p className="text-gray-600">Processing your data...</p>
                    </div>
                </div>
            </div>
        );
    }
};

export default function DatasetManager() {
    const [datasets, setDatasets] = useState([]);
    const [showUploadWizard, setShowUploadWizard] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterType, setFilterType] = useState('all');
    const [isLoading, setIsLoading] = useState(true);

    const authToken = localStorage.getItem('authToken');

    const fetchDatasets = useCallback(async () => {
        setIsLoading(true);
        try {
            const response = await fetch('/api/datasets', {
                headers: { 'Authorization': `Bearer ${authToken}` }
            });
            const data = await response.json();
            if (response.ok) {
                setDatasets(data.datasets || []);
            } else {
                toast.error('Failed to fetch datasets');
            }
        } catch (error) {
            toast.error('Error fetching datasets');
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    }, [authToken]);

    useEffect(() => {
        fetchDatasets();
    }, [fetchDatasets]);

    const filteredDatasets = datasets.filter(dataset => {
        const matchesSearch = dataset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            dataset.description?.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesType = filterType === 'all' || dataset.data_type === filterType;
        return matchesSearch && matchesType;
    });

    const handleDatasetAction = async (action, datasetId) => {
        switch (action) {
            case 'delete':
                if (window.confirm('Are you sure you want to delete this dataset?')) {
                    try {
                        const response = await fetch(`/api/datasets/${datasetId}`, {
                            method: 'DELETE',
                            headers: { 'Authorization': `Bearer ${authToken}` }
                        });
                        if (response.ok) {
                            setDatasets(prev => prev.filter(d => d.id !== datasetId));
                            toast.success('Dataset deleted successfully');
                        } else {
                            toast.error('Failed to delete dataset');
                        }
                    } catch (error) {
                        toast.error('Error deleting dataset');
                    }
                }
                break;
            case 'view':
                toast.info('Dataset viewer not implemented yet');
                break;
            case 'download':
                toast.info('Dataset download not implemented yet');
                break;
        }
    };

    const handleUploadComplete = (newDataset) => {
        setDatasets(prev => [newDataset, ...prev]);
        setShowUploadWizard(false);
    };

    const stats = {
        total: datasets.length,
        validated: datasets.filter(d => d.is_validated).length,
        totalRecords: datasets.reduce((sum, d) => sum + (d.record_count || 0), 0),
        recentUploads: datasets.filter(d => {
            const uploadDate = new Date(d.upload_date);
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            return uploadDate > weekAgo;
        }).length
    };

    if (showUploadWizard) {
        return (
            <div className="space-y-6">
                <Toaster richColors />
                <UploadWizard
                    onComplete={handleUploadComplete}
                    onCancel={() => setShowUploadWizard(false)}
                />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <Toaster richColors />
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Dataset Manager</h1>
                    <p className="text-gray-600">Manage your epidemiological datasets</p>
                </div>
                <Button onClick={() => setShowUploadWizard(true)} className="bg-gradient-to-r from-blue-500 to-purple-600">
                    <Plus className="w-4 h-4 mr-2" />
                    Upload Dataset
                </Button>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                    <CardContent className="flex items-center justify-between p-4">
                        <div>
                            <p className="text-sm text-gray-600">Total Datasets</p>
                            <p className="text-2xl font-bold">{stats.total}</p>
                        </div>
                        <Database className="h-8 w-8 text-gray-400" />
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="flex items-center justify-between p-4">
                        <div>
                            <p className="text-sm text-gray-600">Validated</p>
                            <p className="text-2xl font-bold text-green-600">{stats.validated}</p>
                        </div>
                        <CheckCircle className="h-8 w-8 text-green-400" />
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="flex items-center justify-between p-4">
                        <div>
                            <p className="text-sm text-gray-600">Total Records</p>
                            <p className="text-2xl font-bold">{stats.totalRecords.toLocaleString()}</p>
                        </div>
                        <BarChart3 className="h-8 w-8 text-gray-400" />
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="flex items-center justify-between p-4">
                        <div>
                            <p className="text-sm text-gray-600">Recent Uploads</p>
                            <p className="text-2xl font-bold">{stats.recentUploads}</p>
                        </div>
                        <Upload className="h-8 w-8 text-gray-400" />
                    </CardContent>
                </Card>
            </div>

            {/* Search and Filter */}
            <div className="flex flex-col md:flex-row gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                        placeholder="Search datasets..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10"
                    />
                </div>
                <Select value={filterType} onValueChange={setFilterType}>
                    <SelectTrigger className="w-full md:w-48">
                        <Filter className="w-4 h-4 mr-2" />
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Types</SelectItem>
                        <SelectItem value="time_series">Time Series</SelectItem>
                        <SelectItem value="cross_sectional">Cross-sectional</SelectItem>
                        <SelectItem value="spatial">Spatial</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            {/* Datasets Grid */}
            {isLoading ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                    {[...Array(6)].map((_, i) => (
                        <Card key={i} className="animate-pulse">
                            <CardHeader>
                                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-2">
                                    <div className="h-3 bg-gray-200 rounded"></div>
                                    <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                    {filteredDatasets.map(dataset => (
                        <DatasetCard
                            key={dataset.id}
                            dataset={dataset}
                            onAction={handleDatasetAction}
                        />
                    ))}
                </div>
            )}

            {filteredDatasets.length === 0 && !isLoading && (
                <Card>
                    <CardContent className="flex flex-col items-center justify-center py-12">
                        <Database className="h-12 w-12 text-gray-400 mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">
                            {searchTerm || filterType !== 'all' ? 'No datasets found' : 'No datasets yet'}
                        </h3>
                        <p className="text-gray-600 text-center mb-4">
                            {searchTerm || filterType !== 'all'
                                ? 'Try adjusting your search or filter criteria'
                                : 'Upload your first dataset to get started with epidemiological analysis'
                            }
                        </p>
                        {!searchTerm && filterType === 'all' && (
                            <Button onClick={() => setShowUploadWizard(true)} className="bg-gradient-to-r from-blue-500 to-purple-600">
                                <Plus className="w-4 h-4 mr-2" />
                                Upload First Dataset
                            </Button>
                        )}
                    </CardContent>
                </Card>
            )}
        </div>
    );
}