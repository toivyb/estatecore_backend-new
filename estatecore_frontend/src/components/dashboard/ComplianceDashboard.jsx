/**
 * Comprehensive Compliance Dashboard Component
 * Main interface for the Automated Compliance Monitoring system
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Alert,
  AlertDescription,
  Badge,
  Button,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Progress,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
  Input,
  Label,
  Textarea,
  CheckboxGroup,
  Checkbox,
  Switch,
  Separator
} from '../ui';
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Shield,
  FileText,
  Users,
  Bell,
  Settings,
  Download,
  RefreshCw,
  Plus,
  Eye,
  Filter,
  Search,
  Calendar,
  BarChart3,
  PieChart,
  LineChart,
  Activity,
  Building,
  BookOpen,
  Gavel
} from 'lucide-react';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, PieChart as RechartsPieChart, Cell, AreaChart, Area } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const ComplianceDashboard = () => {
  // State management
  const [dashboardData, setDashboardData] = useState({
    overview: {},
    metrics: [],
    violations: [],
    alerts: [],
    regulations: [],
    properties: []
  });
  const [loading, setLoading] = useState(true);
  const [selectedProperty, setSelectedProperty] = useState('all');
  const [selectedTimeRange, setSelectedTimeRange] = useState('30');
  const [activeTab, setActiveTab] = useState('overview');
  const [filters, setFilters] = useState({
    severity: 'all',
    status: 'all',
    regulationType: 'all'
  });
  const [selectedViolation, setSelectedViolation] = useState(null);
  const [showReportDialog, setShowReportDialog] = useState(false);
  const [reportConfig, setReportConfig] = useState({
    type: 'executive_dashboard',
    format: 'pdf',
    includeCharts: true,
    includeRecommendations: true
  });

  // API functions
  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Fetch dashboard overview
      const overviewResponse = await fetch('/api/compliance/dashboard/overview');
      const overviewData = await overviewResponse.json();
      
      // Fetch metrics
      const metricsResponse = await fetch(`/api/compliance/dashboard/metrics?days_back=${selectedTimeRange}`);
      const metricsData = await metricsResponse.json();
      
      // Fetch recent violations
      const violationsResponse = await fetch(`/api/compliance/violations?page=1&per_page=20${selectedProperty !== 'all' ? `&property_id=${selectedProperty}` : ''}`);
      const violationsData = await violationsResponse.json();
      
      // Fetch active alerts
      const alertsResponse = await fetch('/api/compliance/alerts?unacknowledged_only=true');
      const alertsData = await alertsResponse.json();
      
      // Fetch regulations
      const regulationsResponse = await fetch('/api/compliance/regulations');
      const regulationsData = await regulationsResponse.json();

      setDashboardData({
        overview: overviewData.success ? overviewData.overview : {},
        metrics: metricsData.success ? metricsData.metrics : [],
        violations: violationsData.success ? violationsData.violations : [],
        alerts: alertsData.success ? alertsData.alerts : [],
        regulations: regulationsData.success ? regulationsData.regulations : [],
        properties: [] // Would be fetched from properties API
      });
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedProperty, selectedTimeRange]);

  const runViolationDetection = async () => {
    try {
      const response = await fetch('/api/compliance/violations/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          property_ids: selectedProperty !== 'all' ? [selectedProperty] : null 
        })
      });
      const result = await response.json();
      
      if (result.success) {
        alert('Violation detection completed successfully');
        fetchDashboardData(); // Refresh data
      } else {
        alert('Violation detection failed: ' + result.error);
      }
    } catch (error) {
      alert('Error running violation detection: ' + error.message);
    }
  };

  const generateReport = async () => {
    try {
      const response = await fetch('/api/compliance/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report_type: reportConfig.type,
          format: reportConfig.format,
          title: `Compliance Report - ${new Date().toLocaleDateString()}`,
          property_ids: selectedProperty !== 'all' ? [selectedProperty] : null,
          include_charts: reportConfig.includeCharts,
          include_recommendations: reportConfig.includeRecommendations
        })
      });
      const result = await response.json();
      
      if (result.success && result.report_data) {
        // Handle different report formats
        if (reportConfig.format === 'pdf') {
          // Create download link for PDF
          const blob = new Blob([atob(result.report_data)], { type: 'application/pdf' });
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `compliance_report_${Date.now()}.pdf`;
          link.click();
          window.URL.revokeObjectURL(url);
        } else {
          console.log('Report generated:', result.report_data);
        }
        
        setShowReportDialog(false);
        alert('Report generated successfully');
      } else {
        alert('Report generation failed: ' + result.error);
      }
    } catch (error) {
      alert('Error generating report: ' + error.message);
    }
  };

  const acknowledgeAlert = async (alertId) => {
    try {
      const response = await fetch(`/api/compliance/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'current_user', notes: 'Acknowledged from dashboard' })
      });
      const result = await response.json();
      
      if (result.success) {
        fetchDashboardData(); // Refresh data
      } else {
        alert('Failed to acknowledge alert: ' + result.error);
      }
    } catch (error) {
      alert('Error acknowledging alert: ' + error.message);
    }
  };

  const resolveViolation = async (violationId, resolutionNotes) => {
    try {
      const response = await fetch(`/api/compliance/violations/${violationId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resolution_notes: resolutionNotes })
      });
      const result = await response.json();
      
      if (result.success) {
        fetchDashboardData(); // Refresh data
        setSelectedViolation(null);
      } else {
        alert('Failed to resolve violation: ' + result.error);
      }
    } catch (error) {
      alert('Error resolving violation: ' + error.message);
    }
  };

  // Effects
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Helper functions
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      case 'informational': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getComplianceScoreColor = (score) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-yellow-600';
    if (score >= 60) return 'text-orange-600';
    return 'text-red-600';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  // Chart data preparation
  const prepareMetricsChartData = () => {
    return dashboardData.metrics.map(metric => ({
      date: formatDate(metric.date),
      'Compliance Score': metric.overall_score,
      'Risk Score': 100 - metric.risk_score, // Invert risk score for better visualization
      'Violations': metric.total_violations
    }));
  };

  const prepareViolationSeverityData = () => {
    const severityCounts = {};
    dashboardData.violations.forEach(violation => {
      severityCounts[violation.severity] = (severityCounts[violation.severity] || 0) + 1;
    });
    
    return Object.entries(severityCounts).map(([severity, count]) => ({
      name: severity.charAt(0).toUpperCase() + severity.slice(1),
      value: count
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading compliance data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Compliance Dashboard</h1>
          <p className="text-gray-600">Automated compliance monitoring and management</p>
        </div>
        
        <div className="flex space-x-3">
          <Select value={selectedProperty} onValueChange={setSelectedProperty}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select Property" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Properties</SelectItem>
              {dashboardData.properties.map(property => (
                <SelectItem key={property.id} value={property.id}>
                  {property.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Select value={selectedTimeRange} onValueChange={setSelectedTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">7 Days</SelectItem>
              <SelectItem value="30">30 Days</SelectItem>
              <SelectItem value="90">90 Days</SelectItem>
              <SelectItem value="365">1 Year</SelectItem>
            </SelectContent>
          </Select>
          
          <Button onClick={runViolationDetection} variant="outline">
            <Activity className="h-4 w-4 mr-2" />
            Run Detection
          </Button>
          
          <Dialog open={showReportDialog} onOpenChange={setShowReportDialog}>
            <DialogTrigger asChild>
              <Button>
                <Download className="h-4 w-4 mr-2" />
                Generate Report
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Generate Compliance Report</DialogTitle>
                <DialogDescription>
                  Configure and generate a comprehensive compliance report.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="report-type">Report Type</Label>
                  <Select value={reportConfig.type} onValueChange={(value) => setReportConfig({...reportConfig, type: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="executive_dashboard">Executive Dashboard</SelectItem>
                      <SelectItem value="violation_analysis">Violation Analysis</SelectItem>
                      <SelectItem value="property_compliance">Property Compliance</SelectItem>
                      <SelectItem value="regulatory_compliance">Regulatory Compliance</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="report-format">Format</Label>
                  <Select value={reportConfig.format} onValueChange={(value) => setReportConfig({...reportConfig, format: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pdf">PDF</SelectItem>
                      <SelectItem value="html">HTML</SelectItem>
                      <SelectItem value="excel">Excel</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="include-charts"
                    checked={reportConfig.includeCharts}
                    onCheckedChange={(checked) => setReportConfig({...reportConfig, includeCharts: checked})}
                  />
                  <Label htmlFor="include-charts">Include Charts</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="include-recommendations"
                    checked={reportConfig.includeRecommendations}
                    onCheckedChange={(checked) => setReportConfig({...reportConfig, includeRecommendations: checked})}
                  />
                  <Label htmlFor="include-recommendations">Include Recommendations</Label>
                </div>
                <Button onClick={generateReport} className="w-full">
                  Generate Report
                </Button>
              </div>
            </DialogContent>
          </Dialog>
          
          <Button variant="outline" onClick={fetchDashboardData}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Compliance Score</p>
                <p className={`text-2xl font-bold ${getComplianceScoreColor(dashboardData.overview.overall_compliance_score || 0)}`}>
                  {(dashboardData.overview.overall_compliance_score || 0).toFixed(1)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <AlertTriangle className="h-8 w-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Risk Score</p>
                <p className="text-2xl font-bold text-orange-600">
                  {(dashboardData.overview.risk_score || 0).toFixed(1)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <XCircle className="h-8 w-8 text-red-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Recent Violations</p>
                <p className="text-2xl font-bold text-red-600">
                  {dashboardData.overview.recent_violations || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Clock className="h-8 w-8 text-yellow-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Overdue Items</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {dashboardData.overview.overdue_requirements || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Bell className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Alerts</p>
                <p className="text-2xl font-bold text-purple-600">
                  {dashboardData.overview.unacknowledged_alerts || 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Alerts Banner */}
      {dashboardData.alerts.length > 0 && (
        <Alert className="border-orange-200 bg-orange-50">
          <AlertTriangle className="h-4 w-4 text-orange-600" />
          <AlertDescription className="text-orange-800">
            You have {dashboardData.alerts.length} unacknowledged compliance alerts requiring attention.
            <Button variant="link" className="p-0 h-auto ml-2 text-orange-800" onClick={() => setActiveTab('alerts')}>
              View Alerts →
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="violations">Violations</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="regulations">Regulations</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Compliance Trends Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Compliance Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsLineChart data={prepareMetricsChartData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <RechartsTooltip />
                    <Line type="monotone" dataKey="Compliance Score" stroke="#8884d8" strokeWidth={2} />
                    <Line type="monotone" dataKey="Risk Score" stroke="#82ca9d" strokeWidth={2} />
                  </RechartsLineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Violation Severity Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Violation Severity Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsPieChart>
                    <Pie
                      dataKey="value"
                      isAnimationActive={false}
                      data={prepareViolationSeverityData()}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      label
                    >
                      {prepareViolationSeverityData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Recent Violations Table */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Violations</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Property</TableHead>
                    <TableHead>Violation Type</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Detected</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dashboardData.violations.slice(0, 10).map((violation) => (
                    <TableRow key={violation.id}>
                      <TableCell className="font-medium">{violation.property_id}</TableCell>
                      <TableCell>{violation.violation_type}</TableCell>
                      <TableCell>
                        <Badge className={getSeverityColor(violation.severity)}>
                          {violation.severity}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatDate(violation.detected_date)}</TableCell>
                      <TableCell>
                        {violation.is_resolved ? (
                          <Badge className="bg-green-100 text-green-800">Resolved</Badge>
                        ) : (
                          <Badge className="bg-red-100 text-red-800">Open</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedViolation(violation)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="violations" className="space-y-6">
          {/* Violations Filters */}
          <Card>
            <CardContent className="p-6">
              <div className="flex space-x-4">
                <div className="flex-1">
                  <Label htmlFor="search-violations">Search Violations</Label>
                  <Input
                    id="search-violations"
                    placeholder="Search by type, description..."
                    className="w-full"
                  />
                </div>
                <div>
                  <Label htmlFor="severity-filter">Severity</Label>
                  <Select value={filters.severity} onValueChange={(value) => setFilters({...filters, severity: value})}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="critical">Critical</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="low">Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="status-filter">Status</Label>
                  <Select value={filters.status} onValueChange={(value) => setFilters({...filters, status: value})}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="open">Open</SelectItem>
                      <SelectItem value="resolved">Resolved</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Violations List */}
          <Card>
            <CardHeader>
              <CardTitle>All Violations</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Property</TableHead>
                    <TableHead>Violation Type</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Detected</TableHead>
                    <TableHead>Detection Method</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dashboardData.violations.map((violation) => (
                    <TableRow key={violation.id}>
                      <TableCell className="font-medium">{violation.property_id}</TableCell>
                      <TableCell>{violation.violation_type}</TableCell>
                      <TableCell>{violation.title}</TableCell>
                      <TableCell>
                        <Badge className={getSeverityColor(violation.severity)}>
                          {violation.severity}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatDate(violation.detected_date)}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{violation.detection_method}</Badge>
                      </TableCell>
                      <TableCell>
                        {violation.is_resolved ? (
                          <Badge className="bg-green-100 text-green-800">Resolved</Badge>
                        ) : (
                          <Badge className="bg-red-100 text-red-800">Open</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex space-x-2">
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => setSelectedViolation(violation)}
                                >
                                  <Eye className="h-4 w-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>View Details</TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Active Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {dashboardData.alerts.map((alert) => (
                  <div key={alert.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <AlertTriangle className={`h-5 w-5 ${alert.priority === 'critical' ? 'text-red-600' : alert.priority === 'high' ? 'text-orange-600' : 'text-yellow-600'}`} />
                      <div>
                        <p className="font-medium">{alert.title}</p>
                        <p className="text-sm text-gray-600">{alert.message}</p>
                        <p className="text-xs text-gray-500">
                          {formatDate(alert.created_at)} • Priority: {alert.priority}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => acknowledgeAlert(alert.id)}
                    >
                      Acknowledge
                    </Button>
                  </div>
                ))}
                {dashboardData.alerts.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <Bell className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No active alerts</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="regulations" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Regulatory Knowledge Base</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {dashboardData.regulations.slice(0, 10).map((regulation) => (
                  <div key={regulation.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium">{regulation.title}</h3>
                        <p className="text-sm text-gray-600 mt-1">{regulation.description}</p>
                        <div className="flex space-x-4 mt-2 text-sm text-gray-500">
                          <span>Type: {regulation.regulation_type}</span>
                          <span>Jurisdiction: {regulation.jurisdiction}</span>
                          <span>Version: {regulation.version}</span>
                        </div>
                      </div>
                      <Badge variant="outline">{regulation.regulation_code}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Compliance Score Trends */}
            <Card>
              <CardHeader>
                <CardTitle>Compliance Score Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={prepareMetricsChartData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <RechartsTooltip />
                    <Area type="monotone" dataKey="Compliance Score" stackId="1" stroke="#8884d8" fill="#8884d8" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Violations by Type */}
            <Card>
              <CardHeader>
                <CardTitle>Violations by Type</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={prepareMetricsChartData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <RechartsTooltip />
                    <Bar dataKey="Violations" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Performance Metrics */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <p className="text-sm font-medium text-gray-600 mb-2">Average Resolution Time</p>
                  <p className="text-2xl font-bold text-blue-600">5.2 days</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600 mb-2">Prevention Rate</p>
                  <p className="text-2xl font-bold text-green-600">78%</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600 mb-2">False Positive Rate</p>
                  <p className="text-2xl font-bold text-yellow-600">12%</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Compliance System Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium mb-4">Detection Settings</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <Label htmlFor="auto-detection">Automatic Violation Detection</Label>
                        <p className="text-sm text-gray-600">Enable continuous monitoring for compliance violations</p>
                      </div>
                      <Switch id="auto-detection" />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <Label htmlFor="ai-analysis">AI-Powered Analysis</Label>
                        <p className="text-sm text-gray-600">Use AI for pattern recognition and prediction</p>
                      </div>
                      <Switch id="ai-analysis" />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <Label htmlFor="real-time-alerts">Real-time Alerts</Label>
                        <p className="text-sm text-gray-600">Send immediate notifications for critical violations</p>
                      </div>
                      <Switch id="real-time-alerts" />
                    </div>
                  </div>
                </div>

                <Separator />

                <div>
                  <h3 className="text-lg font-medium mb-4">Notification Settings</h3>
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="email-notifications">Email Notifications</Label>
                      <CheckboxGroup className="mt-2">
                        <div className="flex items-center space-x-2">
                          <Checkbox id="email-violations" />
                          <Label htmlFor="email-violations">New Violations</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Checkbox id="email-deadlines" />
                          <Label htmlFor="email-deadlines">Upcoming Deadlines</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Checkbox id="email-reports" />
                          <Label htmlFor="email-reports">Weekly Reports</Label>
                        </div>
                      </CheckboxGroup>
                    </div>
                  </div>
                </div>

                <Separator />

                <div>
                  <h3 className="text-lg font-medium mb-4">Integration Settings</h3>
                  <div className="space-y-4">
                    <Button variant="outline">
                      <Settings className="h-4 w-4 mr-2" />
                      Configure Integrations
                    </Button>
                    <Button variant="outline">
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Sync External Data
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Violation Detail Modal */}
      {selectedViolation && (
        <Dialog open={!!selectedViolation} onOpenChange={() => setSelectedViolation(null)}>
          <DialogContent className="sm:max-w-2xl">
            <DialogHeader>
              <DialogTitle>{selectedViolation.title}</DialogTitle>
              <DialogDescription>
                Violation details and resolution options
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Property ID</Label>
                  <p className="font-medium">{selectedViolation.property_id}</p>
                </div>
                <div>
                  <Label>Severity</Label>
                  <Badge className={getSeverityColor(selectedViolation.severity)}>
                    {selectedViolation.severity}
                  </Badge>
                </div>
                <div>
                  <Label>Detected Date</Label>
                  <p>{formatDate(selectedViolation.detected_date)}</p>
                </div>
                <div>
                  <Label>Detection Method</Label>
                  <p>{selectedViolation.detection_method}</p>
                </div>
              </div>
              
              <div>
                <Label>Description</Label>
                <p className="text-sm text-gray-600">{selectedViolation.description}</p>
              </div>

              {selectedViolation.ai_recommendations && selectedViolation.ai_recommendations.length > 0 && (
                <div>
                  <Label>AI Recommendations</Label>
                  <ul className="list-disc list-inside text-sm text-gray-600">
                    {selectedViolation.ai_recommendations.map((rec, index) => (
                      <li key={index}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}

              {!selectedViolation.is_resolved && (
                <div>
                  <Label htmlFor="resolution-notes">Resolution Notes</Label>
                  <Textarea
                    id="resolution-notes"
                    placeholder="Enter resolution details..."
                    className="mt-1"
                  />
                  <Button
                    className="mt-2"
                    onClick={() => {
                      const notes = document.getElementById('resolution-notes').value;
                      resolveViolation(selectedViolation.id, notes);
                    }}
                  >
                    Mark as Resolved
                  </Button>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default ComplianceDashboard;