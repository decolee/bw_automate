import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import './index.css';

// Components
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DirectoryBrowser from './components/DirectoryBrowser';
import AnalysisResults from './components/AnalysisResults';
import SettingsPanel from './components/SettingsPanel';
import Toast from './components/Toast';

// Pages
import Dashboard from './pages/Dashboard';
import ProjectAnalysis from './pages/ProjectAnalysis';
import Reports from './pages/Reports';
import Settings from './pages/Settings';

// Services
import { AnalysisService } from './services/analysisService';

// Hooks
import { useLocalStorage } from './hooks/useLocalStorage';

function App() {
  // State management
  const [currentProject, setCurrentProject] = useLocalStorage('currentProject', null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [theme, setTheme] = useLocalStorage('theme', 'light');

  // Analysis service
  const analysisService = new AnalysisService();

  // Toast management
  const addToast = (message, type = 'info', duration = 5000) => {
    const id = Date.now();
    const toast = { id, message, type, duration };
    setToasts(prev => [...prev, toast]);
    
    setTimeout(() => {
      removeToast(id);
    }, duration);
  };

  const removeToast = (id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  };

  // Project management
  const handleProjectSelect = (projectPath) => {
    setCurrentProject(projectPath);
    setSelectedFiles([]);
    setAnalysisResults(null);
    addToast(`Project selected: ${projectPath}`, 'success');
  };

  const handleFilesSelect = (files) => {
    setSelectedFiles(files);
    addToast(`${files.length} files selected for analysis`, 'info');
  };

  // Analysis management
  const handleStartAnalysis = async (options = {}) => {
    if (!currentProject || selectedFiles.length === 0) {
      addToast('Please select a project and files to analyze', 'warning');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisProgress(0);
    
    try {
      // Progress callback
      const onProgress = (progress) => {
        setAnalysisProgress(progress);
      };

      const results = await analysisService.analyzeProject({
        projectPath: currentProject,
        selectedFiles,
        options,
        onProgress
      });

      setAnalysisResults(results);
      addToast('Analysis completed successfully!', 'success');
      
    } catch (error) {
      console.error('Analysis failed:', error);
      addToast(`Analysis failed: ${error.message}`, 'error');
    } finally {
      setIsAnalyzing(false);
      setAnalysisProgress(0);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Cmd/Ctrl + K for quick project open
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        // Open project selector modal
      }
      
      // Cmd/Ctrl + Enter for start analysis
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        if (!isAnalyzing) {
          handleStartAnalysis();
        }
      }
      
      // Escape to collapse sidebar
      if (e.key === 'Escape') {
        setSidebarCollapsed(true);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isAnalyzing]);

  // App layout variants for animations
  const layoutVariants = {
    expanded: { marginLeft: 280 },
    collapsed: { marginLeft: 80 }
  };

  return (
    <div className={`min-h-screen bg-gray-50 ${theme}`}>
      <Router>
        {/* Sidebar */}
        <Sidebar 
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          currentProject={currentProject}
          onProjectSelect={handleProjectSelect}
        />

        {/* Main content area */}
        <motion.div 
          className="transition-all duration-300 ease-out"
          variants={layoutVariants}
          animate={sidebarCollapsed ? 'collapsed' : 'expanded'}
        >
          {/* Header */}
          <Header 
            currentProject={currentProject}
            selectedFiles={selectedFiles}
            isAnalyzing={isAnalyzing}
            analysisProgress={analysisProgress}
            onStartAnalysis={handleStartAnalysis}
            onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)}
          />

          {/* Main content */}
          <main className="section-padding">
            <AnimatePresence mode="wait">
              <Routes>
                <Route 
                  path="/" 
                  element={
                    <Dashboard 
                      currentProject={currentProject}
                      selectedFiles={selectedFiles}
                      analysisResults={analysisResults}
                      isAnalyzing={isAnalyzing}
                      onProjectSelect={handleProjectSelect}
                      onStartAnalysis={handleStartAnalysis}
                    />
                  } 
                />
                <Route 
                  path="/analysis" 
                  element={
                    <ProjectAnalysis 
                      currentProject={currentProject}
                      selectedFiles={selectedFiles}
                      onFilesSelect={handleFilesSelect}
                      analysisResults={analysisResults}
                      isAnalyzing={isAnalyzing}
                      onStartAnalysis={handleStartAnalysis}
                    />
                  } 
                />
                <Route 
                  path="/reports" 
                  element={
                    <Reports 
                      analysisResults={analysisResults}
                      currentProject={currentProject}
                    />
                  } 
                />
                <Route 
                  path="/settings" 
                  element={
                    <Settings 
                      theme={theme}
                      onThemeChange={setTheme}
                    />
                  } 
                />
              </Routes>
            </AnimatePresence>
          </main>
        </motion.div>

        {/* Toast notifications */}
        <div className="fixed top-4 right-4 z-50 space-y-2">
          <AnimatePresence>
            {toasts.map(toast => (
              <Toast 
                key={toast.id}
                message={toast.message}
                type={toast.type}
                onClose={() => removeToast(toast.id)}
              />
            ))}
          </AnimatePresence>
        </div>

        {/* Global loading overlay */}
        <AnimatePresence>
          {isAnalyzing && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm z-40 flex items-center justify-center"
            >
              <motion.div 
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-white rounded-2xl p-8 shadow-apple-xl max-w-md w-full mx-4"
              >
                <div className="text-center">
                  <div className="text-xl font-semibold text-gray-900 mb-4">
                    Analyzing Code...
                  </div>
                  <div className="progress-bar mb-4">
                    <motion.div 
                      className="progress-fill"
                      initial={{ width: 0 }}
                      animate={{ width: `${analysisProgress}%` }}
                      transition={{ duration: 0.3, ease: "easeOut" }}
                    />
                  </div>
                  <div className="text-sm text-gray-600">
                    {analysisProgress}% complete
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </Router>
    </div>
  );
}

export default App;