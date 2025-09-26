import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Folder, 
  FolderOpen, 
  File, 
  FileText, 
  Code,
  CheckSquare,
  Square,
  Search,
  Filter,
  RefreshCw,
  Upload,
  X
} from 'lucide-react';

const DirectoryBrowser = ({ 
  projectPath, 
  onFilesSelect, 
  selectedFiles = [],
  className = ""
}) => {
  const [fileTree, setFileTree] = useState([]);
  const [expandedFolders, setExpandedFolders] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all'); // all, python, config
  const [selectedFilesList, setSelectedFilesList] = useState(selectedFiles);

  // Load file tree from backend
  useEffect(() => {
    if (projectPath) {
      loadFileTree();
    }
  }, [projectPath]);

  const loadFileTree = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/files/tree', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: projectPath })
      });
      
      const data = await response.json();
      if (data.success) {
        setFileTree(data.tree);
        // Auto-expand first level
        const firstLevelFolders = data.tree
          .filter(item => item.type === 'folder')
          .map(item => item.path);
        setExpandedFolders(new Set(firstLevelFolders));
      }
    } catch (error) {
      console.error('Failed to load file tree:', error);
    } finally {
      setLoading(false);
    }
  };

  // Toggle folder expansion
  const toggleFolder = (folderPath) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(folderPath)) {
      newExpanded.delete(folderPath);
    } else {
      newExpanded.add(folderPath);
    }
    setExpandedFolders(newExpanded);
  };

  // Toggle file selection
  const toggleFileSelection = (filePath) => {
    const newSelected = [...selectedFilesList];
    const index = newSelected.indexOf(filePath);
    
    if (index > -1) {
      newSelected.splice(index, 1);
    } else {
      newSelected.push(filePath);
    }
    
    setSelectedFilesList(newSelected);
    onFilesSelect(newSelected);
  };

  // Select all Python files
  const selectAllPythonFiles = () => {
    const pythonFiles = getAllPythonFiles(fileTree);
    setSelectedFilesList(pythonFiles);
    onFilesSelect(pythonFiles);
  };

  // Clear all selections
  const clearAllSelections = () => {
    setSelectedFilesList([]);
    onFilesSelect([]);
  };

  // Get all Python files recursively
  const getAllPythonFiles = (tree) => {
    const pythonFiles = [];
    
    const traverse = (items) => {
      for (const item of items) {
        if (item.type === 'file' && item.name.endsWith('.py')) {
          pythonFiles.push(item.path);
        } else if (item.type === 'folder' && item.children) {
          traverse(item.children);
        }
      }
    };
    
    traverse(tree);
    return pythonFiles;
  };

  // Filter files based on search and filter type
  const filterTree = (tree) => {
    if (!searchTerm && filterType === 'all') return tree;
    
    const filtered = [];
    
    const filterItem = (item) => {
      if (item.type === 'file') {
        const matchesSearch = !searchTerm || 
          item.name.toLowerCase().includes(searchTerm.toLowerCase());
        
        const matchesFilter = 
          filterType === 'all' ||
          (filterType === 'python' && item.name.endsWith('.py')) ||
          (filterType === 'config' && /\.(json|yaml|yml|toml|cfg|ini)$/.test(item.name));
        
        return matchesSearch && matchesFilter;
      }
      
      if (item.type === 'folder') {
        const filteredChildren = item.children ? 
          item.children.map(filterItem).filter(Boolean) : [];
        
        if (filteredChildren.length > 0) {
          return { ...item, children: filteredChildren };
        }
        
        return null;
      }
      
      return null;
    };
    
    for (const item of tree) {
      const filteredItem = filterItem(item);
      if (filteredItem) {
        filtered.push(filteredItem);
      }
    }
    
    return filtered;
  };

  // Get file icon
  const getFileIcon = (fileName) => {
    if (fileName.endsWith('.py')) return Code;
    if (/\.(json|yaml|yml|toml|cfg|ini)$/.test(fileName)) return FileText;
    return File;
  };

  // Render file tree item
  const renderTreeItem = (item, depth = 0) => {
    const isSelected = selectedFilesList.includes(item.path);
    const isExpanded = expandedFolders.has(item.path);
    const Icon = item.type === 'folder' 
      ? (isExpanded ? FolderOpen : Folder)
      : getFileIcon(item.name);

    return (
      <motion.div
        key={item.path}
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.2 }}
      >
        <div
          className={`file-tree-item ${isSelected ? 'selected' : ''}`}
          style={{ paddingLeft: `${depth * 20 + 12}px` }}
          onClick={() => {
            if (item.type === 'folder') {
              toggleFolder(item.path);
            } else {
              toggleFileSelection(item.path);
            }
          }}
        >
          <Icon size={16} className="text-gray-500 flex-shrink-0" />
          <span className="flex-1 truncate">{item.name}</span>
          
          {item.type === 'file' && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="flex-shrink-0"
            >
              {isSelected ? (
                <CheckSquare size={16} className="text-blue-600" />
              ) : (
                <Square size={16} className="text-gray-400" />
              )}
            </motion.div>
          )}
          
          {item.type === 'folder' && item.children && (
            <span className="text-xs text-gray-400 flex-shrink-0">
              {item.children.length}
            </span>
          )}
        </div>
        
        {/* Render children if folder is expanded */}
        <AnimatePresence>
          {item.type === 'folder' && isExpanded && item.children && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: 'easeInOut' }}
              className="overflow-hidden"
            >
              {item.children.map(child => renderTreeItem(child, depth + 1))}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    );
  };

  const filteredTree = filterTree(fileTree);

  if (!projectPath) {
    return (
      <div className={`card p-8 text-center ${className}`}>
        <Upload size={48} className="mx-auto text-gray-400 mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          No Project Selected
        </h3>
        <p className="text-gray-600 mb-4">
          Select a project folder to browse and analyze Python files
        </p>
      </div>
    );
  }

  return (
    <div className={`card ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Project Files
          </h3>
          <button
            onClick={loadFileTree}
            disabled={loading}
            className="btn-ghost p-2"
            title="Refresh"
          >
            <RefreshCw 
              size={16} 
              className={loading ? 'animate-spin' : ''} 
            />
          </button>
        </div>

        {/* Search */}
        <div className="relative mb-3">
          <Search size={16} className="absolute left-3 top-3 text-gray-400" />
          <input
            type="text"
            placeholder="Search files..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pl-10 text-sm"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
            >
              <X size={16} />
            </button>
          )}
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-2 mb-4">
          <Filter size={16} className="text-gray-400" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-2 py-1 bg-white"
          >
            <option value="all">All Files</option>
            <option value="python">Python Files</option>
            <option value="config">Config Files</option>
          </select>
        </div>

        {/* Selection actions */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">
            {selectedFilesList.length} files selected
          </span>
          <div className="flex space-x-2">
            <button
              onClick={selectAllPythonFiles}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Select All .py
            </button>
            <span className="text-gray-300">|</span>
            <button
              onClick={clearAllSelections}
              className="text-gray-600 hover:text-gray-700 font-medium"
            >
              Clear All
            </button>
          </div>
        </div>
      </div>

      {/* File tree */}
      <div className="p-2 max-h-96 overflow-y-auto file-tree">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw size={24} className="animate-spin text-gray-400" />
            <span className="ml-2 text-gray-600">Loading files...</span>
          </div>
        ) : filteredTree.length > 0 ? (
          <AnimatePresence>
            {filteredTree.map(item => renderTreeItem(item))}
          </AnimatePresence>
        ) : (
          <div className="text-center py-8 text-gray-500">
            {searchTerm || filterType !== 'all' 
              ? 'No files match your criteria' 
              : 'No files found'
            }
          </div>
        )}
      </div>

      {/* Footer info */}
      {filteredTree.length > 0 && (
        <div className="p-3 border-t border-gray-100 bg-gray-50 rounded-b-2xl">
          <div className="text-xs text-gray-500 flex justify-between">
            <span>{filteredTree.length} items shown</span>
            <span>
              {selectedFilesList.filter(f => f.endsWith('.py')).length} Python files selected
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default DirectoryBrowser;