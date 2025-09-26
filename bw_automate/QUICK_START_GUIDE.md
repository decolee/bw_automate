# 🚀 BW_AUTOMATE Quick Start Guide

**Professional Python Code Analysis Platform with Apple-Inspired Interface**

## ⚡ Quick Launch (30 seconds)

```bash
# 1. Clone the repository
git clone https://github.com/decolee/bw_automate.git
cd bw_automate

# 2. Launch with beautiful installer
python run_server.py --install-deps

# 3. Open your browser
# Server will start at: http://127.0.0.1:8000
```

## 🎯 Using the Interface

### 1. **Select Your Project**
- Click **"Select Project"** in the sidebar
- Choose any Python project folder
- The interface will automatically scan and display your files

### 2. **Browse & Select Files**
- Navigate through your project using the **file tree**
- **Search** for specific files or use **filters**
- **Multi-select** files by clicking the checkboxes
- Use **"Select All .py"** for quick Python file selection

### 3. **Configure Analysis**
- Choose analysis scope:
  - **Basic**: Quick syntax and structure analysis
  - **Advanced**: Modern Python features detection
  - **Complete**: Comprehensive analysis with all features
  - **Enterprise**: Full security and compliance scanning

### 4. **Run Analysis**
- Click **"Analyze"** button in the header
- Watch **real-time progress** with beautiful animations
- Get **estimated completion time**

### 5. **View Results**
- **Dashboard**: Overview with quality scores
- **Reports**: Detailed analysis results
- **Export**: Download results as JSON

## 🏗️ Directory Structure

```
your_project/           ← Select this folder
├── src/
│   ├── main.py        ← These will be detected
│   ├── utils.py       ← and available for analysis
│   └── models/
├── tests/
├── requirements.txt   ← Configuration files detected
└── README.md
```

## 🎨 Key Features

### **Apple-Inspired Interface**
- **Clean Design**: Minimalist, professional interface
- **Smooth Animations**: Framer Motion powered transitions
- **Responsive**: Works on desktop, tablet, and mobile
- **Dark/Light Mode**: Automatic system preference detection

### **Smart File Management**
- **Tree View**: Hierarchical file exploration
- **Smart Filtering**: Python files, config files, or all files
- **Search**: Real-time file search with highlighting
- **Bulk Actions**: Select all Python files with one click

### **Real-Time Analysis**
- **Progress Tracking**: Live progress bar with percentage
- **Background Processing**: Non-blocking analysis execution
- **Status Updates**: Real-time feedback and notifications
- **Cancellation**: Stop analysis anytime (if needed)

### **Comprehensive Results**
- **Quality Score**: Overall code quality rating (0-100)
- **Security Analysis**: Vulnerability detection and scoring
- **Performance Insights**: Optimization recommendations
- **Compatibility**: Python version requirements

## 📊 Analysis Scopes Explained

| Scope | Time | Features |
|-------|------|----------|
| **Basic** | < 1 min | AST parsing, syntax validation, basic metrics |
| **Advanced** | 1-2 min | Type hints, async/await, modern Python features |
| **SQL** | 2-3 min | Database operations, SQL analysis, ORM detection |
| **Complete** | 3-5 min | All above + performance metrics, quality scoring |
| **Enterprise** | 5-10 min | Complete + security scanning, compliance checks |

## 🛠️ Installation Options

### **Option 1: Automatic (Recommended)**
```bash
python run_server.py --install-deps
```

### **Option 2: Manual Setup**
```bash
# Install Python dependencies
pip install flask flask-cors pathlib

# Install Node.js dependencies (for frontend)
cd frontend
npm install
npm run build
cd ..

# Start server
python backend_server.py
```

### **Option 3: Development Mode**
```bash
# Backend (Terminal 1)
python backend_server.py --debug

# Frontend (Terminal 2)
cd frontend
npm start
```

## 🔧 Configuration

### **Server Options**
```bash
python run_server.py --host 0.0.0.0 --port 8080  # Custom host/port
python run_server.py --debug                      # Debug mode
python run_server.py --build-only                 # Only build frontend
```

### **Project Directory**
The `user_projects/` folder is created to store:
- Analysis results
- Project history
- Cached data
- Exported reports

## 🎯 Best Practices

### **For Best Results**
1. **Select Representative Files**: Choose core Python files, not just tests
2. **Include Configuration**: Select `requirements.txt`, `pyproject.toml` for dependency analysis
3. **Use Appropriate Scope**: Start with "Complete" for comprehensive insights
4. **Review Recommendations**: Pay attention to security and performance suggestions

### **Performance Tips**
- **Large Projects**: Start with smaller file selections
- **Network**: Ensure stable connection for file operations
- **Resources**: Close unnecessary applications during analysis

## 🚨 Troubleshooting

### **Common Issues**

**🔴 "No files found"**
- Ensure you selected the correct project root folder
- Check that the folder contains `.py` files
- Verify folder permissions

**🔴 "Analysis failed"**
- Check that all files are readable
- Ensure no files are corrupted or binary
- Try with a smaller file selection first

**🔴 "Server not starting"**
- Check if port 8000 is available
- Run with `--port 8080` to use different port
- Ensure Python dependencies are installed

**🔴 "Frontend not loading"**
- Run `python run_server.py --build-only` to rebuild frontend
- Check browser console for errors
- Try clearing browser cache

## 📞 Support

### **Getting Help**
- **Issues**: Report bugs at [GitHub Issues](https://github.com/decolee/bw_automate/issues)
- **Documentation**: Check `README_FRONTEND.md` for detailed frontend docs
- **Logs**: Check console output for detailed error messages

### **Feature Requests**
We're constantly improving! Submit feature requests through GitHub Issues.

## 🎉 Success Indicators

**✅ Everything is working when you see:**
- Beautiful Apple-style interface loads
- Project folder selection works
- File tree displays your Python files
- Analysis runs with progress tracking
- Results display with quality scores

**🎯 You're ready to analyze enterprise Python codebases!**

---

*Built with attention to detail and inspired by the best design patterns. Enjoy analyzing your Python code with professional-grade insights!*