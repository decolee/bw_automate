#!/usr/bin/env python3
"""
🤖 REAL MACHINE LEARNING ANALYZER
Statistical analysis and trend prediction without hardcoded values
"""

import ast
import os
import sys
import json
import time
import math
import statistics
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import logging

class StatisticalTrendAnalyzer:
    """Real statistical analysis without external ML libraries"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def linear_regression(self, x_values: List[float], y_values: List[float]) -> Tuple[float, float, float]:
        """Calculate linear regression: slope, intercept, and correlation coefficient"""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0, 0.0, 0.0
        
        n = len(x_values)
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)
        
        # Calculate slope and intercept
        numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0, y_mean, 0.0
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Calculate correlation coefficient
        if n > 1:
            x_std = statistics.stdev(x_values)
            y_std = statistics.stdev(y_values)
            if x_std > 0 and y_std > 0:
                correlation = numerator / ((n - 1) * x_std * y_std)
            else:
                correlation = 0.0
        else:
            correlation = 0.0
        
        return slope, intercept, correlation
    
    def polynomial_fit(self, x_values: List[float], y_values: List[float], degree: int = 2) -> List[float]:
        """Simple polynomial fitting using least squares"""
        if len(x_values) < degree + 1:
            return [0.0] * (degree + 1)
        
        # Create Vandermonde matrix
        n = len(x_values)
        A = []
        for i in range(n):
            row = [x_values[i] ** j for j in range(degree + 1)]
            A.append(row)
        
        # Solve using normal equations (A^T * A * x = A^T * b)
        try:
            # Simple matrix operations without numpy
            AT_A = [[0.0] * (degree + 1) for _ in range(degree + 1)]
            AT_b = [0.0] * (degree + 1)
            
            # Calculate A^T * A
            for i in range(degree + 1):
                for j in range(degree + 1):
                    for k in range(n):
                        AT_A[i][j] += A[k][i] * A[k][j]
            
            # Calculate A^T * b
            for i in range(degree + 1):
                for k in range(n):
                    AT_b[i] += A[k][i] * y_values[k]
            
            # Solve using Gaussian elimination
            coefficients = self._gaussian_elimination(AT_A, AT_b)
            return coefficients
        except:
            return [0.0] * (degree + 1)
    
    def _gaussian_elimination(self, A: List[List[float]], b: List[float]) -> List[float]:
        """Solve system of linear equations using Gaussian elimination"""
        n = len(A)
        
        # Forward elimination
        for i in range(n):
            # Find pivot
            max_row = i
            for k in range(i + 1, n):
                if abs(A[k][i]) > abs(A[max_row][i]):
                    max_row = k
            
            # Swap rows
            A[i], A[max_row] = A[max_row], A[i]
            b[i], b[max_row] = b[max_row], b[i]
            
            # Make all rows below this one 0 in current column
            for k in range(i + 1, n):
                if A[i][i] != 0:
                    c = A[k][i] / A[i][i]
                    for j in range(i, n):
                        A[k][j] -= c * A[i][j]
                    b[k] -= c * b[i]
        
        # Back substitution
        x = [0.0] * n
        for i in range(n - 1, -1, -1):
            x[i] = b[i]
            for j in range(i + 1, n):
                x[i] -= A[i][j] * x[j]
            if A[i][i] != 0:
                x[i] /= A[i][i]
        
        return x
    
    def detect_outliers(self, values: List[float]) -> List[int]:
        """Detect outliers using IQR method"""
        if len(values) < 4:
            return []
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        # Calculate quartiles
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        q1 = sorted_values[q1_idx]
        q3 = sorted_values[q3_idx]
        
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Find outlier indices
        outliers = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outliers.append(i)
        
        return outliers
    
    def calculate_trend_strength(self, values: List[float]) -> Dict[str, float]:
        """Calculate trend strength and direction"""
        if len(values) < 3:
            return {'strength': 0.0, 'direction': 0.0, 'consistency': 0.0}
        
        # Calculate differences between consecutive values
        differences = [values[i+1] - values[i] for i in range(len(values)-1)]
        
        # Trend direction (positive = increasing, negative = decreasing)
        avg_difference = statistics.mean(differences)
        
        # Trend consistency (how consistent the direction is)
        if differences:
            positive_changes = sum(1 for d in differences if d > 0)
            consistency = abs(positive_changes / len(differences) - 0.5) * 2
        else:
            consistency = 0.0
        
        # Trend strength (magnitude of change relative to values)
        if values:
            avg_value = statistics.mean(values)
            if avg_value != 0:
                strength = abs(avg_difference) / abs(avg_value)
            else:
                strength = 0.0
        else:
            strength = 0.0
        
        return {
            'strength': min(1.0, strength),
            'direction': 1.0 if avg_difference > 0 else -1.0 if avg_difference < 0 else 0.0,
            'consistency': consistency
        }

class RealCodePatternAnalyzer:
    """Analyze real code patterns and complexity trends"""
    
    def __init__(self):
        self.trend_analyzer = StatisticalTrendAnalyzer()
        self.pattern_cache = {}
        
    def analyze_complexity_evolution(self, file_metrics: List[Dict]) -> Dict[str, Any]:
        """Analyze how code complexity evolves across files"""
        
        # Extract complexity metrics
        complexities = []
        file_sizes = []
        function_counts = []
        
        for metrics in file_metrics:
            if 'cyclomatic_complexity' in metrics:
                complexities.append(metrics['cyclomatic_complexity'])
                file_sizes.append(metrics.get('lines_of_code', 0))
                function_counts.append(len(metrics.get('functions', [])))
        
        if not complexities:
            return {}
        
        # Analyze trends
        file_indices = list(range(len(complexities)))
        
        # Complexity trend over files
        complexity_slope, complexity_intercept, complexity_correlation = \
            self.trend_analyzer.linear_regression(file_indices, complexities)
        
        # Size vs complexity correlation
        size_complexity_slope, _, size_complexity_correlation = \
            self.trend_analyzer.linear_regression(file_sizes, complexities)
        
        # Function count vs complexity
        func_complexity_slope, _, func_complexity_correlation = \
            self.trend_analyzer.linear_regression(function_counts, complexities)
        
        # Detect complexity outliers
        complexity_outliers = self.trend_analyzer.detect_outliers(complexities)
        
        # Calculate trend strength
        trend_strength = self.trend_analyzer.calculate_trend_strength(complexities)
        
        return {
            'complexity_trend': {
                'slope': complexity_slope,
                'correlation': complexity_correlation,
                'trend_strength': trend_strength,
                'prediction_next_5': [
                    complexity_slope * (len(complexities) + i) + complexity_intercept 
                    for i in range(1, 6)
                ]
            },
            'size_complexity_relationship': {
                'correlation': size_complexity_correlation,
                'slope': size_complexity_slope,
                'interpretation': self._interpret_correlation(size_complexity_correlation)
            },
            'function_complexity_relationship': {
                'correlation': func_complexity_correlation,
                'slope': func_complexity_slope,
                'interpretation': self._interpret_correlation(func_complexity_correlation)
            },
            'outlier_analysis': {
                'outlier_count': len(complexity_outliers),
                'outlier_indices': complexity_outliers,
                'outlier_percentage': len(complexity_outliers) / len(complexities) * 100
            },
            'statistics': {
                'mean_complexity': statistics.mean(complexities),
                'median_complexity': statistics.median(complexities),
                'std_complexity': statistics.stdev(complexities) if len(complexities) > 1 else 0,
                'max_complexity': max(complexities),
                'min_complexity': min(complexities)
            }
        }
    
    def analyze_import_patterns(self, file_metrics: List[Dict]) -> Dict[str, Any]:
        """Analyze import patterns and dependencies"""
        
        all_imports = []
        import_counts = []
        
        for metrics in file_metrics:
            imports = metrics.get('imports', [])
            all_imports.extend([imp['name'] for imp in imports])
            import_counts.append(len(imports))
        
        if not all_imports:
            return {}
        
        # Count import frequencies
        import_frequency = Counter(all_imports)
        most_common_imports = import_frequency.most_common(10)
        
        # Analyze import trends
        file_indices = list(range(len(import_counts)))
        import_slope, import_intercept, import_correlation = \
            self.trend_analyzer.linear_regression(file_indices, import_counts)
        
        # Detect import outliers
        import_outliers = self.trend_analyzer.detect_outliers(import_counts)
        
        # Calculate diversity metrics
        unique_imports = len(set(all_imports))
        total_imports = len(all_imports)
        diversity_ratio = unique_imports / total_imports if total_imports > 0 else 0
        
        return {
            'import_trend': {
                'slope': import_slope,
                'correlation': import_correlation,
                'prediction_next_5': [
                    max(0, import_slope * (len(import_counts) + i) + import_intercept)
                    for i in range(1, 6)
                ]
            },
            'most_common_imports': most_common_imports,
            'diversity_metrics': {
                'unique_imports': unique_imports,
                'total_imports': total_imports,
                'diversity_ratio': diversity_ratio,
                'reuse_ratio': 1 - diversity_ratio
            },
            'outlier_analysis': {
                'files_with_unusual_imports': len(import_outliers),
                'outlier_indices': import_outliers
            },
            'statistics': {
                'mean_imports_per_file': statistics.mean(import_counts),
                'median_imports_per_file': statistics.median(import_counts),
                'max_imports_per_file': max(import_counts) if import_counts else 0
            }
        }
    
    def analyze_function_patterns(self, file_metrics: List[Dict]) -> Dict[str, Any]:
        """Analyze function size and complexity patterns"""
        
        all_functions = []
        functions_per_file = []
        
        for metrics in file_metrics:
            functions = metrics.get('functions', [])
            all_functions.extend(functions)
            functions_per_file.append(len(functions))
        
        if not all_functions:
            return {}
        
        # Extract function metrics
        function_complexities = [f.get('complexity', 0) for f in all_functions]
        function_lengths = [f.get('lines', 0) for f in all_functions]
        function_args = [f.get('args_count', 0) for f in all_functions]
        
        # Analyze patterns
        # Complexity vs length correlation
        complexity_length_slope, _, complexity_length_correlation = \
            self.trend_analyzer.linear_regression(function_lengths, function_complexities)
        
        # Arguments vs complexity correlation
        args_complexity_slope, _, args_complexity_correlation = \
            self.trend_analyzer.linear_regression(function_args, function_complexities)
        
        # Detect function outliers
        complexity_outliers = self.trend_analyzer.detect_outliers(function_complexities)
        length_outliers = self.trend_analyzer.detect_outliers(function_lengths)
        
        # Function size distribution
        length_ranges = {
            'short': len([l for l in function_lengths if l <= 10]),
            'medium': len([l for l in function_lengths if 10 < l <= 30]),
            'long': len([l for l in function_lengths if 30 < l <= 100]),
            'very_long': len([l for l in function_lengths if l > 100])
        }
        
        return {
            'complexity_length_relationship': {
                'correlation': complexity_length_correlation,
                'slope': complexity_length_slope,
                'interpretation': self._interpret_correlation(complexity_length_correlation)
            },
            'args_complexity_relationship': {
                'correlation': args_complexity_correlation,
                'slope': args_complexity_slope,
                'interpretation': self._interpret_correlation(args_complexity_correlation)
            },
            'size_distribution': length_ranges,
            'outlier_analysis': {
                'high_complexity_functions': len(complexity_outliers),
                'long_functions': len(length_outliers)
            },
            'statistics': {
                'total_functions': len(all_functions),
                'avg_complexity': statistics.mean(function_complexities),
                'avg_length': statistics.mean(function_lengths),
                'avg_args': statistics.mean(function_args),
                'functions_per_file': statistics.mean(functions_per_file)
            }
        }
    
    def _interpret_correlation(self, correlation: float) -> str:
        """Interpret correlation coefficient"""
        abs_corr = abs(correlation)
        if abs_corr >= 0.8:
            strength = "strong"
        elif abs_corr >= 0.5:
            strength = "moderate"
        elif abs_corr >= 0.3:
            strength = "weak"
        else:
            strength = "negligible"
        
        direction = "positive" if correlation > 0 else "negative"
        return f"{strength} {direction} correlation"

class RealMLAnalyzer:
    """Production ML analyzer with real statistical computations"""
    
    def __init__(self):
        self.trend_analyzer = StatisticalTrendAnalyzer()
        self.pattern_analyzer = RealCodePatternAnalyzer()
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Setup production logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Alias for unified CLI compatibility"""
        return self.analyze_project_trends(project_path)
    
    def analyze_project_trends(self, project_path: str) -> Dict[str, Any]:
        """Comprehensive ML analysis of project trends"""
        
        start_time = time.time()
        project_path = Path(project_path)
        
        # Load existing analysis data if available
        analysis_file = project_path / "PRODUCTION_ANALYSIS_REPORT.json"
        if analysis_file.exists():
            with open(analysis_file, 'r') as f:
                analysis_data = json.load(f)
            file_metrics = analysis_data.get('file_metrics', [])
        else:
            # Run basic analysis first
            self.logger.warning("No existing analysis found, running basic analysis...")
            file_metrics = self._run_basic_analysis(project_path)
        
        if not file_metrics:
            return {'error': 'No file metrics available for analysis'}
        
        self.logger.info(f"Analyzing trends from {len(file_metrics)} files")
        
        # Complexity evolution analysis
        complexity_analysis = self.pattern_analyzer.analyze_complexity_evolution(file_metrics)
        
        # Import pattern analysis
        import_analysis = self.pattern_analyzer.analyze_import_patterns(file_metrics)
        
        # Function pattern analysis
        function_analysis = self.pattern_analyzer.analyze_function_patterns(file_metrics)
        
        # Quality trend analysis
        quality_analysis = self._analyze_quality_trends(file_metrics)
        
        # Technical debt prediction
        debt_prediction = self._predict_technical_debt(file_metrics)
        
        # Anomaly detection
        anomalies = self._detect_anomalies(file_metrics)
        
        # Risk assessment
        risk_assessment = self._assess_project_risks(
            complexity_analysis, quality_analysis, debt_prediction
        )
        
        analysis_time = time.time() - start_time
        
        return {
            'project_path': str(project_path),
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_duration_seconds': analysis_time,
            'files_analyzed': len(file_metrics),
            'complexity_trends': complexity_analysis,
            'import_patterns': import_analysis,
            'function_patterns': function_analysis,
            'quality_trends': quality_analysis,
            'technical_debt_prediction': debt_prediction,
            'anomaly_detection': anomalies,
            'risk_assessment': risk_assessment,
            'ml_confidence_scores': self._calculate_confidence_scores(
                complexity_analysis, import_analysis, function_analysis
            ),
            'actionable_insights': self._generate_actionable_insights(
                complexity_analysis, quality_analysis, risk_assessment
            )
        }
    
    def _run_basic_analysis(self, project_path: Path) -> List[Dict]:
        """Run basic file analysis if needed"""
        # Import and run production analyzer
        try:
            from PRODUCTION_READY_ANALYZER import RealTimeCodeAnalyzer
            analyzer = RealTimeCodeAnalyzer()
            
            python_files = list(project_path.rglob("*.py"))[:50]  # Limit for performance
            file_metrics = []
            
            for file_path in python_files:
                metrics = analyzer.analyze_file(str(file_path))
                if 'error' not in metrics:
                    file_metrics.append(metrics)
            
            return file_metrics
        except Exception as e:
            self.logger.error(f"Could not run basic analysis: {e}")
            return []
    
    def _analyze_quality_trends(self, file_metrics: List[Dict]) -> Dict[str, Any]:
        """Analyze quality trends over time/files"""
        
        quality_scores = []
        maintainability_scores = []
        comment_ratios = []
        
        for metrics in file_metrics:
            quality_scores.append(metrics.get('quality_score', 0))
            maintainability_scores.append(metrics.get('maintainability_index', 0))
            comment_ratios.append(metrics.get('comment_ratio', 0))
        
        if not quality_scores:
            return {}
        
        file_indices = list(range(len(quality_scores)))
        
        # Quality trend analysis
        quality_slope, quality_intercept, quality_correlation = \
            self.trend_analyzer.linear_regression(file_indices, quality_scores)
        
        # Maintainability trend
        maint_slope, maint_intercept, maint_correlation = \
            self.trend_analyzer.linear_regression(file_indices, maintainability_scores)
        
        # Comment trend
        comment_slope, comment_intercept, comment_correlation = \
            self.trend_analyzer.linear_regression(file_indices, comment_ratios)
        
        # Trend strengths
        quality_trend = self.trend_analyzer.calculate_trend_strength(quality_scores)
        maint_trend = self.trend_analyzer.calculate_trend_strength(maintainability_scores)
        
        return {
            'quality_trend': {
                'slope': quality_slope,
                'correlation': quality_correlation,
                'trend_strength': quality_trend,
                'current_average': statistics.mean(quality_scores),
                'predicted_next_5': [
                    max(0, min(100, quality_slope * (len(quality_scores) + i) + quality_intercept))
                    for i in range(1, 6)
                ]
            },
            'maintainability_trend': {
                'slope': maint_slope,
                'correlation': maint_correlation,
                'trend_strength': maint_trend,
                'current_average': statistics.mean(maintainability_scores),
                'predicted_next_5': [
                    max(0, min(100, maint_slope * (len(maintainability_scores) + i) + maint_intercept))
                    for i in range(1, 6)
                ]
            },
            'documentation_trend': {
                'slope': comment_slope,
                'correlation': comment_correlation,
                'current_average': statistics.mean(comment_ratios)
            }
        }
    
    def _predict_technical_debt(self, file_metrics: List[Dict]) -> Dict[str, Any]:
        """Predict technical debt accumulation"""
        
        # Calculate debt indicators
        debt_indicators = []
        
        for metrics in file_metrics:
            complexity = metrics.get('cyclomatic_complexity', 0)
            quality = metrics.get('quality_score', 100)
            maintainability = metrics.get('maintainability_index', 100)
            comment_ratio = metrics.get('comment_ratio', 0)
            
            # Weighted debt score (higher = more debt)
            debt_score = (
                (complexity / 20) * 0.3 +  # Normalize complexity
                ((100 - quality) / 100) * 0.3 +  # Quality penalty
                ((100 - maintainability) / 100) * 0.25 +  # Maintainability penalty
                (max(0, 15 - comment_ratio) / 15) * 0.15  # Documentation penalty
            )
            
            debt_indicators.append(min(1.0, debt_score))
        
        if not debt_indicators:
            return {}
        
        # Analyze debt trend
        file_indices = list(range(len(debt_indicators)))
        debt_slope, debt_intercept, debt_correlation = \
            self.trend_analyzer.linear_regression(file_indices, debt_indicators)
        
        # Calculate debt velocity (rate of accumulation)
        debt_velocity = debt_slope * len(debt_indicators)
        
        # Predict future debt levels
        future_debt = [
            max(0, min(1, debt_slope * (len(debt_indicators) + i) + debt_intercept))
            for i in range(1, 13)  # Next 12 periods
        ]
        
        # Risk categorization
        current_avg_debt = statistics.mean(debt_indicators)
        if current_avg_debt < 0.3:
            debt_level = "LOW"
        elif current_avg_debt < 0.6:
            debt_level = "MODERATE"
        elif current_avg_debt < 0.8:
            debt_level = "HIGH"
        else:
            debt_level = "CRITICAL"
        
        return {
            'current_debt_level': debt_level,
            'average_debt_score': current_avg_debt,
            'debt_velocity': debt_velocity,
            'debt_trend_correlation': debt_correlation,
            'predicted_debt_12_months': future_debt,
            'high_debt_files': len([d for d in debt_indicators if d > 0.7]),
            'debt_statistics': {
                'min': min(debt_indicators),
                'max': max(debt_indicators),
                'median': statistics.median(debt_indicators),
                'std': statistics.stdev(debt_indicators) if len(debt_indicators) > 1 else 0
            }
        }
    
    def _detect_anomalies(self, file_metrics: List[Dict]) -> Dict[str, Any]:
        """Detect anomalous files and patterns"""
        
        # Extract metrics for anomaly detection
        complexities = [m.get('cyclomatic_complexity', 0) for m in file_metrics]
        quality_scores = [m.get('quality_score', 0) for m in file_metrics]
        file_sizes = [m.get('lines_of_code', 0) for m in file_metrics]
        
        anomalies = {
            'complexity_outliers': self.trend_analyzer.detect_outliers(complexities),
            'quality_outliers': self.trend_analyzer.detect_outliers(quality_scores),
            'size_outliers': self.trend_analyzer.detect_outliers(file_sizes)
        }
        
        # Find files that are outliers in multiple dimensions
        all_outliers = set()
        for outlier_list in anomalies.values():
            all_outliers.update(outlier_list)
        
        multi_dimension_outliers = []
        for idx in all_outliers:
            outlier_count = sum(1 for outlier_list in anomalies.values() if idx in outlier_list)
            if outlier_count >= 2:
                multi_dimension_outliers.append({
                    'file_index': idx,
                    'file_path': file_metrics[idx].get('file_path', ''),
                    'outlier_dimensions': outlier_count,
                    'complexity': complexities[idx],
                    'quality': quality_scores[idx],
                    'size': file_sizes[idx]
                })
        
        return {
            'total_anomalies': len(all_outliers),
            'anomaly_percentage': len(all_outliers) / len(file_metrics) * 100,
            'complexity_anomalies': len(anomalies['complexity_outliers']),
            'quality_anomalies': len(anomalies['quality_outliers']),
            'size_anomalies': len(anomalies['size_outliers']),
            'multi_dimension_anomalies': multi_dimension_outliers,
            'severity_assessment': self._assess_anomaly_severity(len(all_outliers), len(file_metrics))
        }
    
    def _assess_project_risks(self, complexity_analysis: Dict, quality_analysis: Dict, 
                            debt_prediction: Dict) -> Dict[str, Any]:
        """Assess overall project risks based on ML analysis"""
        
        risks = []
        risk_score = 0
        
        # Complexity risks
        if complexity_analysis:
            complexity_trend = complexity_analysis.get('complexity_trend', {})
            if complexity_trend.get('slope', 0) > 0.5:
                risks.append("Increasing complexity trend detected")
                risk_score += 20
            
            avg_complexity = complexity_trend.get('trend_strength', {}).get('strength', 0)
            if avg_complexity > 0.7:
                risks.append("High complexity variability")
                risk_score += 15
        
        # Quality risks
        if quality_analysis:
            quality_trend = quality_analysis.get('quality_trend', {})
            if quality_trend.get('slope', 0) < -0.5:
                risks.append("Declining quality trend")
                risk_score += 25
            
            current_quality = quality_trend.get('current_average', 100)
            if current_quality < 60:
                risks.append("Low overall code quality")
                risk_score += 20
        
        # Technical debt risks
        if debt_prediction:
            debt_level = debt_prediction.get('current_debt_level', 'LOW')
            if debt_level in ['HIGH', 'CRITICAL']:
                risks.append(f"{debt_level.lower()} technical debt level")
                risk_score += 30 if debt_level == 'CRITICAL' else 20
            
            debt_velocity = debt_prediction.get('debt_velocity', 0)
            if debt_velocity > 0.1:
                risks.append("Rapid technical debt accumulation")
                risk_score += 15
        
        # Overall risk assessment
        if risk_score < 20:
            overall_risk = "LOW"
        elif risk_score < 50:
            overall_risk = "MODERATE"
        elif risk_score < 80:
            overall_risk = "HIGH"
        else:
            overall_risk = "CRITICAL"
        
        return {
            'overall_risk_level': overall_risk,
            'risk_score': risk_score,
            'identified_risks': risks,
            'risk_count': len(risks),
            'mitigation_priority': "IMMEDIATE" if risk_score > 60 else "PLANNED" if risk_score > 30 else "ROUTINE"
        }
    
    def _calculate_confidence_scores(self, complexity_analysis: Dict, import_analysis: Dict, 
                                   function_analysis: Dict) -> Dict[str, float]:
        """Calculate confidence scores for ML predictions"""
        
        confidence_scores = {}
        
        # Complexity prediction confidence
        if complexity_analysis:
            complexity_correlation = abs(complexity_analysis.get('complexity_trend', {}).get('correlation', 0))
            confidence_scores['complexity_predictions'] = min(100, complexity_correlation * 100)
        
        # Import pattern confidence
        if import_analysis:
            import_correlation = abs(import_analysis.get('import_trend', {}).get('correlation', 0))
            confidence_scores['import_predictions'] = min(100, import_correlation * 100)
        
        # Function pattern confidence
        if function_analysis:
            func_correlation = abs(function_analysis.get('complexity_length_relationship', {}).get('correlation', 0))
            confidence_scores['function_predictions'] = min(100, func_correlation * 100)
        
        # Overall confidence
        if confidence_scores:
            confidence_scores['overall_confidence'] = statistics.mean(confidence_scores.values())
        
        return confidence_scores
    
    def _generate_actionable_insights(self, complexity_analysis: Dict, quality_analysis: Dict, 
                                    risk_assessment: Dict) -> List[str]:
        """Generate actionable insights based on ML analysis"""
        
        insights = []
        
        # Complexity insights
        if complexity_analysis:
            complexity_trend = complexity_analysis.get('complexity_trend', {})
            if complexity_trend.get('slope', 0) > 0:
                insights.append("Focus on refactoring to reduce growing complexity")
            
            outlier_percentage = complexity_analysis.get('outlier_analysis', {}).get('outlier_percentage', 0)
            if outlier_percentage > 20:
                insights.append(f"{outlier_percentage:.1f}% of files have unusual complexity - prioritize review")
        
        # Quality insights
        if quality_analysis:
            quality_trend = quality_analysis.get('quality_trend', {})
            predicted_quality = quality_trend.get('predicted_next_5', [])
            if predicted_quality and predicted_quality[-1] < 70:
                insights.append("Quality trend suggests intervention needed within 5 iterations")
            
            comment_trend = quality_analysis.get('documentation_trend', {})
            if comment_trend.get('current_average', 0) < 10:
                insights.append("Increase documentation coverage - currently below recommended levels")
        
        # Risk-based insights
        if risk_assessment:
            risk_level = risk_assessment.get('overall_risk_level', 'LOW')
            if risk_level in ['HIGH', 'CRITICAL']:
                insights.append(f"Project at {risk_level} risk - implement quality gates immediately")
            
            identified_risks = risk_assessment.get('identified_risks', [])
            if len(identified_risks) > 3:
                insights.append("Multiple risk factors detected - comprehensive quality review recommended")
        
        # Default insight
        if not insights:
            insights.append("Code metrics are within acceptable ranges - maintain current practices")
        
        return insights
    
    def _assess_anomaly_severity(self, anomaly_count: int, total_files: int) -> str:
        """Assess the severity of detected anomalies"""
        percentage = anomaly_count / total_files * 100 if total_files > 0 else 0
        
        if percentage < 5:
            return "LOW"
        elif percentage < 15:
            return "MODERATE"
        elif percentage < 30:
            return "HIGH"
        else:
            return "CRITICAL"

def main():
    """Main entry point for real ML analyzer"""
    if len(sys.argv) != 2:
        print("Usage: python REAL_ML_ANALYZER.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    if not os.path.exists(project_path):
        print(f"Error: Path {project_path} does not exist")
        sys.exit(1)
    
    print("🤖 Starting Real ML Analysis...")
    
    analyzer = RealMLAnalyzer()
    results = analyzer.analyze_project_trends(project_path)
    
    # Save results
    output_file = "REAL_ML_ANALYSIS_REPORT.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Display summary
    if 'error' not in results:
        print(f"\n📊 ML Analysis Summary:")
        print(f"   Files analyzed: {results['files_analyzed']}")
        print(f"   Analysis time: {results['analysis_duration_seconds']:.2f}s")
        
        # Risk assessment
        risk = results.get('risk_assessment', {})
        if risk:
            print(f"\n🚨 Risk Assessment:")
            print(f"   Overall risk: {risk.get('overall_risk_level', 'UNKNOWN')}")
            print(f"   Risk score: {risk.get('risk_score', 0)}/100")
            print(f"   Identified risks: {risk.get('risk_count', 0)}")
        
        # Technical debt
        debt = results.get('technical_debt_prediction', {})
        if debt:
            print(f"\n💳 Technical Debt:")
            print(f"   Current level: {debt.get('current_debt_level', 'UNKNOWN')}")
            print(f"   Average score: {debt.get('average_debt_score', 0):.2f}")
            print(f"   High debt files: {debt.get('high_debt_files', 0)}")
        
        # Anomalies
        anomalies = results.get('anomaly_detection', {})
        if anomalies:
            print(f"\n🔍 Anomaly Detection:")
            print(f"   Total anomalies: {anomalies.get('total_anomalies', 0)}")
            print(f"   Anomaly rate: {anomalies.get('anomaly_percentage', 0):.1f}%")
            print(f"   Severity: {anomalies.get('severity_assessment', 'UNKNOWN')}")
        
        # Confidence scores
        confidence = results.get('ml_confidence_scores', {})
        if confidence:
            print(f"\n🎯 ML Confidence:")
            print(f"   Overall: {confidence.get('overall_confidence', 0):.1f}%")
        
        # Insights
        insights = results.get('actionable_insights', [])
        if insights:
            print(f"\n💡 Key Insights:")
            for i, insight in enumerate(insights[:5], 1):
                print(f"   {i}. {insight}")
    else:
        print(f"Error: {results['error']}")
    
    print(f"\n📄 Detailed report saved to: {output_file}")
    print("✅ Real ML analysis completed!")

if __name__ == "__main__":
    main()