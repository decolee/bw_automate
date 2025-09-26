import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  FolderOpen,
  Code2,
  BarChart3,
  Shield,
  Zap,
  Target,
  FileText,
  Clock,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  Play,
  Upload
} from 'lucide-react';

const Dashboard = ({
  currentProject,
  selectedFiles,
  analysisResults,
  isAnalyzing,
  onProjectSelect,
  onStartAnalysis
}) => {
  // Quick stats
  const pythonFiles = selectedFiles?.filter(f => f.endsWith('.py')) || [];
  const hasResults = analysisResults && Object.keys(analysisResults).length > 0;

  // Feature cards data
  const featureCards = [
    {
      icon: Code2,
      title: 'Complete Python Analysis',
      description: '100% code coverage with AST, token, and bytecode analysis',
      gradient: 'from-blue-500 to-cyan-500',
      features: ['AST Parsing', 'Token Analysis', 'Bytecode Inspection', 'Dynamic Analysis']
    },
    {
      icon: Zap,
      title: 'Advanced Features',
      description: 'Modern Python syntax detection (3.6-3.12+)',
      gradient: 'from-purple-500 to-pink-500',
      features: ['Type Hints', 'Pattern Matching', 'Async/Await', 'Walrus Operator']
    },
    {
      icon: Shield,
      title: 'Security Analysis',
      description: 'Comprehensive vulnerability and risk assessment',
      gradient: 'from-red-500 to-orange-500',
      features: ['SQL Injection', 'Hardcoded Secrets', 'Insecure Functions', 'File Access']
    },
    {
      icon: Target,
      title: 'Performance Insights',
      description: 'Optimization suggestions and complexity metrics',
      gradient: 'from-green-500 to-emerald-500',
      features: ['Complexity Analysis', 'Memory Usage', 'CPU Optimization', 'Code Quality']
    }
  ];

  // Recent analysis summary (if available)
  const getAnalysisSummary = () => {
    if (!hasResults) return null;

    return {
      totalFiles: analysisResults.total_files_analyzed || 0,
      qualityScore: analysisResults.overall_quality_score || 0,
      securityScore: analysisResults.security_score || 0,
      performanceScore: analysisResults.performance_score || 0,
      recommendations: analysisResults.recommendations?.length || 0
    };
  };

  const summary = getAnalysisSummary();

  return (
    <div className="container-max">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        {/* Hero Section */}
        <div className="text-center mb-12">
          <motion.h1
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-4xl md:text-5xl font-bold text-gray-900 mb-4"
          >
            Professional Python 
            <span className="text-gradient ml-3">Code Analysis</span>
          </motion.h1>
          
          <motion.p
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-xl text-gray-600 max-w-3xl mx-auto mb-8"
          >
            Enterprise-grade code analysis with 100% Python coverage, 
            security scanning, and performance optimization insights.
          </motion.p>

          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-4"
          >
            {!currentProject ? (
              <button
                onClick={onProjectSelect}
                className="btn-primary flex items-center space-x-2 text-lg px-8 py-4"
              >
                <FolderOpen size={20} />
                <span>Select Project</span>
              </button>
            ) : selectedFiles?.length > 0 ? (
              <button
                onClick={onStartAnalysis}
                disabled={isAnalyzing}
                className="btn-primary flex items-center space-x-2 text-lg px-8 py-4"
              >
                <Play size={20} />
                <span>{isAnalyzing ? 'Analyzing...' : 'Start Analysis'}</span>
              </button>
            ) : (
              <Link
                to="/analysis"
                className="btn-primary flex items-center space-x-2 text-lg px-8 py-4"
              >
                <FileText size={20} />
                <span>Select Files</span>
              </Link>
            )}

            <Link
              to="/reports"
              className="btn-secondary flex items-center space-x-2 text-lg px-8 py-4"
            >
              <BarChart3 size={20} />
              <span>View Reports</span>
            </Link>
          </motion.div>
        </div>

        {/* Current Project Status */}
        {currentProject && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
            className="card p-6 mb-12 bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center">
                  <FolderOpen size={24} className="text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {currentProject.split('/').pop()}
                  </h3>
                  <p className="text-gray-600 text-sm">
                    {currentProject}
                  </p>
                  <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                    <span>{pythonFiles.length} Python files selected</span>
                    {selectedFiles?.length > pythonFiles.length && (
                      <span>• {selectedFiles.length - pythonFiles.length} other files</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                {hasResults && (
                  <div className="text-right mr-4">
                    <div className="text-sm text-gray-600">Last Analysis</div>
                    <div className="text-lg font-semibold text-green-600">
                      {summary.qualityScore.toFixed(1)}/100
                    </div>
                  </div>
                )}
                
                <Link
                  to="/analysis"
                  className="btn-primary flex items-center space-x-2"
                >
                  <span>Configure Analysis</span>
                  <ArrowRight size={16} />
                </Link>
              </div>
            </div>
          </motion.div>
        )}

        {/* Analysis Results Summary */}
        {hasResults && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="mb-12"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              Latest Analysis Results
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
              <div className="card p-6 text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <FileText size={24} className="text-blue-600" />
                </div>
                <div className="text-2xl font-bold text-gray-900">{summary.totalFiles}</div>
                <div className="text-sm text-gray-600">Files Analyzed</div>
              </div>

              <div className="card p-6 text-center">
                <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <CheckCircle size={24} className="text-green-600" />
                </div>
                <div className="text-2xl font-bold text-gray-900">{summary.qualityScore.toFixed(1)}</div>
                <div className="text-sm text-gray-600">Quality Score</div>
              </div>

              <div className="card p-6 text-center">
                <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <Shield size={24} className="text-red-600" />
                </div>
                <div className="text-2xl font-bold text-gray-900">{summary.securityScore.toFixed(1)}</div>
                <div className="text-sm text-gray-600">Security Score</div>
              </div>

              <div className="card p-6 text-center">
                <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <AlertTriangle size={24} className="text-orange-600" />
                </div>
                <div className="text-2xl font-bold text-gray-900">{summary.recommendations}</div>
                <div className="text-sm text-gray-600">Recommendations</div>
              </div>
            </div>

            <div className="flex justify-center">
              <Link
                to="/reports"
                className="btn-primary flex items-center space-x-2"
              >
                <BarChart3 size={16} />
                <span>View Detailed Reports</span>
                <ArrowRight size={16} />
              </Link>
            </div>
          </motion.div>
        )}

        {/* Feature Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="mb-12"
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            Comprehensive Analysis Features
          </h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {featureCards.map((card, index) => {
              const Icon = card.icon;
              return (
                <motion.div
                  key={card.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.8 + index * 0.1 }}
                  className="card card-hover p-8 relative overflow-hidden"
                >
                  {/* Background gradient */}
                  <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${card.gradient} opacity-10 rounded-full -mr-16 -mt-16`} />
                  
                  <div className="relative">
                    <div className={`w-16 h-16 bg-gradient-to-br ${card.gradient} rounded-2xl flex items-center justify-center mb-6`}>
                      <Icon size={32} className="text-white" />
                    </div>
                    
                    <h3 className="text-xl font-bold text-gray-900 mb-3">
                      {card.title}
                    </h3>
                    
                    <p className="text-gray-600 mb-6">
                      {card.description}
                    </p>
                    
                    <div className="space-y-2">
                      {card.features.map((feature, featureIndex) => (
                        <div key={featureIndex} className="flex items-center space-x-2">
                          <CheckCircle size={16} className="text-green-500 flex-shrink-0" />
                          <span className="text-sm text-gray-700">{feature}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        {/* Getting Started */}
        {!currentProject && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
            className="card p-8 text-center bg-gradient-to-br from-gray-50 to-gray-100"
          >
            <Upload size={48} className="mx-auto text-gray-400 mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-3">
              Ready to Get Started?
            </h3>
            <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
              Select your Python project folder to begin comprehensive code analysis. 
              Our advanced analyzers will scan your entire codebase and provide 
              detailed insights on code quality, security, and performance.
            </p>
            <button
              onClick={onProjectSelect}
              className="btn-primary flex items-center space-x-2 mx-auto"
            >
              <FolderOpen size={20} />
              <span>Select Your Project</span>
            </button>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
};

export default Dashboard;