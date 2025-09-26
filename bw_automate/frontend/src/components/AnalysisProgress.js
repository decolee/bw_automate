import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const AnalysisProgress = ({ 
  isAnalyzing, 
  progress, 
  currentFile, 
  totalFiles, 
  processedFiles,
  onCancel 
}) => {
  const [currentFileShort, setCurrentFileShort] = useState('');
  const [logs, setLogs] = useState([]);
  const [metrics, setMetrics] = useState({
    analysisSpeed: 0,
    estimatedTimeRemaining: 0,
    cacheHitRate: 0
  });

  useEffect(() => {
    if (currentFile) {
      // Shorten the file path for display
      const parts = currentFile.split('/');
      const shortPath = parts.length > 3 
        ? `.../${parts.slice(-3).join('/')}`
        : currentFile;
      setCurrentFileShort(shortPath);
      
      // Add to logs
      setLogs(prev => [
        ...prev.slice(-4), // Keep only last 5 logs
        {
          id: Date.now(),
          message: `Analyzing: ${shortPath}`,
          timestamp: new Date().toLocaleTimeString(),
          type: 'info'
        }
      ]);
    }
  }, [currentFile]);

  useEffect(() => {
    if (processedFiles > 0 && totalFiles > 0) {
      // Calculate metrics
      const progressPercent = (processedFiles / totalFiles) * 100;
      const speed = processedFiles / ((Date.now() - startTime) / 1000);
      const remaining = (totalFiles - processedFiles) / speed;
      
      setMetrics({
        analysisSpeed: speed.toFixed(1),
        estimatedTimeRemaining: Math.ceil(remaining),
        cacheHitRate: 85 // This would come from actual cache stats
      });
    }
  }, [processedFiles, totalFiles]);

  const [startTime] = useState(Date.now());

  if (!isAnalyzing) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <motion.div
        initial={{ scale: 0.9 }}
        animate={{ scale: 1 }}
        className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full mx-4"
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                className="w-4 h-4 border-2 border-white border-t-transparent rounded-full"
              />
            </div>
            <h3 className="text-xl font-semibold text-gray-900">
              Analyzing Codebase
            </h3>
          </div>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>{processedFiles} of {totalFiles} files</span>
            <span>{progress.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            />
          </div>
        </div>

        {/* Current File */}
        <div className="mb-6">
          <p className="text-sm text-gray-500 mb-1">Currently analyzing:</p>
          <motion.p
            key={currentFileShort}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-gray-900 font-mono text-sm bg-gray-50 p-2 rounded truncate"
          >
            {currentFileShort || 'Preparing analysis...'}
          </motion.p>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {metrics.analysisSpeed}
            </div>
            <div className="text-xs text-gray-500">files/sec</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {metrics.estimatedTimeRemaining}s
            </div>
            <div className="text-xs text-gray-500">remaining</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {metrics.cacheHitRate}%
            </div>
            <div className="text-xs text-gray-500">cache hits</div>
          </div>
        </div>

        {/* Recent Activity Log */}
        <div className="border-t pt-4">
          <p className="text-sm text-gray-500 mb-2">Recent activity:</p>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            <AnimatePresence>
              {logs.map((log) => (
                <motion.div
                  key={log.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="flex justify-between text-xs"
                >
                  <span className="text-gray-600 truncate flex-1 mr-2">
                    {log.message}
                  </span>
                  <span className="text-gray-400 font-mono">
                    {log.timestamp}
                  </span>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>

        {/* Status Indicators */}
        <div className="flex items-center justify-between mt-6 pt-4 border-t">
          <div className="flex items-center space-x-4 text-xs text-gray-500">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span>Analysis Engine</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
              <span>Cache System</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse"></div>
              <span>Pattern Detection</span>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
          >
            Cancel
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default AnalysisProgress;