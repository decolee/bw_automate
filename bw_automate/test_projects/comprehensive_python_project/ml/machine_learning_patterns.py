"""
Machine Learning and Data Science Patterns
Testing various ML algorithms, data preprocessing, feature engineering patterns
"""

import numpy as np
import math
import statistics
from typing import List, Dict, Tuple, Any, Optional, Union, Callable
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import json
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

# Simulated numpy-like operations (for environments without numpy)
class SimpleArray:
    def __init__(self, data: List[float]):
        self.data = data
        self.shape = (len(data),)
    
    def mean(self) -> float:
        return sum(self.data) / len(self.data)
    
    def std(self) -> float:
        mean_val = self.mean()
        variance = sum((x - mean_val) ** 2 for x in self.data) / len(self.data)
        return math.sqrt(variance)
    
    def normalize(self) -> 'SimpleArray':
        min_val = min(self.data)
        max_val = max(self.data)
        range_val = max_val - min_val
        if range_val == 0:
            return SimpleArray([0.0] * len(self.data))
        normalized = [(x - min_val) / range_val for x in self.data]
        return SimpleArray(normalized)
    
    def standardize(self) -> 'SimpleArray':
        mean_val = self.mean()
        std_val = self.std()
        if std_val == 0:
            return SimpleArray([0.0] * len(self.data))
        standardized = [(x - mean_val) / std_val for x in self.data]
        return SimpleArray(standardized)

# Data Preprocessing Patterns
class DataPreprocessor:
    def __init__(self):
        self.scalers = {}
        self.encoders = {}
        
    def handle_missing_values(self, data: List[Dict], strategy: str = 'mean') -> List[Dict]:
        """Handle missing values in dataset"""
        if not data:
            return data
        
        # Identify numeric and categorical columns
        sample_record = data[0]
        numeric_cols = []
        categorical_cols = []
        
        for key, value in sample_record.items():
            try:
                float(value)
                numeric_cols.append(key)
            except (ValueError, TypeError):
                categorical_cols.append(key)
        
        # Calculate statistics for imputation
        col_stats = {}
        for col in numeric_cols:
            values = []
            for record in data:
                if record.get(col) is not None:
                    try:
                        values.append(float(record[col]))
                    except (ValueError, TypeError):
                        continue
            
            if values:
                col_stats[col] = {
                    'mean': sum(values) / len(values),
                    'median': statistics.median(values),
                    'mode': statistics.mode(values) if len(set(values)) < len(values) else values[0]
                }
        
        for col in categorical_cols:
            values = [record.get(col) for record in data if record.get(col) is not None]
            if values:
                col_stats[col] = {'mode': max(set(values), key=values.count)}
        
        # Apply imputation
        processed_data = []
        for record in data:
            new_record = record.copy()
            
            for col in numeric_cols:
                if record.get(col) is None or record.get(col) == '':
                    if col in col_stats:
                        if strategy == 'mean':
                            new_record[col] = col_stats[col]['mean']
                        elif strategy == 'median':
                            new_record[col] = col_stats[col]['median']
                        elif strategy == 'mode':
                            new_record[col] = col_stats[col]['mode']
                        else:
                            new_record[col] = 0  # Default
            
            for col in categorical_cols:
                if record.get(col) is None or record.get(col) == '':
                    if col in col_stats:
                        new_record[col] = col_stats[col]['mode']
                    else:
                        new_record[col] = 'unknown'
            
            processed_data.append(new_record)
        
        return processed_data
    
    def encode_categorical(self, data: List[Dict], columns: List[str], 
                          method: str = 'one_hot') -> List[Dict]:
        """Encode categorical variables"""
        if method == 'one_hot':
            return self._one_hot_encode(data, columns)
        elif method == 'label':
            return self._label_encode(data, columns)
        else:
            return data
    
    def _one_hot_encode(self, data: List[Dict], columns: List[str]) -> List[Dict]:
        """One-hot encode categorical columns"""
        # Find unique values for each column
        unique_values = {}
        for col in columns:
            values = set()
            for record in data:
                if col in record and record[col] is not None:
                    values.add(str(record[col]))
            unique_values[col] = sorted(list(values))
        
        # Create encoded data
        encoded_data = []
        for record in data:
            new_record = record.copy()
            
            for col in columns:
                # Remove original column
                if col in new_record:
                    original_value = str(new_record.pop(col))
                    
                    # Add one-hot encoded columns
                    for value in unique_values[col]:
                        new_col_name = f"{col}_{value}"
                        new_record[new_col_name] = 1 if original_value == value else 0
            
            encoded_data.append(new_record)
        
        return encoded_data
    
    def _label_encode(self, data: List[Dict], columns: List[str]) -> List[Dict]:
        """Label encode categorical columns"""
        # Create label mappings
        label_mappings = {}
        for col in columns:
            unique_values = set()
            for record in data:
                if col in record and record[col] is not None:
                    unique_values.add(str(record[col]))
            label_mappings[col] = {value: i for i, value in enumerate(sorted(unique_values))}
        
        # Apply label encoding
        encoded_data = []
        for record in data:
            new_record = record.copy()
            for col in columns:
                if col in new_record and new_record[col] is not None:
                    value = str(new_record[col])
                    new_record[col] = label_mappings[col].get(value, -1)
            encoded_data.append(new_record)
        
        self.encoders.update(label_mappings)
        return encoded_data
    
    def scale_features(self, data: List[Dict], columns: List[str], 
                      method: str = 'standard') -> List[Dict]:
        """Scale numerical features"""
        if not data or not columns:
            return data
        
        # Calculate scaling parameters
        scaling_params = {}
        for col in columns:
            values = []
            for record in data:
                if col in record:
                    try:
                        values.append(float(record[col]))
                    except (ValueError, TypeError):
                        continue
            
            if values:
                if method == 'standard':
                    mean_val = sum(values) / len(values)
                    variance = sum((x - mean_val) ** 2 for x in values) / len(values)
                    std_val = math.sqrt(variance)
                    scaling_params[col] = {'mean': mean_val, 'std': std_val}
                elif method == 'minmax':
                    min_val = min(values)
                    max_val = max(values)
                    scaling_params[col] = {'min': min_val, 'max': max_val}
        
        # Apply scaling
        scaled_data = []
        for record in data:
            new_record = record.copy()
            for col in columns:
                if col in new_record and col in scaling_params:
                    try:
                        value = float(new_record[col])
                        if method == 'standard':
                            params = scaling_params[col]
                            if params['std'] != 0:
                                new_record[col] = (value - params['mean']) / params['std']
                            else:
                                new_record[col] = 0
                        elif method == 'minmax':
                            params = scaling_params[col]
                            range_val = params['max'] - params['min']
                            if range_val != 0:
                                new_record[col] = (value - params['min']) / range_val
                            else:
                                new_record[col] = 0
                    except (ValueError, TypeError):
                        continue
            scaled_data.append(new_record)
        
        self.scalers.update(scaling_params)
        return scaled_data

# Feature Engineering Patterns
class FeatureEngineer:
    def __init__(self):
        self.feature_functions = {}
    
    def create_polynomial_features(self, data: List[Dict], columns: List[str], 
                                 degree: int = 2) -> List[Dict]:
        """Create polynomial features"""
        enhanced_data = []
        
        for record in data:
            new_record = record.copy()
            
            # Create polynomial features
            for col in columns:
                if col in record:
                    try:
                        value = float(record[col])
                        for d in range(2, degree + 1):
                            new_record[f"{col}^{d}"] = value ** d
                    except (ValueError, TypeError):
                        continue
            
            # Create interaction features
            for i, col1 in enumerate(columns):
                for col2 in columns[i+1:]:
                    if col1 in record and col2 in record:
                        try:
                            val1 = float(record[col1])
                            val2 = float(record[col2])
                            new_record[f"{col1}*{col2}"] = val1 * val2
                        except (ValueError, TypeError):
                            continue
            
            enhanced_data.append(new_record)
        
        return enhanced_data
    
    def create_datetime_features(self, data: List[Dict], datetime_col: str) -> List[Dict]:
        """Extract features from datetime column"""
        enhanced_data = []
        
        for record in data:
            new_record = record.copy()
            
            if datetime_col in record and record[datetime_col]:
                dt_str = str(record[datetime_col])
                try:
                    # Try multiple datetime formats
                    dt = None
                    formats = ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y', '%d/%m/%Y']
                    
                    for fmt in formats:
                        try:
                            dt = datetime.strptime(dt_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if dt:
                        new_record[f"{datetime_col}_year"] = dt.year
                        new_record[f"{datetime_col}_month"] = dt.month
                        new_record[f"{datetime_col}_day"] = dt.day
                        new_record[f"{datetime_col}_weekday"] = dt.weekday()
                        new_record[f"{datetime_col}_quarter"] = (dt.month - 1) // 3 + 1
                        new_record[f"{datetime_col}_is_weekend"] = 1 if dt.weekday() >= 5 else 0
                        
                except ValueError:
                    logging.warning(f"Could not parse datetime: {dt_str}")
            
            enhanced_data.append(new_record)
        
        return enhanced_data
    
    def create_binned_features(self, data: List[Dict], column: str, 
                              bins: int = 5, strategy: str = 'equal_width') -> List[Dict]:
        """Create binned categorical features from numerical data"""
        # Extract values for binning
        values = []
        for record in data:
            if column in record:
                try:
                    values.append(float(record[column]))
                except (ValueError, TypeError):
                    continue
        
        if not values:
            return data
        
        # Create bins
        if strategy == 'equal_width':
            min_val, max_val = min(values), max(values)
            bin_width = (max_val - min_val) / bins
            bin_edges = [min_val + i * bin_width for i in range(bins + 1)]
        elif strategy == 'equal_frequency':
            sorted_values = sorted(values)
            bin_size = len(sorted_values) // bins
            bin_edges = [sorted_values[i * bin_size] for i in range(bins)]
            bin_edges.append(sorted_values[-1])
        else:
            return data
        
        # Apply binning
        binned_data = []
        for record in data:
            new_record = record.copy()
            
            if column in record:
                try:
                    value = float(record[column])
                    bin_index = 0
                    for i in range(len(bin_edges) - 1):
                        if bin_edges[i] <= value < bin_edges[i + 1]:
                            bin_index = i
                            break
                    else:
                        bin_index = bins - 1  # Last bin
                    
                    new_record[f"{column}_bin"] = bin_index
                    new_record[f"{column}_bin_range"] = f"{bin_edges[bin_index]:.2f}-{bin_edges[bin_index+1]:.2f}"
                    
                except (ValueError, TypeError):
                    new_record[f"{column}_bin"] = -1
                    new_record[f"{column}_bin_range"] = "unknown"
            
            binned_data.append(new_record)
        
        return binned_data

# Machine Learning Models
class BaseModel(ABC):
    def __init__(self):
        self.is_trained = False
        self.feature_names = []
    
    @abstractmethod
    def fit(self, X: List[List[float]], y: List[float]):
        pass
    
    @abstractmethod
    def predict(self, X: List[List[float]]) -> List[float]:
        pass

class LinearRegression(BaseModel):
    def __init__(self):
        super().__init__()
        self.weights = []
        self.bias = 0.0
        self.learning_rate = 0.01
        self.iterations = 1000
    
    def fit(self, X: List[List[float]], y: List[float]):
        """Train linear regression model using gradient descent"""
        if not X or not y or len(X) != len(y):
            raise ValueError("Invalid training data")
        
        n_samples = len(X)
        n_features = len(X[0])
        
        # Initialize weights and bias
        self.weights = [0.0] * n_features
        self.bias = 0.0
        
        # Gradient descent
        for _ in range(self.iterations):
            # Forward pass
            predictions = []
            for i in range(n_samples):
                pred = self.bias + sum(self.weights[j] * X[i][j] for j in range(n_features))
                predictions.append(pred)
            
            # Calculate gradients
            weight_gradients = [0.0] * n_features
            bias_gradient = 0.0
            
            for i in range(n_samples):
                error = predictions[i] - y[i]
                bias_gradient += error
                for j in range(n_features):
                    weight_gradients[j] += error * X[i][j]
            
            # Update parameters
            self.bias -= self.learning_rate * bias_gradient / n_samples
            for j in range(n_features):
                self.weights[j] -= self.learning_rate * weight_gradients[j] / n_samples
        
        self.is_trained = True
    
    def predict(self, X: List[List[float]]) -> List[float]:
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        predictions = []
        for sample in X:
            pred = self.bias + sum(self.weights[j] * sample[j] for j in range(len(sample)))
            predictions.append(pred)
        
        return predictions

class LogisticRegression(BaseModel):
    def __init__(self):
        super().__init__()
        self.weights = []
        self.bias = 0.0
        self.learning_rate = 0.01
        self.iterations = 1000
    
    def _sigmoid(self, z: float) -> float:
        """Sigmoid activation function"""
        return 1 / (1 + math.exp(-max(-500, min(500, z))))  # Prevent overflow
    
    def fit(self, X: List[List[float]], y: List[int]):
        """Train logistic regression model"""
        if not X or not y or len(X) != len(y):
            raise ValueError("Invalid training data")
        
        n_samples = len(X)
        n_features = len(X[0])
        
        # Initialize weights and bias
        self.weights = [0.0] * n_features
        self.bias = 0.0
        
        # Gradient descent
        for _ in range(self.iterations):
            # Forward pass
            predictions = []
            for i in range(n_samples):
                z = self.bias + sum(self.weights[j] * X[i][j] for j in range(n_features))
                pred = self._sigmoid(z)
                predictions.append(pred)
            
            # Calculate gradients
            weight_gradients = [0.0] * n_features
            bias_gradient = 0.0
            
            for i in range(n_samples):
                error = predictions[i] - y[i]
                bias_gradient += error
                for j in range(n_features):
                    weight_gradients[j] += error * X[i][j]
            
            # Update parameters
            self.bias -= self.learning_rate * bias_gradient / n_samples
            for j in range(n_features):
                self.weights[j] -= self.learning_rate * weight_gradients[j] / n_samples
        
        self.is_trained = True
    
    def predict(self, X: List[List[float]]) -> List[int]:
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        predictions = []
        for sample in X:
            z = self.bias + sum(self.weights[j] * sample[j] for j in range(len(sample)))
            prob = self._sigmoid(z)
            predictions.append(1 if prob >= 0.5 else 0)
        
        return predictions
    
    def predict_proba(self, X: List[List[float]]) -> List[float]:
        """Predict probabilities"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        probabilities = []
        for sample in X:
            z = self.bias + sum(self.weights[j] * sample[j] for j in range(len(sample)))
            prob = self._sigmoid(z)
            probabilities.append(prob)
        
        return probabilities

class KNearestNeighbors(BaseModel):
    def __init__(self, k: int = 5):
        super().__init__()
        self.k = k
        self.X_train = []
        self.y_train = []
    
    def _euclidean_distance(self, point1: List[float], point2: List[float]) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(point1, point2)))
    
    def fit(self, X: List[List[float]], y: List[Any]):
        """Store training data"""
        self.X_train = X.copy()
        self.y_train = y.copy()
        self.is_trained = True
    
    def predict(self, X: List[List[float]]) -> List[Any]:
        """Make predictions using k-nearest neighbors"""
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        predictions = []
        
        for sample in X:
            # Calculate distances to all training points
            distances = []
            for i, train_sample in enumerate(self.X_train):
                dist = self._euclidean_distance(sample, train_sample)
                distances.append((dist, self.y_train[i]))
            
            # Sort by distance and get k nearest neighbors
            distances.sort(key=lambda x: x[0])
            k_nearest = distances[:self.k]
            
            # Get most common class among k nearest neighbors
            neighbor_labels = [label for _, label in k_nearest]
            prediction = max(set(neighbor_labels), key=neighbor_labels.count)
            predictions.append(prediction)
        
        return predictions

# Model Evaluation Patterns
class ModelEvaluator:
    @staticmethod
    def mean_squared_error(y_true: List[float], y_pred: List[float]) -> float:
        """Calculate mean squared error"""
        if len(y_true) != len(y_pred):
            raise ValueError("Arrays must have same length")
        
        mse = sum((true - pred) ** 2 for true, pred in zip(y_true, y_pred)) / len(y_true)
        return mse
    
    @staticmethod
    def root_mean_squared_error(y_true: List[float], y_pred: List[float]) -> float:
        """Calculate root mean squared error"""
        return math.sqrt(ModelEvaluator.mean_squared_error(y_true, y_pred))
    
    @staticmethod
    def mean_absolute_error(y_true: List[float], y_pred: List[float]) -> float:
        """Calculate mean absolute error"""
        if len(y_true) != len(y_pred):
            raise ValueError("Arrays must have same length")
        
        mae = sum(abs(true - pred) for true, pred in zip(y_true, y_pred)) / len(y_true)
        return mae
    
    @staticmethod
    def r_squared(y_true: List[float], y_pred: List[float]) -> float:
        """Calculate R-squared (coefficient of determination)"""
        if len(y_true) != len(y_pred):
            raise ValueError("Arrays must have same length")
        
        y_mean = sum(y_true) / len(y_true)
        ss_res = sum((true - pred) ** 2 for true, pred in zip(y_true, y_pred))
        ss_tot = sum((true - y_mean) ** 2 for true in y_true)
        
        if ss_tot == 0:
            return 1.0 if ss_res == 0 else 0.0
        
        return 1 - (ss_res / ss_tot)
    
    @staticmethod
    def accuracy(y_true: List[Any], y_pred: List[Any]) -> float:
        """Calculate classification accuracy"""
        if len(y_true) != len(y_pred):
            raise ValueError("Arrays must have same length")
        
        correct = sum(1 for true, pred in zip(y_true, y_pred) if true == pred)
        return correct / len(y_true)
    
    @staticmethod
    def confusion_matrix(y_true: List[Any], y_pred: List[Any]) -> Dict:
        """Calculate confusion matrix"""
        if len(y_true) != len(y_pred):
            raise ValueError("Arrays must have same length")
        
        labels = sorted(set(y_true + y_pred))
        matrix = defaultdict(lambda: defaultdict(int))
        
        for true, pred in zip(y_true, y_pred):
            matrix[true][pred] += 1
        
        return {
            'labels': labels,
            'matrix': {true_label: dict(matrix[true_label]) for true_label in labels}
        }
    
    @staticmethod
    def classification_report(y_true: List[Any], y_pred: List[Any]) -> Dict:
        """Generate classification report with precision, recall, F1-score"""
        if len(y_true) != len(y_pred):
            raise ValueError("Arrays must have same length")
        
        labels = sorted(set(y_true))
        report = {}
        
        for label in labels:
            tp = sum(1 for true, pred in zip(y_true, y_pred) if true == label and pred == label)
            fp = sum(1 for true, pred in zip(y_true, y_pred) if true != label and pred == label)
            fn = sum(1 for true, pred in zip(y_true, y_pred) if true == label and pred != label)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            report[label] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'support': sum(1 for true in y_true if true == label)
            }
        
        return report

# Cross-Validation Patterns
class CrossValidator:
    def __init__(self, k_folds: int = 5):
        self.k_folds = k_folds
    
    def k_fold_split(self, X: List[List[float]], y: List[Any]) -> List[Tuple]:
        """Split data into k folds"""
        n_samples = len(X)
        fold_size = n_samples // self.k_folds
        
        indices = list(range(n_samples))
        random.shuffle(indices)
        
        folds = []
        for i in range(self.k_folds):
            start = i * fold_size
            end = start + fold_size if i < self.k_folds - 1 else n_samples
            
            test_indices = indices[start:end]
            train_indices = indices[:start] + indices[end:]
            
            X_train = [X[j] for j in train_indices]
            X_test = [X[j] for j in test_indices]
            y_train = [y[j] for j in train_indices]
            y_test = [y[j] for j in test_indices]
            
            folds.append((X_train, X_test, y_train, y_test))
        
        return folds
    
    def cross_validate(self, model_class: type, X: List[List[float]], 
                      y: List[Any], **model_kwargs) -> Dict:
        """Perform k-fold cross-validation"""
        folds = self.k_fold_split(X, y)
        scores = []
        
        for X_train, X_test, y_train, y_test in folds:
            # Create and train model
            model = model_class(**model_kwargs)
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate score (accuracy for classification)
            score = ModelEvaluator.accuracy(y_test, y_pred)
            scores.append(score)
        
        return {
            'scores': scores,
            'mean_score': sum(scores) / len(scores),
            'std_score': math.sqrt(sum((s - sum(scores) / len(scores)) ** 2 for s in scores) / len(scores))
        }

# Example usage and testing
if __name__ == "__main__":
    # Generate sample data
    random.seed(42)
    
    # Classification data
    n_samples = 100
    X_classification = []
    y_classification = []
    
    for _ in range(n_samples):
        x1 = random.uniform(-5, 5)
        x2 = random.uniform(-5, 5)
        X_classification.append([x1, x2])
        # Simple decision boundary: x1 + x2 > 0
        y_classification.append(1 if x1 + x2 + random.uniform(-1, 1) > 0 else 0)
    
    # Regression data
    X_regression = []
    y_regression = []
    
    for _ in range(n_samples):
        x1 = random.uniform(-10, 10)
        x2 = random.uniform(-10, 10)
        X_regression.append([x1, x2])
        # Linear relationship with noise
        y_regression.append(2 * x1 + 3 * x2 + random.uniform(-2, 2))
    
    # Test models
    print("Testing Linear Regression...")
    lr_model = LinearRegression()
    lr_model.fit(X_regression[:80], y_regression[:80])
    lr_predictions = lr_model.predict(X_regression[80:])
    lr_mse = ModelEvaluator.mean_squared_error(y_regression[80:], lr_predictions)
    print(f"Linear Regression MSE: {lr_mse:.4f}")
    
    print("\nTesting Logistic Regression...")
    log_model = LogisticRegression()
    log_model.fit(X_classification[:80], y_classification[:80])
    log_predictions = log_model.predict(X_classification[80:])
    log_accuracy = ModelEvaluator.accuracy(y_classification[80:], log_predictions)
    print(f"Logistic Regression Accuracy: {log_accuracy:.4f}")
    
    print("\nTesting KNN...")
    knn_model = KNearestNeighbors(k=3)
    knn_model.fit(X_classification[:80], y_classification[:80])
    knn_predictions = knn_model.predict(X_classification[80:])
    knn_accuracy = ModelEvaluator.accuracy(y_classification[80:], knn_predictions)
    print(f"KNN Accuracy: {knn_accuracy:.4f}")
    
    print("\nTesting Cross-Validation...")
    cv = CrossValidator(k_folds=5)
    cv_results = cv.cross_validate(LogisticRegression, X_classification, y_classification)
    print(f"Cross-Validation Results: {cv_results}")
    
    # Test preprocessing
    print("\nTesting Data Preprocessing...")
    sample_data = [
        {'feature1': '1.0', 'feature2': '2.0', 'category': 'A'},
        {'feature1': '2.0', 'feature2': None, 'category': 'B'},
        {'feature1': None, 'feature2': '4.0', 'category': 'A'},
        {'feature1': '4.0', 'feature2': '5.0', 'category': 'C'}
    ]
    
    preprocessor = DataPreprocessor()
    processed = preprocessor.handle_missing_values(sample_data, strategy='mean')
    encoded = preprocessor.encode_categorical(processed, ['category'], method='one_hot')
    scaled = preprocessor.scale_features(encoded, ['feature1', 'feature2'], method='standard')
    
    print(f"Preprocessed data sample: {scaled[0]}")
    
    # Test feature engineering
    print("\nTesting Feature Engineering...")
    feature_engineer = FeatureEngineer()
    poly_features = feature_engineer.create_polynomial_features(
        sample_data, ['feature1', 'feature2'], degree=2
    )
    print(f"Polynomial features sample: {poly_features[0] if poly_features else 'None'}")