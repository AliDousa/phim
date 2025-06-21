import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button.jsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Input } from '@/components/ui/input.jsx';
import { Label } from '@/components/ui/label.jsx';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table.jsx';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert.jsx';
import { Badge } from '@/components/ui/badge.jsx';
import { Skeleton } from '@/components/ui/skeleton.jsx';
import { UploadCloud, Trash2, FileText, AlertCircle, Inbox } from 'lucide-react';

// This is a placeholder for your actual JWT token.
// In a real app, you would get this from localStorage, a cookie, or a context.
const MOCK_JWT_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...";

export default function DatasetManagement() {
  const [datasets, setDatasets] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const fetchDatasets = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/datasets', {
        headers: {
          'Authorization': `Bearer ${MOCK_JWT_TOKEN}`
        }
      });
      if (!response.ok) {
        throw new Error(`Failed to fetch datasets: ${response.statusText}`);
      }
      const data = await response.json();
      setDatasets(data.datasets || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDatasets();
  }, [fetchDatasets]);

  const handleUpload = async (event) => {
    event.preventDefault();
    setIsUploading(true);
    setUploadError(null);
    
    const formData = new FormData(event.target);
    const file = formData.get('file');

    if (!file || file.size === 0) {
      setUploadError("Please select a file to upload.");
      setIsUploading(false);
      return;
    }

    try {
      // NOTE: No 'Content-Type' header is set here. The browser automatically
      // sets it to 'multipart/form-data' and includes the boundary.
      const response = await fetch('/api/datasets', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${MOCK_JWT_TOKEN}`
        },
        body: formData
      });

      if (!response.ok) {
        let errorMessage = `HTTP error! Status: ${response.status}`;
        try {
          const contentType = response.headers.get("content-type");
          if (contentType && contentType.indexOf("application/json") !== -1) {
            const errData = await response.json();
            errorMessage = errData.error?.message || JSON.stringify(errData);
          } else {
            errorMessage = await response.text();
          }
        } catch (e) {
            errorMessage = `Failed to parse server error response. Status: ${response.status}`;
        }
        throw new Error(errorMessage);
      }
      
      event.target.reset();
      await fetchDatasets();

    } catch (err) {
      setUploadError(err.message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (datasetId) => {
    if (!window.confirm("Are you sure you want to delete this dataset? This action cannot be undone.")) {
      return;
    }

    try {
      const response = await fetch(`/api/datasets/${datasetId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${MOCK_JWT_TOKEN}`
        }
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error?.message || 'Failed to delete dataset.');
      }
      await fetchDatasets();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <TableBody>
          {[...Array(3)].map((_, i) => (
            <TableRow key={i}>
              <TableCell><Skeleton className="h-4 w-32" /></TableCell>
              <TableCell><Skeleton className="h-4 w-24" /></TableCell>
              <TableCell><Skeleton className="h-4 w-24" /></TableCell>
              <TableCell><Skeleton className="h-4 w-48" /></TableCell>
              <TableCell><Skeleton className="h-8 w-8" /></TableCell>
            </TableRow>
          ))}
        </TableBody>
      );
    }

    if (error) {
      return (
        <TableBody>
          <TableRow>
            <TableCell colSpan={5}>
              <div className="flex flex-col items-center justify-center p-8 text-center">
                <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
                <p className="font-medium">Failed to load datasets</p>
                <p className="text-sm text-gray-600">{error}</p>
              </div>
            </TableCell>
          </TableRow>
        </TableBody>
      );
    }

    if (datasets.length === 0) {
      return (
        <TableBody>
          <TableRow>
            <TableCell colSpan={5}>
              <div className="flex flex-col items-center justify-center p-8 text-center">
                <Inbox className="h-12 w-12 text-gray-400 mb-4" />
                <p className="font-medium">No datasets found</p>
                <p className="text-sm text-gray-600">Upload a dataset to get started.</p>
              </div>
            </TableCell>
          </TableRow>
        </TableBody>
      );
    }

    return (
      <TableBody>
        {datasets.map((dataset) => (
          <TableRow key={dataset.id}>
            <TableCell className="font-medium">{dataset.name}</TableCell>
            <TableCell><Badge variant="outline">{dataset.data_type}</Badge></TableCell>
            {/* This now correctly reads `record_count` from the API response */}
            <TableCell>{dataset.record_count}</TableCell>
            <TableCell>{new Date(dataset.upload_date).toLocaleString()}</TableCell>
            <TableCell>
              <Button variant="ghost" size="icon" onClick={() => handleDelete(dataset.id)}>
                <Trash2 className="h-4 w-4 text-red-500" />
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    );
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Upload New Dataset</CardTitle>
          <CardDescription>Upload a CSV or JSON file for analysis.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleUpload} className="space-y-4">
             {uploadError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Upload Failed</AlertTitle>
                <AlertDescription>
                  <pre className="whitespace-pre-wrap text-xs">{uploadError}</pre>
                </AlertDescription>
              </Alert>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Dataset Name</Label>
                <Input id="name" name="name" placeholder="e.g., COVID-19 Regional Data" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="data_type">Data Type</Label>
                 {/* The name attribute on Select and other form elements is crucial for FormData */}
                <Select name="data_type" required>
                  <SelectTrigger id="data_type">
                    <SelectValue placeholder="Select data type" />
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
              <Label htmlFor="description">Description (Optional)</Label>
              <Input id="description" name="description" placeholder="A brief description of the dataset" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="file">Data File</Label>
              <Input id="file" name="file" type="file" required accept=".csv,.json" />
              <p className="text-sm text-gray-500">Supported formats: CSV, JSON. Max size: 100MB.</p>
            </div>
            <Button type="submit" disabled={isUploading}>
              <UploadCloud className="h-4 w-4 mr-2" />
              {isUploading ? 'Uploading...' : 'Upload Dataset'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Your Datasets</CardTitle>
          <CardDescription>Manage your uploaded datasets.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Records</TableHead>
                <TableHead>Upload Date</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            {renderContent()}
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}