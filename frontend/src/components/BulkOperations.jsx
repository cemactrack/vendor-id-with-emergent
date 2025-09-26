import React, { useState, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Progress } from './ui/progress';
import { Upload, Download, FileSpreadsheet, Users, AlertCircle, CheckCircle } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { vendorAPI } from '../services/api';

const BulkOperations = ({ templates = {}, onComplete }) => {
  const [importing, setImporting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [importProgress, setImportProgress] = useState(0);
  const [importResults, setImportResults] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState('standard');
  const fileInputRef = useRef(null);
  const { toast } = useToast();

  const handleImportCSV = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      toast({
        title: "Invalid file",
        description: "Please select a CSV file",
        variant: "destructive"
      });
      return;
    }

    setImporting(true);
    setImportProgress(0);
    setImportResults(null);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setImportProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const result = await vendorAPI.importCSV(file, selectedTemplate);
      
      clearInterval(progressInterval);
      setImportProgress(100);
      setImportResults(result);

      toast({
        title: "Import completed",
        description: `Created ${result.total_created} vendors with ${result.total_errors} errors`
      });
      
      if (onComplete) {
        onComplete();
      }
    } catch (error) {
      toast({
        title: "Import failed",
        description: error.response?.data?.detail || "Failed to import vendors",
        variant: "destructive"
      });
    } finally {
      setImporting(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleExportCSV = async () => {
    setExporting(true);
    try {
      await vendorAPI.exportCSV();
      toast({
        title: "Export completed",
        description: "CSV file has been downloaded"
      });
    } catch (error) {
      toast({
        title: "Export failed",
        description: "Failed to export vendors",
        variant: "destructive"
      });
    } finally {
      setExporting(false);
    }
  };

  const downloadTemplate = () => {
    const csvTemplate = `name,email,phone,address,company,department,position
JOHN DOE,john@example.com,+1234567890,"123 Main St, City",ACME Corp,IT,Developer
JANE SMITH,jane@example.com,+0987654321,"456 Oak Ave, Town",Tech Inc,HR,Manager`;
    
    const blob = new Blob([csvTemplate], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'vendor_import_template.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    toast({
      title: "Template downloaded",
      description: "CSV template has been downloaded"
    });
  };

  return (
    <div className="space-y-6">
      {/* Import Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Upload className="w-5 h-5" />
            <span>Bulk Import Vendors</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="template-select">Default Template for Import</Label>
            <Select value={selectedTemplate} onValueChange={setSelectedTemplate}>
              <SelectTrigger>
                <SelectValue placeholder="Select template" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(templates).map(([key, template]) => (
                  <SelectItem key={key} value={key}>
                    <div className="flex items-center space-x-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: template.colors?.primary || '#16a34a' }}
                      ></div>
                      <span>{template.name}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleImportCSV}
                className="hidden"
              />
              <Button 
                onClick={() => fileInputRef.current?.click()}
                disabled={importing}
                className="w-full"
              >
                <Upload className="w-4 h-4 mr-2" />
                {importing ? 'Importing...' : 'Select CSV File'}
              </Button>
            </div>
            
            <Button 
              onClick={downloadTemplate}
              variant="outline"
              className="md:w-auto"
            >
              <FileSpreadsheet className="w-4 h-4 mr-2" />
              Download Template
            </Button>
          </div>

          {importing && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Importing vendors...</span>
                <span>{importProgress}%</span>
              </div>
              <Progress value={importProgress} className="w-full" />
            </div>
          )}

          {importResults && (
            <div className="space-y-2">
              <div className="flex items-center space-x-2 text-green-600">
                <CheckCircle className="w-4 h-4" />
                <span className="font-medium">Import Results</span>
              </div>
              <div className="bg-green-50 border border-green-200 rounded-md p-3 text-sm">
                <p>✅ Successfully created: {importResults.total_created} vendors</p>
                {importResults.total_errors > 0 && (
                  <p className="text-red-600">❌ Errors: {importResults.total_errors}</p>
                )}
              </div>
              {importResults.errors && importResults.errors.length > 0 && (
                <details className="bg-red-50 border border-red-200 rounded-md p-3">
                  <summary className="cursor-pointer text-red-600 font-medium">View Errors</summary>
                  <div className="mt-2 space-y-1 text-sm">
                    {importResults.errors.map((error, index) => (
                      <div key={index} className="text-red-600">
                        Row {error.index + 1} ({error.name}): {error.error}
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          )}

          <div className="bg-blue-50 border border-blue-200 rounded-md p-3 text-sm">
            <div className="flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-blue-600 mt-0.5" />
              <div>
                <p className="font-medium text-blue-800">CSV Format Requirements:</p>
                <ul className="mt-1 text-blue-700 space-y-1">
                  <li>• Required column: <code>name</code></li>
                  <li>• Optional columns: <code>email</code>, <code>phone</code>, <code>address</code>, <code>company</code>, <code>department</code>, <code>position</code></li>
                  <li>• Names will be automatically converted to UPPERCASE</li>
                  <li>• Issue date will be set to current date</li>
                  <li>• Expiry date will be calculated automatically (1 year from issue)</li>
                </ul>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Export Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Download className="w-5 h-5" />
            <span>Export Vendors</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Export all vendors to a CSV file for backup or external processing.
            </p>
            
            <Button 
              onClick={handleExportCSV}
              disabled={exporting}
              className="w-full md:w-auto"
            >
              <Download className="w-4 h-4 mr-2" />
              {exporting ? 'Exporting...' : 'Export All Vendors'}
            </Button>
            
            <div className="bg-gray-50 border border-gray-200 rounded-md p-3 text-sm text-gray-600">
              <p>The exported CSV will include all vendor information including:</p>
              <p>ID, Name, Email, Phone, Address, Company, Department, Position, Status, Dates, and Template</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default BulkOperations;