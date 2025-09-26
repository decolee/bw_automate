/**
 * Analysis Service - Clean API integration for BW_AUTOMATE backend
 * Apple-inspired service architecture with error handling
 */

class AnalysisService {
  constructor() {
    this.baseURL = process.env.NODE_ENV === 'production' 
      ? '/api' 
      : 'http://localhost:8000/api';
    
    this.activeTasks = new Map();
  }

  /**
   * Perform HTTP request with error handling
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    };

    try {
      const response = await fetch(url, { ...defaultOptions, ...options });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  /**
   * Health check
   */
  async healthCheck() {
    return this.request('/health');
  }

  /**
   * Get analyzer information and capabilities
   */
  async getAnalyzerInfo() {
    return this.request('/analyzer/info');
  }

  /**
   * Get file tree for a directory
   */
  async getFileTree(projectPath) {
    return this.request('/files/tree', {
      method: 'POST',
      body: JSON.stringify({ path: projectPath })
    });
  }

  /**
   * Open native folder selection dialog
   */
  async selectFolder() {
    return this.request('/files/select-folder', {
      method: 'POST'
    });
  }

  /**
   * Start code analysis
   */
  async startAnalysis({ projectPath, selectedFiles, options = {}, onProgress }) {
    try {
      // Start analysis
      const startResponse = await this.request('/analysis/start', {
        method: 'POST',
        body: JSON.stringify({
          projectPath,
          selectedFiles,
          options
        })
      });

      if (!startResponse.success) {
        throw new Error(startResponse.error || 'Failed to start analysis');
      }

      const taskId = startResponse.taskId;
      this.activeTasks.set(taskId, { onProgress, status: 'running' });

      // Poll for progress
      return new Promise((resolve, reject) => {
        const pollProgress = async () => {
          try {
            const progressResponse = await this.request(`/analysis/progress/${taskId}`);
            
            if (!progressResponse.success) {
              reject(new Error(progressResponse.error || 'Failed to get progress'));
              return;
            }

            const { status, progress, result, error } = progressResponse;

            // Update progress callback
            if (onProgress && typeof progress === 'number') {
              onProgress(progress);
            }

            // Check status
            if (status === 'completed') {
              this.activeTasks.delete(taskId);
              resolve(result || {});
              return;
            }

            if (status === 'error') {
              this.activeTasks.delete(taskId);
              reject(new Error(error || 'Analysis failed'));
              return;
            }

            // Continue polling if still running
            if (status === 'running' || status === 'pending') {
              setTimeout(pollProgress, 1000); // Poll every second
            }

          } catch (error) {
            this.activeTasks.delete(taskId);
            reject(error);
          }
        };

        // Start polling
        pollProgress();
      });

    } catch (error) {
      console.error('Analysis failed:', error);
      throw error;
    }
  }

  /**
   * Get analysis results
   */
  async getAnalysisResults(taskId) {
    return this.request(`/analysis/results/${taskId}`);
  }

  /**
   * Download analysis results
   */
  async downloadResults(taskId) {
    const url = `${this.baseURL}/download/results/${taskId}`;
    window.open(url, '_blank');
  }

  /**
   * Get recent projects
   */
  async getRecentProjects() {
    return this.request('/projects/recent');
  }

  /**
   * Cancel active analysis
   */
  cancelAnalysis(taskId) {
    if (this.activeTasks.has(taskId)) {
      this.activeTasks.delete(taskId);
      // Note: Backend doesn't support cancellation yet
      // This is a client-side cleanup
    }
  }

  /**
   * Validate project directory
   */
  async validateProject(projectPath) {
    try {
      const response = await this.getFileTree(projectPath);
      
      if (!response.success) {
        return {
          valid: false,
          error: response.error || 'Invalid project directory'
        };
      }

      const tree = response.tree || [];
      const pythonFiles = this.countPythonFiles(tree);

      return {
        valid: true,
        pythonFiles,
        totalFiles: this.countAllFiles(tree),
        hasRequirements: this.hasFile(tree, ['requirements.txt', 'pyproject.toml', 'setup.py']),
        hasTests: this.hasDirectory(tree, ['tests', 'test'])
      };

    } catch (error) {
      return {
        valid: false,
        error: error.message
      };
    }
  }

  /**
   * Count Python files in tree
   */
  countPythonFiles(tree) {
    let count = 0;
    
    const traverse = (items) => {
      for (const item of items) {
        if (item.type === 'file' && item.name.endsWith('.py')) {
          count++;
        } else if (item.type === 'folder' && item.children) {
          traverse(item.children);
        }
      }
    };
    
    traverse(tree);
    return count;
  }

  /**
   * Count all files in tree
   */
  countAllFiles(tree) {
    let count = 0;
    
    const traverse = (items) => {
      for (const item of items) {
        if (item.type === 'file') {
          count++;
        } else if (item.type === 'folder' && item.children) {
          traverse(item.children);
        }
      }
    };
    
    traverse(tree);
    return count;
  }

  /**
   * Check if tree has specific file
   */
  hasFile(tree, fileNames) {
    const traverse = (items) => {
      for (const item of items) {
        if (item.type === 'file' && fileNames.includes(item.name)) {
          return true;
        } else if (item.type === 'folder' && item.children) {
          if (traverse(item.children)) {
            return true;
          }
        }
      }
      return false;
    };
    
    return traverse(tree);
  }

  /**
   * Check if tree has specific directory
   */
  hasDirectory(tree, dirNames) {
    const traverse = (items) => {
      for (const item of items) {
        if (item.type === 'folder' && dirNames.includes(item.name)) {
          return true;
        } else if (item.type === 'folder' && item.children) {
          if (traverse(item.children)) {
            return true;
          }
        }
      }
      return false;
    };
    
    return traverse(tree);
  }

  /**
   * Get analysis scope options
   */
  getAnalysisScopes() {
    return [
      {
        value: 'basic',
        label: 'Basic Analysis',
        description: 'Core Python syntax and structure analysis',
        estimatedTime: '< 1 min',
        features: ['AST Parsing', 'Basic Metrics', 'Syntax Validation']
      },
      {
        value: 'advanced',
        label: 'Advanced Features',
        description: 'Modern Python features and advanced patterns',
        estimatedTime: '1-2 min',
        features: ['Type Hints', 'Async/Await', 'Pattern Matching', 'Decorators']
      },
      {
        value: 'sql',
        label: 'SQL & Database',
        description: 'Database operations and SQL analysis',
        estimatedTime: '2-3 min',
        features: ['SQL Detection', 'ORM Analysis', 'Database Mapping', 'Query Optimization']
      },
      {
        value: 'complete',
        label: 'Complete Analysis',
        description: 'Comprehensive code analysis with all features',
        estimatedTime: '3-5 min',
        features: ['All Basic & Advanced', 'SQL Analysis', 'Performance Metrics', 'Quality Score']
      },
      {
        value: 'enterprise',
        label: 'Enterprise Suite',
        description: 'Full enterprise analysis with security and compliance',
        estimatedTime: '5-10 min',
        features: ['Complete Analysis', 'Security Scanning', 'Compliance Check', 'Detailed Reports']
      }
    ];
  }
}

export { AnalysisService };