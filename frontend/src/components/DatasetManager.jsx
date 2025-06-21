import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Toaster, toast } from 'sonner';
import { UploadCloud, Check, X, Loader2 } from 'lucide-react';

const REQUIRED_MAPPINGS = [
    { id: 'timestamp_col', label: 'Timestamp Column' },
    { id: 'location_col', label: 'Location/Region Column' },
    { id: 'new_cases_col', label: 'New Cases Column' },
    { id: 'new_deaths_col', label: 'New Deaths Column' },
];

export default function DatasetManager() {
    const [datasets, setDatasets] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isUploading, setIsUploading] = useState(false);

    // Form state
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [dataType, setDataType] = useState('time_series');
    const [file, setFile] = useState(null);

    // Column Mapping state
    const [fileHeaders, setFileHeaders] = useState([]);
    const [columnMapping, setColumnMapping] = useState({});

    const authToken = localStorage.getItem('authToken');

    const fetchDatasets = async () => {
        setIsLoading(true);
        try {
            const response = await fetch('/api/datasets', { headers: { 'Authorization': `Bearer ${authToken}` } });
            const data = await response.json();
            if (response.ok) {
                setDatasets(data.datasets || []);
            } else {
                toast.error(`Failed to fetch datasets: ${data.error}`);
            }
        } catch (error) {
            toast.error("An error occurred while fetching datasets.");
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchDatasets();
    }, []);

    const handleFileChange = async (e) => {
        const selectedFile = e.target.files[0];
        setFile(selectedFile);
        setFileHeaders([]);
        setColumnMapping({});

        if (selectedFile) {
            const formData = new FormData();
            formData.append('file', selectedFile);

            try {
                const response = await fetch('/api/datasets/get-headers', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${authToken}` },
                    body: formData,
                });
                const result = await response.json();
                if (response.ok) {
                    setFileHeaders(result.headers);
                    toast.info("File headers detected. Please map the columns.");
                } else {
                    toast.error(`Error reading file: ${result.error}`);
                    setFile(null);
                }
            } catch (error) {
                toast.error("Could not get file headers.");
                setFile(null);
            }
        }
    };

    const handleMappingChange = (internalName, headerName) => {
        setColumnMapping(prev => ({ ...prev, [internalName]: headerName }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file || Object.keys(columnMapping).length < REQUIRED_MAPPINGS.length) {
            toast.error("Please select a file and map all required columns.");
            return;
        }
        setIsUploading(true);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', name);
        formData.append('description', description);
        formData.append('data_type', dataType);
        formData.append('column_mapping', JSON.stringify(columnMapping));

        try {
            const response = await fetch('/api/datasets', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${authToken}` },
                body: formData,
            });
            const result = await response.json();
            if (response.ok) {
                toast.success("Dataset uploaded successfully!");
                fetchDatasets(); // Refresh list
                // Reset form
                setName('');
                setDescription('');
                setFile(null);
                setFileHeaders([]);
                setColumnMapping({});
                e.target.reset(); // Reset file input
            } else {
                toast.error(`Upload failed: ${result.error}`);
            }
        } catch (error) {
            toast.error("An unexpected error occurred during upload.");
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-4 md:p-6">
            <Toaster richColors />
            <div className="lg:col-span-1">
                <form onSubmit={handleSubmit}>
                    <Card>
                        <CardHeader>
                            <CardTitle>Upload New Dataset</CardTitle>
                            <CardDescription>Import data with flexible column mapping.</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div><Label htmlFor="name">Dataset Name</Label><Input id="name" value={name} onChange={e => setName(e.target.value)} required /></div>
                            <div><Label htmlFor="description">Description</Label><Textarea id="description" value={description} onChange={e => setDescription(e.target.value)} /></div>
                            <div><Label htmlFor="file">Data File (CSV/JSON)</Label><Input id="file" type="file" onChange={handleFileChange} accept=".csv,.json" required /></div>

                            {fileHeaders.length > 0 && (
                                <div className="space-y-3 pt-4 border-t">
                                    <h4 className="font-medium">Map Your Columns</h4>
                                    <p className="text-sm text-muted-foreground">Match the required fields to the columns from your file.</p>
                                    {REQUIRED_MAPPINGS.map(req => (
                                        <div key={req.id}>
                                            <Label>{req.label}</Label>
                                            <Select onValueChange={(value) => handleMappingChange(req.id, value)} value={columnMapping[req.id] || ''}>
                                                <SelectTrigger><SelectValue placeholder="Select column from your file" /></SelectTrigger>
                                                <SelectContent>
                                                    {fileHeaders.map(h => <SelectItem key={h} value={h}>{h}</SelectItem>)}
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                        <CardFooter>
                            <Button type="submit" className="w-full" disabled={isUploading}>
                                {isUploading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Uploading...</> : 'Upload Dataset'}
                            </Button>
                        </CardFooter>
                    </Card>
                </form>
            </div>

            <div className="lg:col-span-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Managed Datasets</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Type</TableHead><TableHead>Records</TableHead><TableHead>Validated</TableHead></TableRow></TableHeader>
                            <TableBody>
                                {isLoading ? <TableRow><TableCell colSpan="4" className="text-center">Loading...</TableCell></TableRow> :
                                    datasets.map(d => (
                                        <TableRow key={d.id}>
                                            <TableCell className="font-medium">{d.name}</TableCell>
                                            <TableCell>{d.data_type}</TableCell>
                                            <TableCell>{d.record_count}</TableCell>
                                            <TableCell>{d.is_validated ? <Check className="text-green-500" /> : <X className="text-red-500" />}</TableCell>
                                        </TableRow>
                                    ))}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}