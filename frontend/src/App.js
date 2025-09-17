import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import io from 'socket.io-client';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import { format } from 'date-fns';
import './App.css';

// Import shadcn components
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Alert, AlertDescription } from './components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { ScrollArea } from './components/ui/scroll-area';
import { Separator } from './components/ui/separator';
import { Input } from './components/ui/input';
import { Textarea } from './components/ui/textarea';

// Icons
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Server, 
  Router,
  Monitor,
  Shield,
  MessageCircle,
  Send,
  Bot,
  Wifi,
  Globe,
  BarChart3,
  TrendingUp,
  Zap
} from 'lucide-react';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [nodes, setNodes] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  // Fetch initial data
  useEffect(() => {
    fetchNodes();
    fetchAlerts();
    fetchChatHistory();
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const wsUrl = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');
    wsRef.current = new WebSocket(`${wsUrl}/api/ws`);
    
    wsRef.current.onopen = () => {
      setWsConnected(true);
      console.log('WebSocket connected');
    };
    
    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'network_update') {
          setNodes(data.nodes);
        }
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };
    
    wsRef.current.onclose = () => {
      setWsConnected(false);
      console.log('WebSocket disconnected');
      // Reconnect after 5 seconds
      setTimeout(connectWebSocket, 5000);
    };
    
    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  };

  const fetchNodes = async () => {
    try {
      const response = await axios.get(`${API}/nodes`);
      setNodes(response.data);
    } catch (error) {
      console.error('Error fetching nodes:', error);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await axios.get(`${API}/alerts`);
      setAlerts(response.data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  const fetchChatHistory = async () => {
    try {
      const response = await axios.get(`${API}/chat/history`);
      setChatHistory(response.data);
    } catch (error) {
      console.error('Error fetching chat history:', error);
    }
  };

  const handleDiagnosis = async () => {
    if (!currentQuery.trim()) return;
    
    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/diagnosis`, {
        query: currentQuery,
        context: { nodes: nodes.length, alerts: alerts.length }
      });
      
      setCurrentQuery('');
      await fetchChatHistory();
    } catch (error) {
      console.error('Error getting diagnosis:', error);
    }
    setIsLoading(false);
  };

  const resolveAlert = async (alertId) => {
    try {
      await axios.post(`${API}/alerts/${alertId}/resolve`);
      await fetchAlerts();
    } catch (error) {
      console.error('Error resolving alert:', error);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'online': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'critical': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'offline': return <XCircle className="h-4 w-4 text-gray-500" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  const getNodeIcon = (type) => {
    switch (type) {
      case 'server': return <Server className="h-4 w-4" />;
      case 'router': return <Router className="h-4 w-4" />;
      case 'switch': return <Wifi className="h-4 w-4" />;
      case 'workstation': return <Monitor className="h-4 w-4" />;
      case 'security': return <Shield className="h-4 w-4" />;
      default: return <Globe className="h-4 w-4" />;
    }
  };

  const getSeverityBadge = (severity) => {
    const colors = {
      low: 'bg-blue-100 text-blue-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800'
    };
    return <Badge className={colors[severity] || colors.medium}>{severity}</Badge>;
  };

  // Chart data preparation
  const getPerformanceChartData = () => {
    const onlineNodes = nodes.filter(n => n.status === 'online');
    const labels = onlineNodes.slice(0, 8).map(n => n.name);
    
    return {
      labels,
      datasets: [
        {
          label: 'CPU Usage (%)',
          data: onlineNodes.slice(0, 8).map(n => n.cpu_usage),
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4,
        },
        {
          label: 'Memory Usage (%)',
          data: onlineNodes.slice(0, 8).map(n => n.memory_usage),
          borderColor: 'rgb(16, 185, 129)',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.4,
        }
      ]
    };
  };

  const getNetworkStatusData = () => {
    const statusCounts = nodes.reduce((acc, node) => {
      acc[node.status] = (acc[node.status] || 0) + 1;
      return acc;
    }, {});

    return {
      labels: Object.keys(statusCounts),
      datasets: [{
        data: Object.values(statusCounts),
        backgroundColor: [
          '#10B981', // green for online
          '#F59E0B', // yellow for warning
          '#EF4444', // red for critical
          '#6B7280', // gray for offline
        ],
        borderWidth: 0,
      }]
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
      }
    }
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-4xl font-bold text-white tracking-tight">
              SecureWatch AI
            </h1>
            <p className="text-slate-400 text-lg">
              Intelligent Enterprise Network Monitoring & Diagnosis
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm">
              <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-400' : 'bg-red-400'}`} />
              <span className="text-slate-300">
                {wsConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            
            <Badge variant="outline" className="bg-slate-800 text-slate-200 border-slate-600">
              {nodes.length} Nodes
            </Badge>
            
            <Badge variant="outline" className="bg-slate-800 text-slate-200 border-slate-600">
              {alerts.length} Alerts
            </Badge>
          </div>
        </div>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4 bg-slate-800 border-slate-700">
            <TabsTrigger value="dashboard" className="data-[state=active]:bg-slate-700 text-slate-200">
              <BarChart3 className="h-4 w-4 mr-2" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="topology" className="data-[state=active]:bg-slate-700 text-slate-200">
              <Globe className="h-4 w-4 mr-2" />
              Network Map
            </TabsTrigger>
            <TabsTrigger value="alerts" className="data-[state=active]:bg-slate-700 text-slate-200">
              <AlertTriangle className="h-4 w-4 mr-2" />
              Alerts
            </TabsTrigger>
            <TabsTrigger value="ai-chat" className="data-[state=active]:bg-slate-700 text-slate-200">
              <Bot className="h-4 w-4 mr-2" />
              AI Assistant
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Metrics Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-200">Total Nodes</CardTitle>
                  <Server className="h-4 w-4 text-slate-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">{nodes.length}</div>
                  <p className="text-xs text-slate-400">
                    {nodes.filter(n => n.status === 'online').length} online
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-200">Active Alerts</CardTitle>
                  <AlertTriangle className="h-4 w-4 text-slate-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">{alerts.length}</div>
                  <p className="text-xs text-slate-400">
                    {alerts.filter(a => a.severity === 'critical').length} critical
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-200">Avg Latency</CardTitle>
                  <TrendingUp className="h-4 w-4 text-slate-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-white">
                    {nodes.length > 0 ? 
                      (nodes.reduce((sum, n) => sum + n.network_latency, 0) / nodes.length).toFixed(1) : 
                      '0.0'
                    }ms
                  </div>
                  <p className="text-xs text-slate-400">network performance</p>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-200">System Health</CardTitle>
                  <Zap className="h-4 w-4 text-slate-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-400">
                    {((nodes.filter(n => n.status === 'online').length / Math.max(nodes.length, 1)) * 100).toFixed(0)}%
                  </div>
                  <p className="text-xs text-slate-400">uptime score</p>
                </CardContent>
              </Card>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-slate-200">Performance Metrics</CardTitle>
                  <CardDescription className="text-slate-400">
                    CPU and Memory usage across nodes
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    {nodes.length > 0 && <Line data={getPerformanceChartData()} options={chartOptions} />}
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-slate-200">Network Status</CardTitle>
                  <CardDescription className="text-slate-400">
                    Distribution of node statuses
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    {nodes.length > 0 && <Doughnut data={getNetworkStatusData()} options={doughnutOptions} />}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Network Topology Tab */}
          <TabsContent value="topology" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-slate-200">Network Topology</CardTitle>
                    <CardDescription className="text-slate-400">
                      Visual representation of your network infrastructure
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="relative h-96 bg-slate-900 rounded-lg border border-slate-700 overflow-hidden">
                      <svg className="w-full h-full">
                        {/* Network connections (simplified) */}
                        <defs>
                          <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#334155" strokeWidth="1" opacity="0.3"/>
                          </pattern>
                        </defs>
                        <rect width="100%" height="100%" fill="url(#grid)" />
                        
                        {/* Render nodes */}
                        {nodes.map((node, index) => (
                          <g key={node.id}>
                            <circle
                              cx={node.location?.x || (index % 5) * 120 + 60}
                              cy={node.location?.y || Math.floor(index / 5) * 80 + 60}
                              r="20"
                              fill={
                                node.status === 'online' ? '#10B981' :
                                node.status === 'warning' ? '#F59E0B' :
                                node.status === 'critical' ? '#EF4444' : '#6B7280'
                              }
                              className="drop-shadow-lg"
                            />
                            <text
                              x={node.location?.x || (index % 5) * 120 + 60}
                              y={node.location?.y + 35 || Math.floor(index / 5) * 80 + 95}
                              textAnchor="middle"
                              className="text-xs fill-slate-300"
                            >
                              {node.name}
                            </text>
                          </g>
                        ))}
                      </svg>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="space-y-4">
                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-sm text-slate-200">Node Details</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-80">
                      <div className="space-y-3">
                        {nodes.map((node) => (
                          <div key={node.id} className="p-3 bg-slate-900 rounded-lg border border-slate-700">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center space-x-2">
                                {getNodeIcon(node.type)}
                                <span className="text-sm font-medium text-slate-200">{node.name}</span>
                              </div>
                              {getStatusIcon(node.status)}
                            </div>
                            
                            <div className="text-xs text-slate-400 space-y-1">
                              <div>IP: {node.ip_address}</div>
                              <div>CPU: {node.cpu_usage?.toFixed(1)}%</div>
                              <div>Memory: {node.memory_usage?.toFixed(1)}%</div>
                              <div>Latency: {node.network_latency?.toFixed(1)}ms</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* Alerts Tab */}
          <TabsContent value="alerts" className="space-y-6">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-slate-200">Active Network Alerts</CardTitle>
                <CardDescription className="text-slate-400">
                  Real-time alerts and incidents requiring attention
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-96">
                  <div className="space-y-4">
                    {alerts.length === 0 ? (
                      <div className="text-center py-8 text-slate-400">
                        <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500" />
                        <p>No active alerts - all systems operational</p>
                      </div>
                    ) : (
                      alerts.map((alert) => (
                        <Alert key={alert.id} className="bg-slate-900 border-slate-700">
                          <AlertTriangle className="h-4 w-4" />
                          <AlertDescription className="flex items-center justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-1">
                                {getSeverityBadge(alert.severity)}
                                <Badge variant="outline" className="text-xs">
                                  {alert.alert_type}
                                </Badge>
                              </div>
                              <p className="text-slate-200">{alert.message}</p>
                              <p className="text-xs text-slate-400 mt-1">
                                {format(new Date(alert.timestamp), 'MMM dd, yyyy HH:mm:ss')}
                              </p>
                            </div>
                            <Button
                              size="sm"
                              onClick={() => resolveAlert(alert.id)}
                              className="bg-green-600 hover:bg-green-700"
                            >
                              Resolve
                            </Button>
                          </AlertDescription>
                        </Alert>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          {/* AI Chat Tab */}
          <TabsContent value="ai-chat" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2 text-slate-200">
                      <Bot className="h-5 w-5" />
                      <span>AI Network Assistant</span>
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                      Get intelligent analysis and recommendations for your network
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-96 mb-4">
                      <div className="space-y-4">
                        {chatHistory.length === 0 ? (
                          <div className="text-center py-8 text-slate-400">
                            <MessageCircle className="h-12 w-12 mx-auto mb-4" />
                            <p>Start a conversation with the AI assistant</p>
                            <p className="text-sm mt-2">Ask about network issues, performance, or get recommendations</p>
                          </div>
                        ) : (
                          chatHistory.map((chat) => (
                            <div key={chat.id} className="space-y-3">
                              <div className="flex justify-end">
                                <div className="bg-blue-600 text-white p-3 rounded-lg max-w-xs lg:max-w-md">
                                  <p className="text-sm">{chat.message}</p>
                                </div>
                              </div>
                              
                              <div className="flex justify-start">
                                <div className="bg-slate-700 text-slate-200 p-3 rounded-lg max-w-xs lg:max-w-md">
                                  <p className="text-sm whitespace-pre-wrap">{chat.response}</p>
                                  <p className="text-xs text-slate-400 mt-2">
                                    {format(new Date(chat.timestamp), 'HH:mm:ss')}
                                  </p>
                                </div>
                              </div>
                              
                              <Separator className="bg-slate-700" />
                            </div>
                          ))
                        )}
                      </div>
                    </ScrollArea>
                    
                    <div className="flex space-x-2">
                      <Textarea
                        placeholder="Ask the AI about network issues, performance analysis, or troubleshooting..."
                        value={currentQuery}
                        onChange={(e) => setCurrentQuery(e.target.value)}
                        className="bg-slate-900 border-slate-700 text-slate-200 flex-1"
                        rows={2}
                      />
                      <Button
                        onClick={handleDiagnosis}
                        disabled={isLoading || !currentQuery.trim()}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        {isLoading ? (
                          <Activity className="h-4 w-4 animate-spin" />
                        ) : (
                          <Send className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="space-y-4">
                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-sm text-slate-200">Quick Actions</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentQuery("Analyze current network performance and identify any issues")}
                      className="w-full text-left justify-start bg-slate-900 border-slate-700 text-slate-200 hover:bg-slate-700"
                    >
                      Analyze Performance
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentQuery("Check for security threats and vulnerabilities")}
                      className="w-full text-left justify-start bg-slate-900 border-slate-700 text-slate-200 hover:bg-slate-700"
                    >
                      Security Check
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentQuery("Diagnose connectivity issues across the network")}
                      className="w-full text-left justify-start bg-slate-900 border-slate-700 text-slate-200 hover:bg-slate-700"
                    >
                      Connectivity Issues
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentQuery("Provide optimization recommendations for better performance")}
                      className="w-full text-left justify-start bg-slate-900 border-slate-700 text-slate-200 hover:bg-slate-700"
                    >
                      Optimization Tips
                    </Button>
                  </CardContent>
                </Card>

                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-sm text-slate-200">System Status</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">AI Assistant</span>
                      <Badge className="bg-green-100 text-green-800">Active</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">Real-time Monitoring</span>
                      <Badge className={wsConnected ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                        {wsConnected ? 'Connected' : 'Disconnected'}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">Network Simulation</span>
                      <Badge className="bg-green-100 text-green-800">Running</Badge>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default App;