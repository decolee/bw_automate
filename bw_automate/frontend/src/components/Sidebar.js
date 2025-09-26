import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home,
  Search,
  BarChart3,
  Settings,
  FolderOpen,
  ChevronLeft,
  ChevronRight,
  Code2,
  Zap,
  Shield,
  Target
} from 'lucide-react';

const Sidebar = ({ 
  collapsed, 
  onToggleCollapse, 
  currentProject, 
  onProjectSelect 
}) => {
  const location = useLocation();
  const [showProjectSelector, setShowProjectSelector] = useState(false);

  // Navigation items
  const navigationItems = [
    {
      path: '/',
      icon: Home,
      label: 'Dashboard',
      badge: null
    },
    {
      path: '/analysis',
      icon: Search,
      label: 'Analysis',
      badge: currentProject ? null : '!'
    },
    {
      path: '/reports',
      icon: BarChart3,
      label: 'Reports',
      badge: null
    },
    {
      path: '/settings',
      icon: Settings,
      label: 'Settings',
      badge: null
    }
  ];

  // Feature highlights
  const features = [
    {
      icon: Code2,
      label: 'Complete Python Analysis',
      description: '100% code coverage'
    },
    {
      icon: Zap,
      label: 'Advanced Features',
      description: 'Modern Python syntax'
    },
    {
      icon: Shield,
      label: 'Security Analysis',
      description: 'Vulnerability detection'
    },
    {
      icon: Target,
      label: 'Performance Insights',
      description: 'Optimization suggestions'
    }
  ];

  // Handle project folder selection
  const handleProjectSelect = async () => {
    try {
      // Open native file dialog via backend
      const response = await fetch('/api/files/select-folder', {
        method: 'POST'
      });
      
      const data = await response.json();
      if (data.success && data.folderPath) {
        onProjectSelect(data.folderPath);
        setShowProjectSelector(false);
      }
    } catch (error) {
      console.error('Failed to select folder:', error);
    }
  };

  // Sidebar variants for animation
  const sidebarVariants = {
    expanded: {
      width: 280,
      transition: { duration: 0.3, ease: 'easeInOut' }
    },
    collapsed: {
      width: 80,
      transition: { duration: 0.3, ease: 'easeInOut' }
    }
  };

  const contentVariants = {
    expanded: { opacity: 1, scale: 1 },
    collapsed: { opacity: 0, scale: 0.8 }
  };

  return (
    <motion.div
      className="fixed left-0 top-0 h-full sidebar z-30 flex flex-col"
      variants={sidebarVariants}
      animate={collapsed ? 'collapsed' : 'expanded'}
      initial={false}
    >
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <motion.div
              variants={contentVariants}
              animate={collapsed ? 'collapsed' : 'expanded'}
              className="flex items-center space-x-3"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Code2 size={20} className="text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">BW_AUTOMATE</h1>
                <p className="text-xs text-gray-500">Python Code Analyzer</p>
              </div>
            </motion.div>
          )}
          
          <button
            onClick={onToggleCollapse}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {collapsed ? (
              <ChevronRight size={16} className="text-gray-600" />
            ) : (
              <ChevronLeft size={16} className="text-gray-600" />
            )}
          </button>
        </div>
      </div>

      {/* Project Section */}
      <div className="p-4 border-b border-gray-200">
        {!collapsed && (
          <motion.div
            variants={contentVariants}
            animate={collapsed ? 'collapsed' : 'expanded'}
          >
            <div className="mb-3">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">
                Current Project
              </h3>
              {currentProject ? (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <div className="flex items-start space-x-2">
                    <FolderOpen size={16} className="text-blue-600 mt-0.5 flex-shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-blue-900 truncate">
                        {currentProject.split('/').pop()}
                      </p>
                      <p className="text-xs text-blue-700 opacity-75 truncate">
                        {currentProject}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowProjectSelector(true)}
                    className="mt-2 text-xs text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Change Project
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleProjectSelect}
                  className="w-full bg-gray-100 hover:bg-gray-200 border-2 border-dashed border-gray-300 rounded-lg p-4 text-center transition-colors group"
                >
                  <FolderOpen size={24} className="mx-auto text-gray-400 group-hover:text-gray-600 mb-2" />
                  <p className="text-sm font-medium text-gray-600 group-hover:text-gray-800">
                    Select Project
                  </p>
                  <p className="text-xs text-gray-500">
                    Choose a Python project folder
                  </p>
                </button>
              )}
            </div>
          </motion.div>
        )}
        
        {collapsed && (
          <div className="flex justify-center">
            <button
              onClick={currentProject ? () => setShowProjectSelector(true) : handleProjectSelect}
              className="p-3 hover:bg-gray-100 rounded-lg transition-colors"
              title={currentProject ? 'Change Project' : 'Select Project'}
            >
              <FolderOpen 
                size={20} 
                className={currentProject ? 'text-blue-600' : 'text-gray-400'} 
              />
            </button>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        {!collapsed && (
          <motion.div
            variants={contentVariants}
            animate={collapsed ? 'collapsed' : 'expanded'}
            className="mb-6"
          >
            <h3 className="text-sm font-semibold text-gray-700 mb-3">
              Navigation
            </h3>
          </motion.div>
        )}
        
        <div className="space-y-2">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-all duration-200
                  ${isActive 
                    ? 'bg-blue-600 text-white shadow-sm' 
                    : 'text-gray-700 hover:bg-gray-100'
                  }
                  ${collapsed ? 'justify-center' : ''}
                `}
                title={collapsed ? item.label : ''}
              >
                <Icon size={20} className="flex-shrink-0" />
                {!collapsed && (
                  <motion.div
                    variants={contentVariants}
                    animate={collapsed ? 'collapsed' : 'expanded'}
                    className="flex items-center justify-between w-full"
                  >
                    <span className="font-medium">{item.label}</span>
                    {item.badge && (
                      <span className={`
                        text-xs px-1.5 py-0.5 rounded-full font-semibold
                        ${isActive ? 'bg-blue-500 text-blue-100' : 'bg-red-500 text-white'}
                      `}>
                        {item.badge}
                      </span>
                    )}
                  </motion.div>
                )}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Features Section */}
      {!collapsed && (
        <motion.div
          variants={contentVariants}
          animate={collapsed ? 'collapsed' : 'expanded'}
          className="p-4 border-t border-gray-200"
        >
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Key Features
          </h3>
          <div className="space-y-3">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.label}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-start space-x-3 p-2 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Icon size={14} className="text-white" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {feature.label}
                    </p>
                    <p className="text-xs text-gray-500">
                      {feature.description}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        {!collapsed ? (
          <motion.div
            variants={contentVariants}
            animate={collapsed ? 'collapsed' : 'expanded'}
            className="text-center"
          >
            <p className="text-xs text-gray-500 mb-1">
              BW_AUTOMATE v1.0
            </p>
            <p className="text-xs text-gray-400">
              Enterprise Python Analysis
            </p>
          </motion.div>
        ) : (
          <div className="flex justify-center">
            <div className="w-2 h-2 bg-green-500 rounded-full" title="Ready" />
          </div>
        )}
      </div>

      {/* Project Selector Modal */}
      <AnimatePresence>
        {showProjectSelector && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm z-50 flex items-center justify-center"
            onClick={() => setShowProjectSelector(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl p-6 shadow-apple-xl max-w-md w-full mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Select Project Folder
              </h3>
              <p className="text-gray-600 mb-6">
                Choose a folder containing your Python project files for analysis.
              </p>
              
              <div className="flex space-x-3">
                <button
                  onClick={handleProjectSelect}
                  className="btn-primary flex-1"
                >
                  Browse Folders
                </button>
                <button
                  onClick={() => setShowProjectSelector(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default Sidebar;