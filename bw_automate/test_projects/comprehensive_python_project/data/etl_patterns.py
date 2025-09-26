"""
Data Processing and ETL (Extract, Transform, Load) Patterns
Testing various data transformation, validation, and processing operations
"""

import csv
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Union, Iterator, Callable
import re
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import os
import tempfile
from collections import defaultdict, Counter
from itertools import groupby, chain
from functools import reduce, partial
import operator
import sqlite3
import hashlib
import uuid

# Data Extraction Patterns
class DataExtractor:
    def __init__(self):
        self.supported_formats = ['csv', 'json', 'xml', 'txt']
        
    def extract_csv(self, file_path: str, delimiter: str = ',') -> List[Dict]:
        """Extract data from CSV file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file, delimiter=delimiter)
                return list(reader)
        except FileNotFoundError:
            logging.error(f"CSV file not found: {file_path}")
            return []
        except Exception as e:
            logging.error(f"Error reading CSV: {e}")
            return []
    
    def extract_json(self, file_path: str) -> Union[Dict, List]:
        """Extract data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            logging.error(f"JSON file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON format: {e}")
            return {}
    
    def extract_xml(self, file_path: str) -> Dict:
        """Extract data from XML file"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return self._xml_to_dict(root)
        except FileNotFoundError:
            logging.error(f"XML file not found: {file_path}")
            return {}
        except ET.ParseError as e:
            logging.error(f"Invalid XML format: {e}")
            return {}
    
    def _xml_to_dict(self, element: ET.Element) -> Dict:
        """Convert XML element to dictionary"""
        result = {}
        
        # Add attributes
        if element.attrib:
            result['@attributes'] = element.attrib
        
        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result['#text'] = element.text.strip()
        
        # Add child elements
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    def extract_from_string(self, data_string: str, format_type: str) -> Any:
        """Extract data from string based on format"""
        if format_type == 'json':
            try:
                return json.loads(data_string)
            except json.JSONDecodeError:
                return {}
        elif format_type == 'csv':
            lines = data_string.strip().split('\n')
            if len(lines) < 2:
                return []
            headers = lines[0].split(',')
            return [dict(zip(headers, line.split(','))) for line in lines[1:]]
        elif format_type == 'xml':
            try:
                root = ET.fromstring(data_string)
                return self._xml_to_dict(root)
            except ET.ParseError:
                return {}
        return data_string

# Data Transformation Patterns
class DataTransformer:
    def __init__(self):
        self.transformation_rules = {}
        self.validation_rules = {}
    
    def add_transformation_rule(self, field: str, transform_func: Callable):
        """Add a transformation rule for a specific field"""
        self.transformation_rules[field] = transform_func
    
    def add_validation_rule(self, field: str, validation_func: Callable):
        """Add a validation rule for a specific field"""
        self.validation_rules[field] = validation_func
    
    def transform_record(self, record: Dict) -> Dict:
        """Transform a single record using defined rules"""
        transformed = record.copy()
        
        for field, transform_func in self.transformation_rules.items():
            if field in transformed:
                try:
                    transformed[field] = transform_func(transformed[field])
                except Exception as e:
                    logging.warning(f"Transformation failed for field {field}: {e}")
                    transformed[f"{field}_error"] = str(e)
        
        return transformed
    
    def validate_record(self, record: Dict) -> Dict:
        """Validate a record and add validation results"""
        validation_results = {}
        
        for field, validation_func in self.validation_rules.items():
            if field in record:
                try:
                    is_valid = validation_func(record[field])
                    validation_results[f"{field}_valid"] = is_valid
                except Exception as e:
                    validation_results[f"{field}_validation_error"] = str(e)
        
        return {**record, **validation_results}
    
    def normalize_text(self, text: str) -> str:
        """Normalize text data"""
        if not isinstance(text, str):
            return str(text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters (optional)
        text = re.sub(r'[^\w\s-]', '', text)
        
        return text
    
    def parse_date(self, date_string: str, format_string: str = None) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_string:
            return None
        
        formats_to_try = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ'
        ]
        
        if format_string:
            formats_to_try.insert(0, format_string)
        
        for fmt in formats_to_try:
            try:
                return datetime.strptime(date_string.strip(), fmt)
            except ValueError:
                continue
        
        logging.warning(f"Could not parse date: {date_string}")
        return None
    
    def standardize_phone(self, phone: str) -> str:
        """Standardize phone number format"""
        if not phone:
            return ""
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Handle different formats
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        
        return phone  # Return original if can't standardize
    
    def categorize_numeric(self, value: float, thresholds: List[tuple]) -> str:
        """Categorize numeric value based on thresholds"""
        for threshold, category in thresholds:
            if value <= threshold:
                return category
        return "high"  # Default category

# Data Validation Patterns
class DataValidator:
    @staticmethod
    def is_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_phone(phone: str) -> bool:
        """Validate phone number format"""
        digits = re.sub(r'\D', '', phone)
        return len(digits) in [10, 11]
    
    @staticmethod
    def is_numeric_range(value: Any, min_val: float = None, max_val: float = None) -> bool:
        """Validate numeric value is within range"""
        try:
            num_val = float(value)
            if min_val is not None and num_val < min_val:
                return False
            if max_val is not None and num_val > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_required(value: Any) -> bool:
        """Validate that value is not empty"""
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        return True
    
    @staticmethod
    def matches_pattern(value: str, pattern: str) -> bool:
        """Validate that value matches regex pattern"""
        if not isinstance(value, str):
            return False
        return bool(re.match(pattern, value))

# Data Aggregation Patterns
class DataAggregator:
    def __init__(self, data: List[Dict]):
        self.data = data
    
    def group_by(self, key: str) -> Dict[Any, List[Dict]]:
        """Group records by a specific key"""
        grouped = defaultdict(list)
        for record in self.data:
            group_key = record.get(key)
            grouped[group_key].append(record)
        return dict(grouped)
    
    def aggregate_numeric(self, group_key: str, value_key: str, 
                         agg_func: str = 'sum') -> Dict[Any, float]:
        """Aggregate numeric values by group"""
        grouped = self.group_by(group_key)
        result = {}
        
        for group, records in grouped.items():
            values = []
            for record in records:
                try:
                    values.append(float(record.get(value_key, 0)))
                except (ValueError, TypeError):
                    continue
            
            if values:
                if agg_func == 'sum':
                    result[group] = sum(values)
                elif agg_func == 'avg' or agg_func == 'mean':
                    result[group] = sum(values) / len(values)
                elif agg_func == 'min':
                    result[group] = min(values)
                elif agg_func == 'max':
                    result[group] = max(values)
                elif agg_func == 'count':
                    result[group] = len(values)
                else:
                    result[group] = sum(values)  # Default to sum
        
        return result
    
    def count_values(self, key: str) -> Dict[Any, int]:
        """Count occurrences of values for a specific key"""
        values = [record.get(key) for record in self.data if key in record]
        return dict(Counter(values))
    
    def pivot_table(self, row_key: str, col_key: str, value_key: str, 
                   agg_func: str = 'sum') -> Dict[Any, Dict[Any, float]]:
        """Create a pivot table"""
        result = defaultdict(lambda: defaultdict(float))
        
        for record in self.data:
            row = record.get(row_key)
            col = record.get(col_key)
            value = record.get(value_key, 0)
            
            try:
                value = float(value)
                if agg_func == 'sum':
                    result[row][col] += value
                elif agg_func == 'count':
                    result[row][col] += 1
                elif agg_func == 'max':
                    result[row][col] = max(result[row][col], value)
                elif agg_func == 'min':
                    if result[row][col] == 0:
                        result[row][col] = value
                    else:
                        result[row][col] = min(result[row][col], value)
            except (ValueError, TypeError):
                continue
        
        return {k: dict(v) for k, v in result.items()}

# Data Loading Patterns
class DataLoader:
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or ":memory:"
        
    def load_to_sqlite(self, data: List[Dict], table_name: str) -> bool:
        """Load data to SQLite database"""
        if not data:
            return False
        
        try:
            conn = sqlite3.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Create table dynamically
            columns = list(data[0].keys())
            column_defs = [f"{col} TEXT" for col in columns]
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
            cursor.execute(create_sql)
            
            # Insert data
            placeholders = ', '.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            for record in data:
                values = [str(record.get(col, '')) for col in columns]
                cursor.execute(insert_sql, values)
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logging.error(f"Error loading to SQLite: {e}")
            return False
    
    def load_to_csv(self, data: List[Dict], file_path: str) -> bool:
        """Load data to CSV file"""
        if not data:
            return False
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=list(data[0].keys()))
                writer.writeheader()
                writer.writerows(data)
            return True
        except Exception as e:
            logging.error(f"Error loading to CSV: {e}")
            return False
    
    def load_to_json(self, data: List[Dict], file_path: str) -> bool:
        """Load data to JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, default=str)
            return True
        except Exception as e:
            logging.error(f"Error loading to JSON: {e}")
            return False

# ETL Pipeline Pattern
class ETLPipeline:
    def __init__(self):
        self.extractor = DataExtractor()
        self.transformer = DataTransformer()
        self.validator = DataValidator()
        self.aggregator = None
        self.loader = DataLoader()
        self.steps = []
        
    def add_extraction_step(self, source_path: str, format_type: str):
        """Add data extraction step"""
        self.steps.append(('extract', source_path, format_type))
        
    def add_transformation_step(self, transform_func: Callable):
        """Add data transformation step"""
        self.steps.append(('transform', transform_func))
        
    def add_validation_step(self, validation_func: Callable):
        """Add data validation step"""
        self.steps.append(('validate', validation_func))
        
    def add_loading_step(self, target_path: str, format_type: str):
        """Add data loading step"""
        self.steps.append(('load', target_path, format_type))
    
    def execute(self) -> Dict:
        """Execute the ETL pipeline"""
        results = {
            'success': False,
            'records_processed': 0,
            'errors': [],
            'warnings': []
        }
        
        data = []
        
        try:
            for step in self.steps:
                step_type = step[0]
                
                if step_type == 'extract':
                    source_path, format_type = step[1], step[2]
                    if format_type == 'csv':
                        data = self.extractor.extract_csv(source_path)
                    elif format_type == 'json':
                        extracted = self.extractor.extract_json(source_path)
                        data = extracted if isinstance(extracted, list) else [extracted]
                    elif format_type == 'xml':
                        extracted = self.extractor.extract_xml(source_path)
                        data = [extracted]
                    
                elif step_type == 'transform':
                    transform_func = step[1]
                    data = [transform_func(record) for record in data]
                    
                elif step_type == 'validate':
                    validation_func = step[1]
                    validated_data = []
                    for record in data:
                        if validation_func(record):
                            validated_data.append(record)
                        else:
                            results['warnings'].append(f"Record failed validation: {record}")
                    data = validated_data
                    
                elif step_type == 'load':
                    target_path, format_type = step[1], step[2]
                    if format_type == 'csv':
                        success = self.loader.load_to_csv(data, target_path)
                    elif format_type == 'json':
                        success = self.loader.load_to_json(data, target_path)
                    elif format_type == 'sqlite':
                        success = self.loader.load_to_sqlite(data, target_path)
                    
                    if not success:
                        results['errors'].append(f"Failed to load data to {target_path}")
                        return results
            
            results['success'] = True
            results['records_processed'] = len(data)
            
        except Exception as e:
            results['errors'].append(str(e))
            logging.error(f"ETL Pipeline failed: {e}")
        
        return results

# Data Quality Patterns
class DataQualityChecker:
    def __init__(self, data: List[Dict]):
        self.data = data
        self.quality_report = {}
    
    def check_completeness(self) -> Dict:
        """Check for missing values"""
        if not self.data:
            return {}
        
        total_records = len(self.data)
        completeness = {}
        
        for field in self.data[0].keys():
            missing_count = 0
            for record in self.data:
                value = record.get(field)
                if value is None or (isinstance(value, str) and not value.strip()):
                    missing_count += 1
            
            completeness[field] = {
                'missing_count': missing_count,
                'completeness_rate': (total_records - missing_count) / total_records,
                'missing_percentage': (missing_count / total_records) * 100
            }
        
        return completeness
    
    def check_uniqueness(self, key_fields: List[str]) -> Dict:
        """Check for duplicate records"""
        if not key_fields:
            return {}
        
        seen_keys = set()
        duplicates = []
        
        for i, record in enumerate(self.data):
            key_values = tuple(record.get(field, '') for field in key_fields)
            if key_values in seen_keys:
                duplicates.append((i, record))
            else:
                seen_keys.add(key_values)
        
        return {
            'total_records': len(self.data),
            'unique_records': len(seen_keys),
            'duplicate_count': len(duplicates),
            'uniqueness_rate': len(seen_keys) / len(self.data),
            'duplicates': duplicates[:10]  # Show first 10 duplicates
        }
    
    def check_data_types(self, field_types: Dict[str, str]) -> Dict:
        """Check if data matches expected types"""
        type_errors = defaultdict(list)
        
        for i, record in enumerate(self.data):
            for field, expected_type in field_types.items():
                if field in record:
                    value = record[field]
                    is_valid = True
                    
                    if expected_type == 'int':
                        try:
                            int(value)
                        except (ValueError, TypeError):
                            is_valid = False
                    elif expected_type == 'float':
                        try:
                            float(value)
                        except (ValueError, TypeError):
                            is_valid = False
                    elif expected_type == 'date':
                        if not self._is_date(value):
                            is_valid = False
                    elif expected_type == 'email':
                        if not DataValidator.is_email(str(value)):
                            is_valid = False
                    
                    if not is_valid:
                        type_errors[field].append({
                            'record_index': i,
                            'value': value,
                            'expected_type': expected_type
                        })
        
        return dict(type_errors)
    
    def _is_date(self, value: Any) -> bool:
        """Check if value can be parsed as date"""
        transformer = DataTransformer()
        return transformer.parse_date(str(value)) is not None
    
    def generate_quality_report(self, key_fields: List[str] = None, 
                              field_types: Dict[str, str] = None) -> Dict:
        """Generate comprehensive data quality report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_records': len(self.data),
            'completeness': self.check_completeness()
        }
        
        if key_fields:
            report['uniqueness'] = self.check_uniqueness(key_fields)
        
        if field_types:
            report['type_validation'] = self.check_data_types(field_types)
        
        return report

# Example usage and testing
if __name__ == "__main__":
    # Create sample data
    sample_data = [
        {'id': '1', 'name': 'John Doe', 'email': 'john@example.com', 'age': '30', 'salary': '50000'},
        {'id': '2', 'name': 'Jane Smith', 'email': 'jane@example.com', 'age': '25', 'salary': '45000'},
        {'id': '3', 'name': 'Bob Johnson', 'email': 'invalid-email', 'age': 'thirty', 'salary': '60000'},
        {'id': '1', 'name': 'John Doe', 'email': 'john@example.com', 'age': '30', 'salary': '50000'},  # Duplicate
    ]
    
    # Test data quality checker
    quality_checker = DataQualityChecker(sample_data)
    quality_report = quality_checker.generate_quality_report(
        key_fields=['id', 'email'],
        field_types={'age': 'int', 'salary': 'float', 'email': 'email'}
    )
    
    # Test data aggregation
    aggregator = DataAggregator(sample_data)
    salary_by_age = aggregator.aggregate_numeric('age', 'salary', 'avg')
    
    # Test ETL pipeline
    pipeline = ETLPipeline()
    
    # Setup transformation rules
    transformer = DataTransformer()
    transformer.add_transformation_rule('name', lambda x: x.upper())
    transformer.add_validation_rule('email', DataValidator.is_email)
    
    print(f"Quality Report: {quality_report}")
    print(f"Salary by Age: {salary_by_age}")