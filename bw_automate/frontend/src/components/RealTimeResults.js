import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const RealTimeResults = ({ analysisResults, isLive = false }) => {
  const [filteredResults, setFilteredResults] = useState([]);
  const [filterType, setFilterType] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('timestamp');
  const [stats, setStats] = useState({
    totalFiles: 0,
    securityIssues: 0,
    performanceIssues: 0,
    codeQuality: 0
  });

  useEffect(() => {
    if (analysisResults) {
      updateStats(analysisResults);
      filterAndSortResults(analysisResults);
    }
  }, [analysisResults, filterType, searchTerm, sortBy]);

  const updateStats = (results) => {
    const totalFiles = Object.keys(results).length;
    let securityIssues = 0;
    let performanceIssues = 0;
    let totalQuality = 0;

    Object.values(results).forEach(result => {
      if (result.security_issues) {
        securityIssues += result.security_issues.length;
      }
      if (result.performance_issues) {
        performanceIssues += result.performance_issues.length;
      }
      if (result.quality_score) {
        totalQuality += result.quality_score;
      }
    });

    setStats({
      totalFiles,
      securityIssues,
      performanceIssues,
      codeQuality: totalFiles > 0 ? (totalQuality / totalFiles).toFixed(1) : 0
    });
  };

  const filterAndSortResults = (results) => {
    let filtered = Object.entries(results).map(([path, result]) => ({
      path,
      ...result,
      timestamp: result.timestamp || new Date().toISOString()
    }));

    // Apply filter
    if (filterType !== 'all') {
      filtered = filtered.filter(item => {
        switch (filterType) {
          case 'security':
            return item.security_issues && item.security_issues.length > 0;
          case 'performance':
            return item.performance_issues && item.performance_issues.length > 0;
          case 'quality':
            return item.quality_score && item.quality_score < 80;
          case 'python':
            return item.path.endsWith('.py');
          default:
            return true;
        }
      });
    }

    // Apply search
    if (searchTerm) {
      filtered = filtered.filter(item =>
        item.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (item.constructs && Object.keys(item.constructs).some(construct =>
          construct.toLowerCase().includes(searchTerm.toLowerCase())
        ))
      );
    }

    // Apply sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'timestamp':
          return new Date(b.timestamp) - new Date(a.timestamp);
        case 'path':
          return a.path.localeCompare(b.path);
        case 'issues':
          const aIssues = (a.security_issues?.length || 0) + (a.performance_issues?.length || 0);
          const bIssues = (b.security_issues?.length || 0) + (b.performance_issues?.length || 0);
          return bIssues - aIssues;
        case 'quality':
          return (b.quality_score || 0) - (a.quality_score || 0);
        default:
          return 0;
      }
    });

    setFilteredResults(filtered);
  };

  const getFileIcon = (filePath) => {
    if (filePath.endsWith('.py')) return '🐍';
    if (filePath.endsWith('.js')) return '📜';
    if (filePath.endsWith('.sql')) return '🗃️';
    if (filePath.endsWith('.yaml') || filePath.endsWith('.yml')) return '⚙️';
    return '📄';
  };

  const getQualityColor = (score) => {
    if (score >= 90) return 'text-green-600 bg-green-100';
    if (score >= 70) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header with Live Indicator */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <h3 className="text-xl font-semibold text-gray-900">Analysis Results</h3>
          {isLive && (
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-500">Live</span>
            </div>
          )}
        </div>
        
        {/* Quick Stats */}
        <div className="flex items-center space-x-4 text-sm">
          <div className="text-center">
            <div className="font-bold text-blue-600">{stats.totalFiles}</div>
            <div className="text-gray-500">Files</div>
          </div>
          <div className="text-center">
            <div className="font-bold text-red-600">{stats.securityIssues}</div>
            <div className="text-gray-500">Security</div>
          </div>
          <div className="text-center">
            <div className="font-bold text-orange-600">{stats.performanceIssues}</div>
            <div className="text-gray-500">Performance</div>
          </div>
          <div className="text-center">
            <div className="font-bold text-green-600">{stats.codeQuality}</div>
            <div className="text-gray-500">Quality</div>
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        {/* Filter Buttons */}
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">Filter:</span>
          {['all', 'security', 'performance', 'quality', 'python'].map((filter) => (
            <button
              key={filter}
              onClick={() => setFilterType(filter)}
              className={`px-3 py-1 text-xs rounded-full transition-colors ${
                filterType === filter
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {filter.charAt(0).toUpperCase() + filter.slice(1)}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="flex-1 max-w-md">
          <input
            type="text"
            placeholder="Search files, constructs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Sort */}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="timestamp">Recent First</option>
          <option value="path">File Name</option>
          <option value="issues">Most Issues</option>
          <option value="quality">Quality Score</option>
        </select>
      </div>

      {/* Results List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        <AnimatePresence>
          {filteredResults.map((result, index) => (
            <motion.div
              key={result.path}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ delay: index * 0.05 }}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              {/* File Header */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{getFileIcon(result.path)}</span>
                  <span className="font-mono text-sm text-gray-800">
                    {result.path.split('/').pop()}
                  </span>
                  {result.quality_score && (
                    <span className={`px-2 py-1 text-xs rounded-full ${getQualityColor(result.quality_score)}`}>
                      {result.quality_score}%
                    </span>
                  )}
                </div>
                <span className="text-xs text-gray-400">
                  {new Date(result.timestamp).toLocaleTimeString()}
                </span>
              </div>

              {/* File Path */}
              <div className="text-xs text-gray-500 mb-3 font-mono">
                {result.path}
              </div>

              {/* Analysis Summary */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {/* Constructs */}
                {result.constructs && (
                  <div className="bg-blue-50 p-3 rounded">
                    <div className="text-xs font-semibold text-blue-800 mb-1">Constructs</div>
                    <div className="space-y-1">
                      {Object.entries(result.constructs).slice(0, 3).map(([construct, count]) => (
                        <div key={construct} className="text-xs text-blue-700">
                          {construct}: {count}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Security Issues */}
                {result.security_issues && result.security_issues.length > 0 && (
                  <div className="bg-red-50 p-3 rounded">
                    <div className="text-xs font-semibold text-red-800 mb-1">
                      Security Issues ({result.security_issues.length})
                    </div>
                    <div className="space-y-1">
                      {result.security_issues.slice(0, 2).map((issue, idx) => (
                        <div key={idx} className="text-xs text-red-700">
                          {issue.type}: Line {issue.line}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Performance Issues */}
                {result.performance_issues && result.performance_issues.length > 0 && (
                  <div className="bg-orange-50 p-3 rounded">
                    <div className="text-xs font-semibold text-orange-800 mb-1">
                      Performance Issues ({result.performance_issues.length})
                    </div>
                    <div className="space-y-1">
                      {result.performance_issues.slice(0, 2).map((issue, idx) => (
                        <div key={idx} className="text-xs text-orange-700">
                          {issue.type}: Line {issue.line}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Quick Actions */}
              <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
                <div className="flex items-center space-x-3 text-xs text-gray-500">
                  <span>Size: {result.file_size || 'N/A'}</span>
                  <span>Lines: {result.line_count || 'N/A'}</span>
                  <span>Complexity: {result.complexity_score || 'N/A'}</span>
                </div>
                <button className="text-xs text-blue-600 hover:text-blue-800 transition-colors">
                  View Details →
                </button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Empty State */}
      {filteredResults.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-lg mb-2">🔍</div>
          <div className="text-gray-500">
            {searchTerm || filterType !== 'all' 
              ? 'No results match your filters' 
              : 'No analysis results yet'
            }
          </div>
        </div>
      )}
    </div>
  );
};

export default RealTimeResults;