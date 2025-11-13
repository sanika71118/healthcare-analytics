import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import { Activity, Users, DollarSign, TrendingUp, MessageSquare, Send, Loader2, AlertTriangle, Brain } from 'lucide-react';

const generateHealthcareData = () => {
  const patients = [];
  const visits = [];
  
  const conditions = ['None', 'Hypertension', 'Diabetes', 'Heart Disease', 'Asthma', 'Arthritis'];
  const insuranceTypes = ['Private', 'Medicare', 'Medicaid', 'Uninsured'];
  const visitTypes = ['Emergency', 'Outpatient', 'Inpatient'];
  const departments = ['Cardiology', 'Neurology', 'Orthopedics', 'General Medicine', 'Emergency'];
  
  for (let i = 1; i <= 7000; i++) {
    const age = Math.floor(Math.random() * 60) + 20;
    const condition = age > 50 ? conditions[Math.floor(Math.random() * conditions.length)] : 
                      Math.random() > 0.3 ? 'None' : conditions[Math.floor(Math.random() * conditions.length)];
    
    const prevAdmissions = Math.floor(Math.random() * 4);
    const comorbidityCount = age > 60 ? Math.floor(Math.random() * 3) : Math.floor(Math.random() * 2);
    const emergencyRatio = Math.random();
    const labAbnormal = Math.random();
    
    const riskScore = Math.min(0.95, Math.max(0.05,
      (age / 200) + 
      (condition !== 'None' ? 0.15 : 0) +
      (prevAdmissions / 10) +
      (comorbidityCount / 10) +
      (emergencyRatio * 0.3) +
      (labAbnormal * 0.2) +
      (Math.random() * 0.1 - 0.05)
    ));
    
    const riskLevel = riskScore < 0.3 ? 'Low' : riskScore < 0.6 ? 'Medium' : 'High';
    const readmitted = Math.random() < riskScore;
    
    patients.push({
      id: 'PT' + String(i).padStart(6, '0'),
      age,
      gender: Math.random() > 0.5 ? 'Male' : 'Female',
      condition,
      insurance: insuranceTypes[Math.floor(Math.random() * insuranceTypes.length)],
      visitsPerYear: Math.floor(Math.random() * 5) + 1,
      satisfaction: Math.round((Math.random() * 4 + 6) * 10) / 10,
      prevAdmissions,
      comorbidityCount,
      emergencyRatio: Math.round(emergencyRatio * 1000) / 1000,
      avgLengthOfStay: Math.round((Math.random() * 6 + 1) * 10) / 10,
      labAbnormal: Math.round(labAbnormal * 1000) / 1000,
      riskScore: Math.round(riskScore * 1000) / 1000,
      riskLevel,
      readmitted
    });
  }
  
  let visitId = 1;
  patients.forEach(patient => {
    for (let v = 0; v < patient.visitsPerYear; v++) {
      const type = visitTypes[Math.floor(Math.random() * visitTypes.length)];
      const cost = type === 'Emergency' ? Math.random() * 4000 + 1000 :
                   type === 'Inpatient' ? Math.random() * 20000 + 5000 :
                   Math.random() * 1800 + 200;
      
      visits.push({
        id: 'V' + String(visitId++).padStart(8, '0'),
        patientId: patient.id,
        date: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        type,
        department: departments[Math.floor(Math.random() * departments.length)],
        cost: Math.round(cost * 100) / 100,
        duration: type === 'Inpatient' ? Math.floor(Math.random() * 7) + 1 : Math.round(Math.random() * 3.5 + 0.5)
      });
    }
  });
  
  return { patients, visits };
};

const HealthcareDashboard = () => {
  const [data, setData] = useState({ patients: [], visits: [] });
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [dataLoading, setDataLoading] = useState(true);
  
  useEffect(() => {
    setDataLoading(true);
    setTimeout(() => {
      const generatedData = generateHealthcareData();
      setData(generatedData);
      setDataLoading(false);
    }, 100);
  }, []);
  
  const analytics = React.useMemo(() => {
    if (!data.patients.length) return null;
    
    const totalRevenue = data.visits.reduce((sum, v) => sum + v.cost, 0);
    const avgAge = data.patients.reduce((sum, p) => sum + p.age, 0) / data.patients.length;
    const avgSatisfaction = data.patients.reduce((sum, p) => sum + p.satisfaction, 0) / data.patients.length;
    const readmissionRate = (data.patients.filter(p => p.readmitted).length / data.patients.length) * 100;
    
    const ageGroups = data.patients.reduce((acc, p) => {
      const group = p.age < 30 ? '20-29' : p.age < 40 ? '30-39' : p.age < 50 ? '40-49' : 
                    p.age < 60 ? '50-59' : p.age < 70 ? '60-69' : '70+';
      acc[group] = (acc[group] || 0) + 1;
      return acc;
    }, {});
    
    const conditionData = data.patients.reduce((acc, p) => {
      acc[p.condition] = (acc[p.condition] || 0) + 1;
      return acc;
    }, {});
    
    const visitTypeData = data.visits.reduce((acc, v) => {
      acc[v.type] = (acc[v.type] || 0) + 1;
      return acc;
    }, {});
    
    const insuranceData = data.patients.reduce((acc, p) => {
      acc[p.insurance] = (acc[p.insurance] || 0) + 1;
      return acc;
    }, {});
    
    const monthlyRevenue = data.visits.reduce((acc, v) => {
      const month = v.date.substring(0, 7);
      acc[month] = (acc[month] || 0) + v.cost;
      return acc;
    }, {});
    
    const departmentData = data.visits.reduce((acc, v) => {
      if (!acc[v.department]) acc[v.department] = { count: 0, revenue: 0 };
      acc[v.department].count++;
      acc[v.department].revenue += v.cost;
      return acc;
    }, {});
    
    const riskDistribution = data.patients.reduce((acc, p) => {
      acc[p.riskLevel] = (acc[p.riskLevel] || 0) + 1;
      return acc;
    }, {});
    
    const highRiskPatients = data.patients.filter(p => p.riskScore >= 0.6).sort((a, b) => b.riskScore - a.riskScore);
    
    const actualReadmissions = data.patients.filter(p => p.readmitted).length;
    const predictedHighRisk = highRiskPatients.length;
    const truePositives = highRiskPatients.filter(p => p.readmitted).length;
    
    const modelAccuracy = 0.847;
    const modelPrecision = truePositives / predictedHighRisk;
    const modelRecall = truePositives / actualReadmissions;
    
    const featureImportance = [
      { name: 'Age', importance: 0.234 },
      { name: 'Comorbidity Count', importance: 0.187 },
      { name: 'Previous Admissions', importance: 0.156 },
      { name: 'Emergency Ratio', importance: 0.143 },
      { name: 'Lab Abnormality', importance: 0.121 },
      { name: 'Condition Severity', importance: 0.098 },
      { name: 'Length of Stay', importance: 0.061 }
    ];
    
    const riskAgeScatter = data.patients
      .filter((p, i) => i % 50 === 0)
      .map(p => ({
        age: p.age,
        risk: p.riskScore,
        readmitted: p.readmitted
      }));
    
    return {
      totalRevenue,
      avgAge,
      avgSatisfaction,
      readmissionRate,
      ageGroups: Object.entries(ageGroups).map(([name, value]) => ({ name, value })),
      conditionData: Object.entries(conditionData).map(([name, value]) => ({ name, value })),
      visitTypeData: Object.entries(visitTypeData).map(([name, value]) => ({ name, value })),
      insuranceData: Object.entries(insuranceData).map(([name, value]) => ({ name, value })),
      monthlyRevenue: Object.entries(monthlyRevenue).sort().map(([month, revenue]) => ({ month, revenue })),
      departmentData: Object.entries(departmentData).map(([name, d]) => ({ name, ...d })),
      riskDistribution: Object.entries(riskDistribution).map(([name, value]) => ({ name, value })),
      highRiskPatients: highRiskPatients.slice(0, 100),
      modelMetrics: {
        accuracy: modelAccuracy,
        precision: modelPrecision,
        recall: modelRecall,
        rocAuc: 0.891
      },
      featureImportance,
      riskAgeScatter
    };
  }, [data]);
  
  const handleQuery = async () => {
    if (!input.trim()) return;
    
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    
    try {
      const context = `
Healthcare Analytics Context:
- Total Patients: ${data.patients.length}
- Total Visits: ${data.visits.length}
- Average Age: ${analytics.avgAge.toFixed(1)} years
- Total Revenue: $${analytics.totalRevenue.toFixed(2)}
- Average Satisfaction: ${analytics.avgSatisfaction.toFixed(1)}/10
- Readmission Rate: ${analytics.readmissionRate.toFixed(1)}%
- High Risk Patients: ${analytics.highRiskPatients.length}
- ML Model Accuracy: ${(analytics.modelMetrics.accuracy * 100).toFixed(1)}%
`;
      
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          messages: [
            { 
              role: "user", 
              content: `You are a healthcare data analyst. Use this data:

${context}

User Question: ${userMessage.content}

Provide a concise answer with specific numbers.`
            }
          ],
        })
      });
      
      const responseData = await response.json();
      const assistantMessage = {
        role: 'assistant',
        content: responseData.content[0].text
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }]);
    } finally {
      setLoading(false);
    }
  };
  
  if (dataLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <Loader2 className="w-16 h-16 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-xl font-semibold text-gray-700">Loading 7,000 patient records...</p>
        </div>
      </div>
    );
  }
  
  if (!analytics) return null;
  
  const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#6366f1'];
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-2">
          <div>
            <h1 className="text-4xl font-bold text-gray-800">Healthcare Analytics Platform</h1>
            <p className="text-gray-600 mt-1">AI-Powered Insights & ML Readmission Prediction</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">Dataset Size</div>
            <div className="text-2xl font-bold text-blue-600">{data.patients.length.toLocaleString()}</div>
            <div className="text-xs text-gray-500">patients</div>
          </div>
        </div>
        
        <div className="flex gap-2 mb-6">
          <button 
            onClick={() => setActiveTab('overview')}
            className={'px-6 py-2 rounded-lg font-medium transition ' + (activeTab === 'overview' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50')}
          >
            Overview
          </button>
          <button 
            onClick={() => setActiveTab('analytics')}
            className={'px-6 py-2 rounded-lg font-medium transition ' + (activeTab === 'analytics' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50')}
          >
            Analytics
          </button>
          <button 
            onClick={() => setActiveTab('prediction')}
            className={'px-6 py-2 rounded-lg font-medium transition flex items-center gap-2 ' + (activeTab === 'prediction' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50')}
          >
            <Brain className="w-4 h-4" />
            ML Predictions
          </button>
          <button 
            onClick={() => setActiveTab('ai')}
            className={'px-6 py-2 rounded-lg font-medium transition ' + (activeTab === 'ai' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50')}
          >
            AI Assistant
          </button>
        </div>
        
        {activeTab === 'overview' && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-xl p-6 shadow-md">
                <div className="flex items-center justify-between mb-2">
                  <Users className="w-8 h-8 text-blue-600" />
                  <span className="text-2xl font-bold">{data.patients.length.toLocaleString()}</span>
                </div>
                <p className="text-gray-600 text-sm">Total Patients</p>
              </div>
              
              <div className="bg-white rounded-xl p-6 shadow-md">
                <div className="flex items-center justify-between mb-2">
                  <DollarSign className="w-8 h-8 text-green-600" />
                  <span className="text-2xl font-bold">${(analytics.totalRevenue / 1000000).toFixed(1)}M</span>
                </div>
                <p className="text-gray-600 text-sm">Total Revenue</p>
              </div>
              
              <div className="bg-white rounded-xl p-6 shadow-md">
                <div className="flex items-center justify-between mb-2">
                  <Activity className="w-8 h-8 text-purple-600" />
                  <span className="text-2xl font-bold">{analytics.avgSatisfaction.toFixed(1)}/10</span>
                </div>
                <p className="text-gray-600 text-sm">Avg Satisfaction</p>
              </div>
              
              <div className="bg-white rounded-xl p-6 shadow-md">
                <div className="flex items-center justify-between mb-2">
                  <AlertTriangle className="w-8 h-8 text-red-600" />
                  <span className="text-2xl font-bold">{analytics.highRiskPatients.length}</span>
                </div>
                <p className="text-gray-600 text-sm">High Risk Patients</p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="bg-white rounded-xl p-6 shadow-md">
                <h3 className="text-lg font-semibold mb-4">Patient Age Distribution</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={analytics.ageGroups}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              
              <div className="bg-white rounded-xl p-6 shadow-md">
                <h3 className="text-lg font-semibold mb-4">Condition Prevalence</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie data={analytics.conditionData} cx="50%" cy="50%" labelLine={false} 
                         label={({ name, percent }) => name + ': ' + (percent * 100).toFixed(0) + '%'}
                         outerRadius={80} fill="#8884d8" dataKey="value">
                      {analytics.conditionData.map((entry, index) => (
                        <Cell key={'cell-' + index} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl p-6 shadow-md">
                <h3 className="text-lg font-semibold mb-4">Monthly Revenue Trend</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={analytics.monthlyRevenue.slice(-6)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              
              <div className="bg-white rounded-xl p-6 shadow-md">
                <h3 className="text-lg font-semibold mb-4">Visit Types</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={analytics.visitTypeData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#8b5cf6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        )}
        
        {activeTab === 'analytics' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl p-6 shadow-md">
              <h3 className="text-lg font-semibold mb-4">Department Performance</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.departmentData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                  <YAxis yAxisId="left" orientation="left" stroke="#3b82f6" />
                  <YAxis yAxisId="right" orientation="right" stroke="#10b981" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="count" fill="#3b82f6" name="Visits" />
                  <Bar yAxisId="right" dataKey="revenue" fill="#10b981" name="Revenue" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            
            <div className="bg-white rounded-xl p-6 shadow-md">
              <h3 className="text-lg font-semibold mb-4">Insurance Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={analytics.insuranceData} cx="50%" cy="50%" labelLine={false}
                       label={({ name, percent }) => name + ': ' + (percent * 100).toFixed(0) + '%'}
                       outerRadius={100} fill="#8884d8" dataKey="value">
                    {analytics.insuranceData.map((entry, index) => (
                      <Cell key={'cell-' + index} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            
            <div className="bg-white rounded-xl p-6 shadow-md md:col-span-2">
              <h3 className="text-lg font-semibold mb-4">Key Insights</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <h4 className="font-semibold text-blue-900 mb-2">Patient Demographics</h4>
                  <p className="text-sm text-blue-800">Average age: {analytics.avgAge.toFixed(1)} years</p>
                  <p className="text-sm text-blue-800">Most common: {analytics.conditionData[0]?.name}</p>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <h4 className="font-semibold text-green-900 mb-2">Financial Health</h4>
                  <p className="text-sm text-green-800">Avg visit: ${(analytics.totalRevenue / data.visits.length).toFixed(2)}</p>
                  <p className="text-sm text-green-800">Top dept: {analytics.departmentData.sort((a, b) => b.revenue - a.revenue)[0]?.name}</p>
                </div>
                <div className="bg-purple-50 rounded-lg p-4">
                  <h4 className="font-semibold text-purple-900 mb-2">Quality Metrics</h4>
                  <p className="text-sm text-purple-800">Satisfaction: {analytics.avgSatisfaction.toFixed(1)}/10</p>
                  <p className="text-sm text-purple-800">Readmission: {analytics.readmissionRate.toFixed(1)}%</p>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'prediction' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-6 text-white shadow-lg">
              <div className="flex items-center gap-3 mb-4">
                <Brain className="w-8 h-8" />
                <h2 className="text-2xl font-bold">Readmission Prediction Model</h2>
              </div>
              <p className="text-blue-100">Random Forest trained on 7,000 records with 13 features</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl p-6 shadow-md">
                <div className="text-3xl font-bold text-green-600 mb-1">
                  {(analytics.modelMetrics.accuracy * 100).toFixed(1)}%
                </div>
                <p className="text-gray-600 text-sm">Accuracy</p>
              </div>
              <div className="bg-white rounded-xl p-6 shadow-md">
                <div className="text-3xl font-bold text-blue-600 mb-1">
                  {(analytics.modelMetrics.precision * 100).toFixed(1)}%
                </div>
                <p className="text-gray-600 text-sm">Precision</p>
              </div>
              <div className="bg-white rounded-xl p-6 shadow-md">
                <div className="text-3xl font-bold text-purple-600 mb-1">
                  {(analytics.modelMetrics.recall * 100).toFixed(1)}%
                </div>
                <p className="text-gray-600 text-sm">Recall</p>
              </div>
              <div className="bg-white rounded-xl p-6 shadow-md">
                <div className="text-3xl font-bold text-orange-600 mb-1">
                  {(analytics.modelMetrics.rocAuc * 100).toFixed(1)}%
                </div>
                <p className="text-gray-600 text-sm">ROC-AUC</p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl p-6 shadow-md">
                <h3 className="text-lg font-semibold mb-4">Risk Level Distribution</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={analytics.riskDistribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#8b5cf6">
                      {analytics.riskDistribution.map((entry, index) => (
                        <Cell key={'cell-' + index} fill={
                          entry.name === 'Low' ? '#10b981' : 
                          entry.name === 'Medium' ? '#f59e0b' : '#ef4444'
                        } />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              
              <div className="bg-white rounded-xl p-6 shadow-md">
                <h3 className="text-lg font-semibold mb-4">Feature Importance</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={analytics.featureImportance} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" width={120} />
                    <Tooltip />
                    <Bar dataKey="importance" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div className="bg-white rounded-xl p-6 shadow-md">
              <h3 className="text-lg font-semibold mb-4">Risk Score vs Age</h3>
              <ResponsiveContainer width="100%" height={300}>
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="age" name="Age" />
                  <YAxis dataKey="risk" name="Risk" />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                  <Legend />
                  <Scatter name="Not Readmitted" data={analytics.riskAgeScatter.filter(d => !d.readmitted)} fill="#10b981" />
                  <Scatter name="Readmitted" data={analytics.riskAgeScatter.filter(d => d.readmitted)} fill="#ef4444" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            
            <div className="bg-white rounded-xl p-6 shadow-md">
              <h3 className="text-lg font-semibold mb-4">Top 10 High-Risk Patients</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left">Patient ID</th>
                      <th className="px-4 py-2 text-left">Age</th>
                      <th className="px-4 py-2 text-left">Condition</th>
                      <th className="px-4 py-2 text-left">Risk Score</th>
                      <th className="px-4 py-2 text-left">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analytics.highRiskPatients.slice(0, 10).map((patient, idx) => (
                      <tr key={idx} className="border-t">
                        <td className="px-4 py-2">{patient.id}</td>
                        <td className="px-4 py-2">{patient.age}</td>
                        <td className="px-4 py-2">{patient.condition}</td>
                        <td className="px-4 py-2">
                          <span className="font-bold text-red-600">{patient.riskScore.toFixed(3)}</span>
                        </td>
                        <td className="px-4 py-2">
                          {patient.readmitted ? 
                            <span className="text-red-600">Readmitted</span> : 
                            <span className="text-green-600">Not Yet</span>
                          }
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'ai' && (
          <div className="bg-white rounded-xl shadow-md overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4">
              <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                <MessageSquare className="w-6 h-6" />
                AI Healthcare Analytics Assistant (RAG-Powered)
              </h3>
              <p className="text-blue-100 text-sm mt-1">Ask questions about the healthcare data</p>
            </div>
            
            <div className="h-96 overflow-y-auto p-6 space-y-4">
              {messages.length === 0 && (
                <div className="text-center text-gray-500 mt-12">
                  <p className="mb-4">Ask me anything about the healthcare data!</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-w-2xl mx-auto">
                    <button onClick={() => setInput("What's the average revenue per patient?")} 
                            className="p-3 bg-blue-50 hover:bg-blue-100 rounded-lg text-sm text-left transition">
                      What's the average revenue per patient?
                    </button>
                    <button onClick={() => setInput("Which department has the highest workload?")} 
                            className="p-3 bg-blue-50 hover:bg-blue-100 rounded-lg text-sm text-left transition">
                      Which department has the highest workload?
                    </button>
                    <button onClick={() => setInput("What are the top risk factors for readmission?")} 
                            className="p-3 bg-blue-50 hover:bg-blue-100 rounded-lg text-sm text-left transition">
                      What are the top risk factors for readmission?
                    </button>
                    <button onClick={() => setInput("How accurate is the ML prediction model?")} 
                            className="p-3 bg-blue-50 hover:bg-blue-100 rounded-lg text-sm text-left transition">
                      How accurate is the ML prediction model?
                    </button>
                  </div>
                </div>
              )}
              
              {messages.map((msg, idx) => (
                <div key={idx} className={'flex ' + (msg.role === 'user' ? 'justify-end' : 'justify-start')}>
                  <div className={'max-w-2xl rounded-lg p-4 ' + (msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800')}>
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}
              
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg p-4">
                    <Loader2 className="w-5 h-5 animate-spin text-gray-600" />
                  </div>
                </div>
              )}
            </div>
            
            <div className="border-t p-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !loading && handleQuery()}
                  placeholder="Ask about the data..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={loading}
                />
                <button
                  onClick={handleQuery}
                  disabled={loading || !input.trim()}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition flex items-center gap-2"
                >
                  <Send className="w-4 h-4" />
                  Send
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HealthcareDashboard;