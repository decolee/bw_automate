import React from 'react';
import { motion } from 'framer-motion';
import {
  Play,
  Pause,
  Menu,
  Search,
  Bell,
  User,
  ChevronDown,
  FileText,
  Zap,
  Clock
} from 'lucide-react';

const Header = ({
  currentProject,
  selectedFiles = [],
  isAnalyzing,
  analysisProgress,
  onStartAnalysis,
  onToggleSidebar
}) => {
  const projectName = currentProject ? currentProject.split('/').pop() : null;
  const pythonFiles = selectedFiles.filter(f => f.endsWith('.py'));

  return (
    <header className="bg-white/80 backdrop-blur-xl border-b border-gray-200 sticky top-0 z-20">
      <div className="section-padding">
        <div className="flex items-center justify-between">
          {/* Left side */}
          <div className="flex items-center space-x-4">
            <button
              onClick={onToggleSidebar}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors lg:hidden"
              title="Toggle Sidebar"
            >
              <Menu size={20} className="text-gray-600" />
            </button>

            {/* Project info */}
            <div className="flex items-center space-x-3">
              {projectName ? (
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    {projectName}
                  </h2>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span className="flex items-center space-x-1">
                      <FileText size={14} />
                      <span>{pythonFiles.length} Python files</span>
                    </span>
                    {selectedFiles.length > 0 && (
                      <span className="flex items-center space-x-1">
                        <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                        <span>{selectedFiles.length} selected</span>
                      </span>
                    )}
                  </div>
                </div>
              ) : (
                <div>
                  <h2 className="text-lg font-semibold text-gray-400">
                    No Project Selected
                  </h2>
                  <p className="text-sm text-gray-500">
                    Choose a project to get started
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Center - Analysis Progress */}
          {isAnalyzing && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center space-x-3 bg-blue-50 px-4 py-2 rounded-xl border border-blue-200"
            >
              <div className="flex items-center space-x-2">
                <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-sm font-medium text-blue-900">
                  Analyzing...
                </span>
              </div>
              <div className="w-32 h-2 bg-blue-200 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-blue-600 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${analysisProgress}%` }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                />
              </div>
              <span className="text-sm font-medium text-blue-700">
                {analysisProgress}%
              </span>
            </motion.div>
          )}

          {/* Right side */}
          <div className="flex items-center space-x-3">
            {/* Quick Stats */}
            {!isAnalyzing && currentProject && selectedFiles.length > 0 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="hidden md:flex items-center space-x-4 text-sm text-gray-600 bg-gray-50 px-4 py-2 rounded-lg"
              >
                <div className="flex items-center space-x-1">
                  <Zap size={14} />
                  <span>Ready to analyze</span>
                </div>
              </motion.div>
            )}

            {/* Action buttons */}
            <div className="flex items-center space-x-2">
              {/* Start/Pause Analysis Button */}
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={onStartAnalysis}
                disabled={!currentProject || selectedFiles.length === 0 || isAnalyzing}
                className={`
                  px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2
                  ${!currentProject || selectedFiles.length === 0
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : isAnalyzing
                    ? 'bg-orange-100 text-orange-700 hover:bg-orange-200'
                    : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm hover:shadow-md'
                  }
                `}
                title={
                  !currentProject
                    ? 'Select a project first'
                    : selectedFiles.length === 0
                    ? 'Select files to analyze'
                    : isAnalyzing
                    ? 'Analysis in progress'
                    : 'Start analysis'
                }
              >
                {isAnalyzing ? (
                  <>
                    <Pause size={16} />
                    <span className="hidden sm:inline">Running</span>
                  </>
                ) : (
                  <>
                    <Play size={16} />
                    <span className="hidden sm:inline">Analyze</span>
                  </>
                )}
              </motion.button>

              {/* Search */}
              <button
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Search"
              >
                <Search size={18} className="text-gray-600" />
              </button>

              {/* Notifications */}
              <button
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors relative"
                title="Notifications"
              >
                <Bell size={18} className="text-gray-600" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>

              {/* User menu */}
              <div className="flex items-center space-x-2 hover:bg-gray-100 rounded-lg px-2 py-1 cursor-pointer transition-colors">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
                  <User size={16} className="text-white" />
                </div>
                <ChevronDown size={14} className="text-gray-600 hidden sm:block" />
              </div>
            </div>
          </div>
        </div>

        {/* Analysis Status Bar */}
        {!isAnalyzing && currentProject && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 flex items-center justify-between bg-gray-50 px-4 py-3 rounded-lg"
          >
            <div className="flex items-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="text-gray-700">Project loaded</span>
              </div>
              
              {selectedFiles.length > 0 && (
                <div className="flex items-center space-x-2">
                  <FileText size={14} className="text-blue-600" />
                  <span className="text-gray-700">
                    {selectedFiles.length} files ready for analysis
                  </span>
                </div>
              )}
              
              <div className="flex items-center space-x-2">
                <Clock size={14} className="text-gray-500" />
                <span className="text-gray-500">
                  Est. {Math.ceil(selectedFiles.length / 10)} min
                </span>
              </div>
            </div>

            {selectedFiles.length > 0 && (
              <div className="text-sm text-gray-600">
                <span className="font-medium">{pythonFiles.length}</span> Python files, 
                <span className="font-medium"> {selectedFiles.length - pythonFiles.length}</span> other files
              </div>
            )}
          </motion.div>
        )}
      </div>
    </header>
  );
};

export default Header;