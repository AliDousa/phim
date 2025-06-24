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
    Activity
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
            examples: ['tests', 'testing', 'test_count', 'total_tests']
        }
    ]
};

const DatasetCard = ({ dataset, onAction }) => {
    const getTypeIcon = (type) => {
        switch (type) {
            case 'time_series': return { icon: TrendingUp, color: 'text-blue-500', bg: 'bg-blue-50' };
            case 'cross_sectional': return { icon: BarChart3, color: 'text-purple-500', bg: 'bg-purple-50' };
            case 'spatial': return { icon: MapPin, color: 'text-emerald-500', bg: 'bg-emerald-50' };
            default: return { icon: FileText, color: 'text-slate-500', bg: 'bg-slate-50' };
        }
    };

    const getFileIcon = (filename) => {
        if (filename.endsWith('.csv')) return { icon: FileSpreadsheet, color: 'text-emerald-600' };
        if (filename.endsWith('.json')) return { icon: File, color: 'text-blue-600' };
        return { icon: FileText, color: 'text-slate-600' };
    };

    const typeConfig = getTypeIcon(dataset.data_type);
    const fileConfig = getFileIcon(dataset.source);
    const TypeIcon = typeConfig.icon;
    const FileIcon = fileConfig.icon;

    return (
        <Card className="group relative overflow-hidden border-0 shadow-xl hover:shadow-2xl transition-all duration-500 hover:-translate-y-1 bg-white/90 backdrop-blur-sm">
            {/* Status Indicator */}
            <div className={`absolute top-0 left-0 right-0 h-1 ${dataset.is_validated ? 'bg-emerald-500' : 'bg-orange-500'
                }`} />

            {/* Background Pattern */}
            <div className="absolute top-0 right-0 w-32 h-32 opacity-5 overflow-hidden">
                <TypeIcon className="w-full h-full transform rotate-12 scale-150" />
            </div>

            <CardHeader className="relative">
                <div className="flex items-start justify-between">
                    <div className="space-y-2 flex-1">
                        <div className="flex items-center gap-3">
                            <CardTitle className="text-lg font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                                {dataset.name}
                            </CardTitle>
                            {dataset.is_validated ? (
                                <CheckCircle className="w-5 h-5 text-emerald-500" />
                            ) : (
                                <AlertCircle className="w-5 h-5 text-orange-500" />
                            )}
                        </div>
                        <CardDescription className="text-slate-600">{dataset.description}</CardDescription>
                    </div>
                    <div className={`p-2 rounded-xl ${typeConfig.bg} ${typeConfig.color} shadow-lg`}>
                        <TypeIcon className="w-5 h-5" />
                    </div>
                </div>
            </CardHeader>

            <CardContent className="relative space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-3">
                        <div className="flex items-center gap-2 text-sm">
                            <FileIcon className={`w-4 h-4 ${fileConfig.color}`} />
                            <span className="text-slate-600 truncate font-medium">{dataset.source}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                            <Database className="w-4 h-4 text-slate-400" />
                            <span className="text-slate-600 font-medium">{dataset.record_count?.toLocaleString() || 0} records</span>
                        </div>
                    </div>
                    <div className="space-y-3">
                        <div className="flex items-center gap-2 text-sm">
                            <Calendar className="w-4 h-4 text-slate-400" />
                            <span className="text-slate-600">{new Date(dataset.upload_date).toLocaleDateString()}</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                            <Users className="w-4 h-4 text-slate-400" />
                            <span className="text-slate-600">User {dataset.user_id}</span>
                        </div>
                    </div>
                </div>

                {/* Validation Status */}
                <div className={`p-3 rounded-lg border ${dataset.is_validated
                    ? 'bg-emerald-50 border-emerald-200'
                    : 'bg-orange-50 border-orange-200'
                    }`}>
                    <div className="flex items-center gap-2">
                        {dataset.is_validated ? (
                            <>
                                <CheckCircle className="w-4 h-4 text-emerald-600" />
                                <span className="text-sm font-medium text-emerald-800">Validated & Ready</span>
                            </>
                        ) : (
                            <>
                                <AlertCircle className="w-4 h-4 text-orange-600" />
                                <span className="text-sm font-medium text-orange-800">Validation Issues</span>
                            </>
                        )}
                    </div>
                    {dataset.validation_errors && (
                        <p className="text-sm text-orange-700 mt-1">{dataset.validation_errors}</p>
                    )}
                </div>

                {/* Data Type Badge */}
                <div className="flex items-center justify-between">
                    <Badge className={`${typeConfig.bg} ${typeConfig.color} border-0 px-3 py-1 font-medium`}>
                        <TypeIcon className="w-3 h-3 mr-1" />
                        {dataset.data_type.replace('_', ' ')}
                    </Badge>

                    <div className="flex items-center gap-2">
                        <Button size="sm" variant="outline" onClick={() => onAction('view', dataset.id)}
                            className="shadow-md hover:shadow-lg transition-all">
                            <Eye className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => onAction('download', dataset.id)}
                            className="shadow-md hover:shadow-lg transition-all">
                            <Download className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => onAction('delete', dataset.id)}
                            className="text-red-500 hover:text-red-700 hover:bg-red-50">
                            <Trash2 className="w-4 h-4" />
                        </Button>
                    </div>
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

    const handleFileChange = useCallback(async (file) => {
        if (file) {
            setUploadData(prev => ({ ...prev, file }));
            setIsProcessing(true);

            try {
                // Simulate processing delay
                await new Promise(resolve => setTimeout(resolve, 2000));

                // Mock headers based on file type
                const mockHeaders = file.name.endsWith('.csv')
                    ? ['date', 'location', 'new_cases', 'new_deaths', 'population', 'tests']
                    : ['timestamp', 'region', 'cases', 'deaths', 'recovered'];

                setUploadData(prev => ({ ...prev, headers: mockHeaders }));
                setStep(2);
                toast.success('File processed successfully!');
            } catch (error) {
                toast.error('Error processing file');
            } finally {
                setIsProcessing(false);
            }
        }
    }, []);

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

            await new Promise(resolve => setTimeout(resolve, 3000));

            clearInterval(progressInterval);
            setUploadProgress(100);

            const newDataset = {
                id: Date.now(),
                name: uploadData.name,
                description: uploadData.description,
                data_type: uploadData.data_type,
                source: uploadData.file.name,
                upload_date: new Date().toISOString(),
                is_validated: true,
                record_count: Math.floor(Math.random() * 50000) + 10000,
                user_id: 1,
                validation_errors: null
            };

            setTimeout(() => {
                onComplete(newDataset);
                toast.success('Dataset uploaded successfully!');
            }, 500);
        } catch (error) {
            toast.error('Upload failed');
            setStep(2);
        }
    };

    const renderStepContent = () => {
        switch (step) {
            case 1:
                return (
                    <div className="space-y-8">
                        <div className="text-center">
                            <h3 className="text-3xl font-bold text-slate-900 mb-3">Upload Dataset</h3>
                            <p className="text-lg text-slate-600">Upload your epidemiological data file (CSV or JSON)</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <Label className="font-medium">Dataset Name</Label>
                                <Input
                                    value={uploadData.name}
                                    onChange={(e) => setUploadData(prev => ({ ...prev, name: e.target.value }))}
                                    placeholder="e.g., COVID-19 Regional Data 2024"
                                    className="bg-white shadow-sm"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label className="font-medium">Data Type</Label>
                                <Select value={uploadData.data_type} onValueChange={(value) => setUploadData(prev => ({ ...prev, data_type: value }))}>
                                    <SelectTrigger className="bg-white shadow-sm">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="time_series">
                                            <div className="flex items-center gap-2">
                                                <TrendingUp className="w-4 h-4" />
                                                Time Series
                                            </div>
                                        </SelectItem>
                                        <SelectItem value="cross_sectional">
                                            <div className="flex items-center gap-2">
                                                <BarChart3 className="w-4 h-4" />
                                                Cross-sectional
                                            </div>
                                        </SelectItem>
                                        <SelectItem value="spatial">
                                            <div className="flex items-center gap-2">
                                                <MapPin className="w-4 h-4" />
                                                Spatial
                                            </div>
                                        </SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label className="font-medium">Description</Label>
                            <Textarea
                                value={uploadData.description}
                                onChange={(e) => setUploadData(prev => ({ ...prev, description: e.target.value }))}
                                placeholder="Describe your dataset, its source, and intended use..."
                                rows={3}
                                className="bg-white shadow-sm"
                            />
                        </div>

                        <Card
                            className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 cursor-pointer ${dragActive ? 'border-blue-500 bg-blue-50 shadow-xl' : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50'
                                }`}
                            onDragEnter={() => setDragActive(true)}
                            onDragLeave={() => setDragActive(false)}
                            onDragOver={(e) => e.preventDefault()}
                            onDrop={handleDrop}
                        >
                            {isProcessing ? (
                                <div className="flex flex-col items-center">
                                    <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mb-6 animate-pulse">
                                        <Brain className="w-8 h-8 text-white" />
                                    </div>
                                    <h4 className="text-xl font-semibold mb-3 text-slate-900">Processing File...</h4>
                                    <p className="text-slate-600 mb-4">Analyzing structure and validating data format</p>
                                    <div className="w-full max-w-xs">
                                        <Progress value={75} className="h-2" />
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform">
                                        <Cloud className="w-10 h-10 text-white" />
                                    </div>
                                    <h4 className="text-2xl font-semibold mb-3 text-slate-900">Drop your file here</h4>
                                    <p className="text-slate-600 mb-6">or click to browse your files</p>
                                    <Input
                                        type="file"
                                        accept=".csv,.json"
                                        onChange={(e) => handleFileChange(e.target.files[0])}
                                        className="max-w-xs mx-auto bg-white shadow-lg"
                                    />
                                    <div className="flex items-center justify-center gap-6 mt-6 text-sm text-slate-500">
                                        <div className="flex items-center gap-2">
                                            <FileSpreadsheet className="w-4 h-4 text-emerald-500" />
                                            <span>CSV</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <File className="w-4 h-4 text-blue-500" />
                                            <span>JSON</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Shield className="w-4 h-4 text-purple-500" />
                                            <span>Up to 100MB</span>
                                        </div>
                                    </div>
                                </>
                            )}
                        </Card>
                    </div>
                );

            case 2:
                const requiredMapped = columnMappingOptions.required.every(field => uploadData.columnMapping[field.id]);

                return (
                    <div className="space-y-8">
                        <div className="text-center">
                            <h3 className="text-3xl font-bold text-slate-900 mb-3">Map Your Columns</h3>
                            <p className="text-lg text-slate-600">Match your data columns to our standardized format</p>
                        </div>

                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                            <Card className="border-0 shadow-xl bg-white/90 backdrop-blur-sm">
                                <CardHeader className="bg-gradient-to-r from-red-50 to-orange-50 border-b border-slate-200/60">
                                    <CardTitle className="flex items-center gap-3 text-lg">
                                        <div className="p-2 bg-gradient-to-br from-red-500 to-orange-600 rounded-lg">
                                            <Target className="h-5 w-5 text-white" />
                                        </div>
                                        Required Fields
                                    </CardTitle>
                                    <CardDescription>These fields are essential for analysis</CardDescription>
                                </CardHeader>
                                <CardContent className="p-6 space-y-6">
                                    {columnMappingOptions.required.map(field => {
                                        const IconComponent = field.icon;
                                        return (
                                            <div key={field.id} className="space-y-3">
                                                <div className="flex items-center gap-3">
                                                    <IconComponent className="w-5 h-5 text-blue-500" />
                                                    <Label className="font-medium">{field.label}</Label>
                                                </div>
                                                <Select
                                                    value={uploadData.columnMapping[field.id] || ''}
                                                    onValueChange={(value) => setUploadData(prev => ({
                                                        ...prev,
                                                        columnMapping: { ...prev.columnMapping, [field.id]: value }
                                                    }))}
                                                >
                                                    <SelectTrigger className="bg-white shadow-sm">
                                                        <SelectValue placeholder="Select column" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        {uploadData.headers.map(header => (
                                                            <SelectItem key={header} value={header}>{header}</SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                                <p className="text-xs text-slate-500">{field.description}</p>
                                                <div className="flex flex-wrap gap-1">
                                                    {field.examples.map(example => (
                                                        <Badge key={example} variant="outline" className="text-xs">
                                                            {example}
                                                        </Badge>
                                                    ))}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </CardContent>
                            </Card>

                            <Card className="border-0 shadow-xl bg-white/90 backdrop-blur-sm">
                                <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 border-b border-slate-200/60">
                                    <CardTitle className="flex items-center gap-3 text-lg">
                                        <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
                                            <Sparkles className="h-5 w-5 text-white" />
                                        </div>
                                        Optional Fields
                                    </CardTitle>
                                    <CardDescription>Additional data for enhanced analysis</CardDescription>
                                </CardHeader>
                                <CardContent className="p-6 space-y-6">
                                    {columnMappingOptions.optional.map(field => {
                                        const IconComponent = field.icon;
                                        return (
                                            <div key={field.id} className="space-y-3">
                                                <div className="flex items-center gap-3">
                                                    <IconComponent className="w-5 h-5 text-emerald-500" />
                                                    <Label className="font-medium">{field.label}</Label>
                                                </div>
                                                <Select
                                                    value={uploadData.columnMapping[field.id] || ''}
                                                    onValueChange={(value) => setUploadData(prev => ({
                                                        ...prev,
                                                        columnMapping: { ...prev.columnMapping, [field.id]: value || undefined }
                                                    }))}
                                                >
                                                    <SelectTrigger className="bg-white shadow-sm">
                                                        <SelectValue placeholder="Select column (optional)" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="">None</SelectItem>
                                                        {uploadData.headers.map(header => (
                                                            <SelectItem key={header} value={header}>{header}</SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                                <p className="text-xs text-slate-500">{field.description}</p>
                                                <div className="flex flex-wrap gap-1">
                                                    {field.examples.map(example => (
                                                        <Badge key={example} variant="outline" className="text-xs">
                                                            {example}
                                                        </Badge>
                                                    ))}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </CardContent>
                            </Card>
                        </div>

                        <div className="flex justify-center">
                            <Button
                                onClick={handleSubmit}
                                disabled={!requiredMapped}
                                className="bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white border-0 shadow-xl hover:shadow-2xl px-8 py-6 text-lg font-semibold"
                            >
                                <Zap className="w-5 h-5 mr-3" />
                                Process Dataset
                                <Sparkles className="w-4 w-4 ml-2" />
                            </Button>
                        </div>
                    </div>
                );

            case 3:
                return (
                    <div className="space-y-8">
                        <div className="text-center">
                            <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6 animate-pulse">
                                <Brain className="w-12 h-12 text-white" />
                            </div>
                            <h3 className="text-3xl font-bold text-slate-900 mb-3">Processing Upload</h3>
                            <p className="text-lg text-slate-600">Validating and importing your dataset with AI-powered analysis...</p>
                        </div>

                        <div className="max-w-md mx-auto space-y-4">
                            <div className="flex justify-between text-sm font-medium">
                                <span>Upload Progress</span>
                                <span>{Math.round(uploadProgress)}%</span>
                            </div>
                            <Progress value={uploadProgress} className="h-3" />

                            <div className="flex items-center justify-center gap-2 text-sm text-slate-600">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                <span>Analyzing data patterns and quality...</span>
                            </div>
                        </div>
                    </div>
                );

            default:
                return null;
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20 p-8">
            <div className="max-w-6xl mx-auto space-y-8">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <Button
                        variant="outline"
                        onClick={onCancel}
                        className="shadow-lg"
                    >
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back to Datasets
                    </Button>

                    <div className="flex items-center gap-4">
                        {[1, 2, 3].map((stepNum) => (
                            <div key={stepNum} className="flex items-center gap-2">
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${step >= stepNum
                                    ? 'bg-blue-500 text-white shadow-lg'
                                    : 'bg-slate-200 text-slate-500'
                                    }`}>
                                    {stepNum}
                                </div>
                                {stepNum < 3 && (
                                    <div className={`w-16 h-1 rounded-full ${step > stepNum ? 'bg-blue-500' : 'bg-slate-200'}`} />
                                )}
                            </div>
                        ))}
                    </div>

                    <div className="w-32" /> {/* Spacer */}
                </div>

                {/* Step Content */}
                <div className="animate-fade-in">
                    {renderStepContent()}
                </div>
            </div>
        </div>
    );
};

export default function DatasetManager() {
    const [datasets, setDatasets] = useState([
        {
            id: 1,
            name: "COVID-19 Global Dataset",
            description: "Comprehensive global COVID-19 data with daily updates",
            data_type: "time_series",
            source: "covid_data_2024.csv",
            upload_date: "2024-06-15T10:00:00Z",
            is_validated: true,
            record_count: 45230,
            user_id: 1,
            validation_errors: null
        },
        {
            id: 2,
            name: "Influenza Surveillance",
            description: "Weekly influenza surveillance data from multiple regions",
            data_type: "cross_sectional",
            source: "flu_surveillance.json",
            upload_date: "2024-06-18T14:30:00Z",
            is_validated: false,
            record_count: 12450,
            user_id: 1,
            validation_errors: "Missing population data for 3 regions"
        },
        {
            id: 3,
            name: "Hospital Capacity Data",
            description: "Real-time hospital capacity and utilization metrics",
            data_type: "spatial",
            source: "hospital_data.csv",
            upload_date: "2024-06-20T09:15:00Z",
            is_validated: true,
            record_count: 8760,
            user_id: 1,
            validation_errors: null
        }
    ]);

    const [showUploadWizard, setShowUploadWizard] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterType, setFilterType] = useState('all');
    const [isLoading, setIsLoading] = useState(false);

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
                    setDatasets(prev => prev.filter(d => d.id !== datasetId));
                    toast.success('Dataset deleted successfully');
                }
                break;
            case 'view':
                toast.info('Dataset viewer will open soon');
                break;
            case 'download':
                toast.info('Download started');
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
            <UploadWizard
                onComplete={handleUploadComplete}
                onCancel={() => setShowUploadWizard(false)}
            />
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20">
            <Toaster richColors position="top-right" />

            <div className="p-8 space-y-8">
                {/* Header */}
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                    <div className="space-y-3">
                        <h1 className="text-5xl font-bold bg-gradient-to-r from-slate-900 via-blue-900 to-purple-900 bg-clip-text text-transparent leading-tight">
                            Dataset Manager
                        </h1>
                        <p className="text-xl text-slate-600 max-w-3xl">
                            Manage and analyze your epidemiological datasets with AI-powered validation
                        </p>
                    </div>
                    <Button
                        onClick={() => setShowUploadWizard(true)}
                        className="bg-gradient-to-r from-blue-500 via-blue-600 to-purple-600 hover:from-blue-600 hover:via-blue-700 hover:to-purple-700 text-white border-0 shadow-xl hover:shadow-2xl transition-all px-8 py-6 text-lg font-semibold"
                    >
                        <Plus className="w-5 h-5 mr-3" />
                        Upload Dataset
                        <Sparkles className="w-4 w-4 ml-2" />
                    </Button>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                    {[
                        { title: "Total Datasets", value: stats.total, icon: Database, color: "blue" },
                        { title: "Validated", value: stats.validated, icon: CheckCircle, color: "emerald" },
                        { title: "Total Records", value: `${Math.round(stats.totalRecords / 1000)}K`, icon: BarChart3, color: "purple" },
                        { title: "Recent Uploads", value: stats.recentUploads, icon: Upload, color: "orange" }
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

                {/* Search and Filter */}
                <div className="flex flex-col md:flex-row gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
                        <Input
                            placeholder="Search datasets by name or description..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="pl-12 bg-white shadow-lg border-0 h-12 text-lg"
                        />
                    </div>
                    <Select value={filterType} onValueChange={setFilterType}>
                        <SelectTrigger className="w-full md:w-64 bg-white shadow-lg border-0 h-12">
                            <Filter className="w-5 h-5 mr-2" />
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="all">All Types</SelectItem>
                            <SelectItem value="time_series">
                                <div className="flex items-center gap-2">
                                    <TrendingUp className="w-4 h-4" />
                                    Time Series
                                </div>
                            </SelectItem>
                            <SelectItem value="cross_sectional">
                                <div className="flex items-center gap-2">
                                    <BarChart3 className="w-4 h-4" />
                                    Cross-sectional
                                </div>
                            </SelectItem>
                            <SelectItem value="spatial">
                                <div className="flex items-center gap-2">
                                    <MapPin className="w-4 h-4" />
                                    Spatial
                                </div>
                            </SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                {/* Datasets Grid */}
                {filteredDatasets.length === 0 ? (
                    <Card className="border-0 shadow-xl bg-white/90 backdrop-blur-sm">
                        <CardContent className="flex flex-col items-center justify-center py-16">
                            <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mb-6">
                                <Database className="h-12 w-12 text-white" />
                            </div>
                            <h3 className="text-2xl font-bold text-slate-900 mb-2">
                                {searchTerm || filterType !== 'all' ? 'No datasets found' : 'No datasets yet'}
                            </h3>
                            <p className="text-slate-600 text-center mb-6 max-w-md">
                                {searchTerm || filterType !== 'all'
                                    ? 'Try adjusting your search or filter criteria'
                                    : 'Upload your first dataset to get started with epidemiological analysis'
                                }
                            </p>
                            {!searchTerm && filterType === 'all' && (
                                <Button
                                    onClick={() => setShowUploadWizard(true)}
                                    className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white border-0 shadow-xl hover:shadow-2xl"
                                >
                                    <Plus className="w-5 h-5 mr-2" />
                                    Upload First Dataset
                                </Button>
                            )}
                        </CardContent>
                    </Card>
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
            </div>
        </div>
    );
}