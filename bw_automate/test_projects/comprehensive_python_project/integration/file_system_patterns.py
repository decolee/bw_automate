"""
File System and I/O Patterns
Testing file operations, path manipulation, serialization, compression
"""

import os
import sys
import pathlib
import shutil
import tempfile
import json
import pickle
import csv
import configparser
import zipfile
import tarfile
import gzip
import hashlib
import mimetypes
import glob
import fnmatch
from typing import List, Dict, Any, Optional, Union, Iterator, BinaryIO, TextIO
from datetime import datetime, timedelta
import logging
import stat
import time
import re
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue

# File System Navigation Patterns
class FileSystemNavigator:
    def __init__(self, root_path: str = "."):
        self.root_path = pathlib.Path(root_path).resolve()
        self.current_path = self.root_path
        
    def list_directory(self, path: str = None, pattern: str = "*", 
                      include_hidden: bool = False) -> List[Dict]:
        """List directory contents with metadata"""
        target_path = pathlib.Path(path) if path else self.current_path
        
        try:
            entries = []
            for item in target_path.iterdir():
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                if not fnmatch.fnmatch(item.name, pattern):
                    continue
                
                stat_info = item.stat()
                entries.append({
                    'name': item.name,
                    'path': str(item),
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': stat_info.st_size,
                    'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    'created': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                    'permissions': oct(stat_info.st_mode)[-3:],
                    'is_symlink': item.is_symlink(),
                    'parent': str(item.parent)
                })
            
            return sorted(entries, key=lambda x: (x['type'] == 'file', x['name'].lower()))
            
        except PermissionError:
            logging.error(f"Permission denied accessing {target_path}")
            return []
        except Exception as e:
            logging.error(f"Error listing directory {target_path}: {e}")
            return []
    
    def find_files(self, pattern: str, search_path: str = None, 
                   recursive: bool = True, max_depth: int = None) -> List[str]:
        """Find files matching pattern"""
        search_root = pathlib.Path(search_path) if search_path else self.current_path
        matches = []
        
        try:
            if recursive:
                if max_depth:
                    # Custom recursive search with depth limit
                    matches = self._find_files_recursive(search_root, pattern, 0, max_depth)
                else:
                    # Use glob for unlimited recursive search
                    matches = [str(p) for p in search_root.rglob(pattern)]
            else:
                matches = [str(p) for p in search_root.glob(pattern)]
                
        except Exception as e:
            logging.error(f"Error finding files: {e}")
        
        return matches
    
    def _find_files_recursive(self, path: pathlib.Path, pattern: str, 
                             current_depth: int, max_depth: int) -> List[str]:
        """Recursive file search with depth limit"""
        matches = []
        
        if current_depth > max_depth:
            return matches
        
        try:
            for item in path.iterdir():
                if item.is_file() and fnmatch.fnmatch(item.name, pattern):
                    matches.append(str(item))
                elif item.is_dir() and current_depth < max_depth:
                    matches.extend(
                        self._find_files_recursive(item, pattern, current_depth + 1, max_depth)
                    )
        except PermissionError:
            pass  # Skip directories we can't access
        
        return matches
    
    def get_directory_size(self, path: str = None) -> Dict:
        """Calculate directory size recursively"""
        target_path = pathlib.Path(path) if path else self.current_path
        
        total_size = 0
        file_count = 0
        dir_count = 0
        
        try:
            for item in target_path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
                    file_count += 1
                elif item.is_dir():
                    dir_count += 1
                    
        except Exception as e:
            logging.error(f"Error calculating directory size: {e}")
        
        return {
            'path': str(target_path),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_count': file_count,
            'directory_count': dir_count
        }
    
    def create_directory_tree(self, structure: Dict, base_path: str = None):
        """Create directory structure from nested dict"""
        base = pathlib.Path(base_path) if base_path else self.current_path
        
        def create_tree(tree: Dict, current_path: pathlib.Path):
            for name, content in tree.items():
                item_path = current_path / name
                
                if isinstance(content, dict):
                    # It's a directory
                    item_path.mkdir(exist_ok=True)
                    create_tree(content, item_path)
                else:
                    # It's a file
                    item_path.parent.mkdir(parents=True, exist_ok=True)
                    if isinstance(content, str):
                        item_path.write_text(content, encoding='utf-8')
                    elif isinstance(content, bytes):
                        item_path.write_bytes(content)
        
        try:
            create_tree(structure, base)
        except Exception as e:
            logging.error(f"Error creating directory tree: {e}")

# File I/O Patterns
class FileManager:
    def __init__(self):
        self.encoding = 'utf-8'
        self.buffer_size = 8192
        
    def read_file(self, file_path: str, mode: str = 'text', 
                  encoding: str = None) -> Union[str, bytes, List[str]]:
        """Read file with various modes"""
        path = pathlib.Path(file_path)
        encoding = encoding or self.encoding
        
        try:
            if mode == 'text':
                return path.read_text(encoding=encoding)
            elif mode == 'binary':
                return path.read_bytes()
            elif mode == 'lines':
                with path.open('r', encoding=encoding) as f:
                    return f.readlines()
            elif mode == 'lines_stripped':
                with path.open('r', encoding=encoding) as f:
                    return [line.strip() for line in f]
            else:
                raise ValueError(f"Unknown mode: {mode}")
                
        except Exception as e:
            logging.error(f"Error reading file {file_path}: {e}")
            raise
    
    def write_file(self, file_path: str, content: Union[str, bytes, List[str]], 
                   mode: str = 'text', encoding: str = None, append: bool = False):
        """Write file with various modes"""
        path = pathlib.Path(file_path)
        encoding = encoding or self.encoding
        
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if mode == 'text':
                if append:
                    with path.open('a', encoding=encoding) as f:
                        f.write(content)
                else:
                    path.write_text(content, encoding=encoding)
            elif mode == 'binary':
                if append:
                    with path.open('ab') as f:
                        f.write(content)
                else:
                    path.write_bytes(content)
            elif mode == 'lines':
                open_mode = 'a' if append else 'w'
                with path.open(open_mode, encoding=encoding) as f:
                    for line in content:
                        f.write(line if line.endswith('\n') else line + '\n')
            else:
                raise ValueError(f"Unknown mode: {mode}")
                
        except Exception as e:
            logging.error(f"Error writing file {file_path}: {e}")
            raise
    
    def copy_file(self, source: str, destination: str, 
                  preserve_metadata: bool = True) -> bool:
        """Copy file with options"""
        try:
            if preserve_metadata:
                shutil.copy2(source, destination)
            else:
                shutil.copy(source, destination)
            return True
        except Exception as e:
            logging.error(f"Error copying file {source} to {destination}: {e}")
            return False
    
    def move_file(self, source: str, destination: str) -> bool:
        """Move/rename file"""
        try:
            shutil.move(source, destination)
            return True
        except Exception as e:
            logging.error(f"Error moving file {source} to {destination}: {e}")
            return False
    
    def delete_file(self, file_path: str, secure: bool = False) -> bool:
        """Delete file with optional secure deletion"""
        path = pathlib.Path(file_path)
        
        try:
            if secure and path.is_file():
                # Overwrite file with random data before deletion
                file_size = path.stat().st_size
                with path.open('r+b') as f:
                    for _ in range(3):  # 3 passes
                        f.seek(0)
                        f.write(os.urandom(file_size))
                        f.flush()
                        os.fsync(f.fileno())
            
            path.unlink()
            return True
        except Exception as e:
            logging.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Dict:
        """Get comprehensive file information"""
        path = pathlib.Path(file_path)
        
        try:
            stat_info = path.stat()
            
            # Calculate file hash
            file_hash = self.calculate_file_hash(file_path)
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(str(path))
            
            return {
                'path': str(path.resolve()),
                'name': path.name,
                'stem': path.stem,
                'suffix': path.suffix,
                'size_bytes': stat_info.st_size,
                'size_mb': round(stat_info.st_size / (1024 * 1024), 4),
                'created': datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                'accessed': datetime.fromtimestamp(stat_info.st_atime).isoformat(),
                'permissions': oct(stat_info.st_mode)[-3:],
                'is_symlink': path.is_symlink(),
                'mime_type': mime_type,
                'hash_md5': file_hash,
                'parent_directory': str(path.parent)
            }
            
        except Exception as e:
            logging.error(f"Error getting file info for {file_path}: {e}")
            return {}
    
    def calculate_file_hash(self, file_path: str, algorithm: str = 'md5') -> str:
        """Calculate file hash"""
        hash_func = getattr(hashlib, algorithm)()
        
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(self.buffer_size):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            logging.error(f"Error calculating hash for {file_path}: {e}")
            return ""

# Serialization Patterns
class DataSerializer:
    def __init__(self):
        self.formats = ['json', 'pickle', 'csv']
        
    def serialize_to_json(self, data: Any, file_path: str, 
                         indent: int = 2, ensure_ascii: bool = False):
        """Serialize data to JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii, 
                         default=self._json_serializer)
        except Exception as e:
            logging.error(f"Error serializing to JSON: {e}")
            raise
    
    def deserialize_from_json(self, file_path: str) -> Any:
        """Deserialize data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error deserializing from JSON: {e}")
            raise
    
    def serialize_to_pickle(self, data: Any, file_path: str, protocol: int = None):
        """Serialize data to pickle file"""
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(data, f, protocol=protocol)
        except Exception as e:
            logging.error(f"Error serializing to pickle: {e}")
            raise
    
    def deserialize_from_pickle(self, file_path: str) -> Any:
        """Deserialize data from pickle file"""
        try:
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logging.error(f"Error deserializing from pickle: {e}")
            raise
    
    def serialize_to_csv(self, data: List[Dict], file_path: str, 
                        delimiter: str = ',', quoting: int = csv.QUOTE_MINIMAL):
        """Serialize list of dictionaries to CSV file"""
        if not data:
            return
        
        try:
            fieldnames = list(data[0].keys())
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, 
                                       delimiter=delimiter, quoting=quoting)
                writer.writeheader()
                writer.writerows(data)
        except Exception as e:
            logging.error(f"Error serializing to CSV: {e}")
            raise
    
    def deserialize_from_csv(self, file_path: str, delimiter: str = ',') -> List[Dict]:
        """Deserialize CSV file to list of dictionaries"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                return list(reader)
        except Exception as e:
            logging.error(f"Error deserializing from CSV: {e}")
            raise
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for non-serializable objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, pathlib.Path):
            return str(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)

# Compression Patterns
class CompressionManager:
    def __init__(self):
        self.supported_formats = ['zip', 'tar', 'tar.gz', 'tar.bz2', 'gz']
    
    def create_zip_archive(self, source_path: str, archive_path: str, 
                          compression_level: int = 6) -> bool:
        """Create ZIP archive"""
        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED, 
                               compresslevel=compression_level) as zf:
                source = pathlib.Path(source_path)
                
                if source.is_file():
                    zf.write(source, source.name)
                elif source.is_dir():
                    for file_path in source.rglob('*'):
                        if file_path.is_file():
                            arc_name = file_path.relative_to(source.parent)
                            zf.write(file_path, arc_name)
            return True
        except Exception as e:
            logging.error(f"Error creating ZIP archive: {e}")
            return False
    
    def extract_zip_archive(self, archive_path: str, extract_path: str) -> bool:
        """Extract ZIP archive"""
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(extract_path)
            return True
        except Exception as e:
            logging.error(f"Error extracting ZIP archive: {e}")
            return False
    
    def create_tar_archive(self, source_path: str, archive_path: str, 
                          compression: str = None) -> bool:
        """Create TAR archive with optional compression"""
        mode = 'w'
        if compression == 'gz':
            mode = 'w:gz'
        elif compression == 'bz2':
            mode = 'w:bz2'
        
        try:
            with tarfile.open(archive_path, mode) as tf:
                source = pathlib.Path(source_path)
                tf.add(source, arcname=source.name)
            return True
        except Exception as e:
            logging.error(f"Error creating TAR archive: {e}")
            return False
    
    def extract_tar_archive(self, archive_path: str, extract_path: str) -> bool:
        """Extract TAR archive"""
        try:
            with tarfile.open(archive_path, 'r:*') as tf:
                tf.extractall(extract_path)
            return True
        except Exception as e:
            logging.error(f"Error extracting TAR archive: {e}")
            return False
    
    def compress_file_gzip(self, file_path: str, compressed_path: str = None) -> str:
        """Compress single file with gzip"""
        source_path = pathlib.Path(file_path)
        if compressed_path is None:
            compressed_path = str(source_path) + '.gz'
        
        try:
            with open(source_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return compressed_path
        except Exception as e:
            logging.error(f"Error compressing file with gzip: {e}")
            raise
    
    def decompress_file_gzip(self, compressed_path: str, output_path: str = None) -> str:
        """Decompress gzip file"""
        if output_path is None:
            compressed_path_obj = pathlib.Path(compressed_path)
            if compressed_path_obj.suffix == '.gz':
                output_path = str(compressed_path_obj.with_suffix(''))
            else:
                output_path = compressed_path + '.decompressed'
        
        try:
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return output_path
        except Exception as e:
            logging.error(f"Error decompressing gzip file: {e}")
            raise

# Configuration File Patterns
class ConfigManager:
    def __init__(self):
        self.config_formats = ['ini', 'json', 'env']
        
    def read_ini_config(self, file_path: str) -> Dict:
        """Read INI configuration file"""
        config = configparser.ConfigParser()
        try:
            config.read(file_path, encoding='utf-8')
            return {section: dict(config[section]) for section in config.sections()}
        except Exception as e:
            logging.error(f"Error reading INI config: {e}")
            return {}
    
    def write_ini_config(self, config_data: Dict, file_path: str):
        """Write INI configuration file"""
        config = configparser.ConfigParser()
        
        for section_name, section_data in config_data.items():
            config[section_name] = section_data
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                config.write(f)
        except Exception as e:
            logging.error(f"Error writing INI config: {e}")
            raise
    
    def read_env_file(self, file_path: str) -> Dict[str, str]:
        """Read environment file (.env format)"""
        env_vars = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            # Remove quotes if present
                            value = value.strip('"\'')
                            env_vars[key.strip()] = value
            return env_vars
        except Exception as e:
            logging.error(f"Error reading env file: {e}")
            return {}
    
    def write_env_file(self, env_vars: Dict[str, str], file_path: str):
        """Write environment file (.env format)"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for key, value in env_vars.items():
                    # Quote values that contain spaces
                    if ' ' in value:
                        f.write(f'{key}="{value}"\n')
                    else:
                        f.write(f'{key}={value}\n')
        except Exception as e:
            logging.error(f"Error writing env file: {e}")
            raise

# Temporary File Patterns
class TempFileManager:
    def __init__(self):
        self.temp_files = []
        self.temp_dirs = []
        
    @contextmanager
    def temporary_file(self, suffix: str = '', prefix: str = 'tmp', 
                      mode: str = 'w+', delete: bool = True):
        """Context manager for temporary file"""
        temp_file = tempfile.NamedTemporaryFile(
            mode=mode, suffix=suffix, prefix=prefix, delete=delete
        )
        
        if not delete:
            self.temp_files.append(temp_file.name)
        
        try:
            yield temp_file
        finally:
            if not delete and hasattr(temp_file, 'close'):
                temp_file.close()
    
    @contextmanager
    def temporary_directory(self, suffix: str = '', prefix: str = 'tmp', 
                           cleanup: bool = True):
        """Context manager for temporary directory"""
        temp_dir = tempfile.mkdtemp(suffix=suffix, prefix=prefix)
        
        if not cleanup:
            self.temp_dirs.append(temp_dir)
        
        try:
            yield temp_dir
        finally:
            if cleanup:
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def create_temp_file_with_content(self, content: Union[str, bytes], 
                                     suffix: str = '', encoding: str = 'utf-8') -> str:
        """Create temporary file with specific content"""
        if isinstance(content, str):
            mode = 'w'
        else:
            mode = 'wb'
            encoding = None
        
        temp_file = tempfile.NamedTemporaryFile(
            mode=mode, suffix=suffix, delete=False, encoding=encoding
        )
        
        try:
            temp_file.write(content)
            temp_file.flush()
            self.temp_files.append(temp_file.name)
            return temp_file.name
        finally:
            temp_file.close()
    
    def cleanup_temp_files(self):
        """Clean up all tracked temporary files and directories"""
        for file_path in self.temp_files:
            try:
                pathlib.Path(file_path).unlink()
            except Exception:
                pass
        
        for dir_path in self.temp_dirs:
            try:
                shutil.rmtree(dir_path, ignore_errors=True)
            except Exception:
                pass
        
        self.temp_files.clear()
        self.temp_dirs.clear()
    
    def __del__(self):
        """Cleanup on object destruction"""
        self.cleanup_temp_files()

# File Watching Patterns (simulated)
class FileWatcher:
    def __init__(self, watch_path: str):
        self.watch_path = pathlib.Path(watch_path)
        self.callbacks = []
        self.watching = False
        self.watch_thread = None
        self.file_states = {}
        
    def add_callback(self, callback: Callable):
        """Add callback for file changes"""
        self.callbacks.append(callback)
    
    def start_watching(self, poll_interval: float = 1.0):
        """Start watching for file changes"""
        if self.watching:
            return
        
        self.watching = True
        self._scan_directory()
        
        self.watch_thread = threading.Thread(
            target=self._watch_loop,
            args=(poll_interval,),
            daemon=True
        )
        self.watch_thread.start()
    
    def stop_watching(self):
        """Stop watching for file changes"""
        self.watching = False
        if self.watch_thread:
            self.watch_thread.join(timeout=2.0)
    
    def _scan_directory(self):
        """Scan directory and record file states"""
        if not self.watch_path.exists():
            return
        
        for file_path in self.watch_path.rglob('*'):
            if file_path.is_file():
                try:
                    stat_info = file_path.stat()
                    self.file_states[str(file_path)] = {
                        'mtime': stat_info.st_mtime,
                        'size': stat_info.st_size
                    }
                except Exception:
                    pass
    
    def _watch_loop(self, poll_interval: float):
        """Main watching loop"""
        while self.watching:
            try:
                self._check_for_changes()
                time.sleep(poll_interval)
            except Exception as e:
                logging.error(f"Error in file watching loop: {e}")
    
    def _check_for_changes(self):
        """Check for file changes"""
        if not self.watch_path.exists():
            return
        
        current_files = set()
        
        for file_path in self.watch_path.rglob('*'):
            if file_path.is_file():
                file_str = str(file_path)
                current_files.add(file_str)
                
                try:
                    stat_info = file_path.stat()
                    current_state = {
                        'mtime': stat_info.st_mtime,
                        'size': stat_info.st_size
                    }
                    
                    if file_str not in self.file_states:
                        # New file
                        self._notify_callbacks('created', file_str)
                        self.file_states[file_str] = current_state
                    elif self.file_states[file_str] != current_state:
                        # Modified file
                        self._notify_callbacks('modified', file_str)
                        self.file_states[file_str] = current_state
                        
                except Exception:
                    pass
        
        # Check for deleted files
        deleted_files = set(self.file_states.keys()) - current_files
        for deleted_file in deleted_files:
            self._notify_callbacks('deleted', deleted_file)
            del self.file_states[deleted_file]
    
    def _notify_callbacks(self, event_type: str, file_path: str):
        """Notify all callbacks of file change event"""
        event = {
            'type': event_type,
            'path': file_path,
            'timestamp': datetime.now().isoformat()
        }
        
        for callback in self.callbacks:
            try:
                callback(event)
            except Exception as e:
                logging.error(f"Error in file watcher callback: {e}")

# Example usage and testing
if __name__ == "__main__":
    print("Testing File System Patterns...")
    
    # Test file system navigation
    navigator = FileSystemNavigator()
    current_dir_contents = navigator.list_directory(pattern="*.py")
    print(f"Found {len(current_dir_contents)} Python files in current directory")
    
    # Test file manager
    file_manager = FileManager()
    
    # Create test file
    test_content = "This is a test file\nwith multiple lines\nfor testing purposes."
    test_file_path = "test_file.txt"
    
    file_manager.write_file(test_file_path, test_content)
    
    # Read test file
    read_content = file_manager.read_file(test_file_path)
    print(f"File content matches: {read_content == test_content}")
    
    # Get file info
    file_info = file_manager.get_file_info(test_file_path)
    print(f"File size: {file_info.get('size_bytes', 0)} bytes")
    
    # Test serialization
    serializer = DataSerializer()
    test_data = {
        'name': 'Test Data',
        'values': [1, 2, 3, 4, 5],
        'metadata': {'created': datetime.now().isoformat()}
    }
    
    json_file = "test_data.json"
    serializer.serialize_to_json(test_data, json_file)
    loaded_data = serializer.deserialize_from_json(json_file)
    print(f"JSON serialization successful: {loaded_data['name'] == test_data['name']}")
    
    # Test compression
    compression_manager = CompressionManager()
    
    # Create zip archive
    zip_path = "test_archive.zip"
    success = compression_manager.create_zip_archive(test_file_path, zip_path)
    print(f"ZIP archive created: {success}")
    
    # Test temporary files
    temp_manager = TempFileManager()
    
    with temp_manager.temporary_file(suffix='.txt') as temp_file:
        temp_file.write("Temporary content")
        temp_file.flush()
        print(f"Temporary file created: {temp_file.name}")
    
    # Test file watcher (brief test)
    def file_change_handler(event):
        print(f"File {event['type']}: {event['path']}")
    
    watcher = FileWatcher('.')
    watcher.add_callback(file_change_handler)
    watcher.start_watching(poll_interval=0.5)
    
    # Create a test file to trigger watcher
    time.sleep(1)
    with open('watcher_test.txt', 'w') as f:
        f.write('test')
    
    time.sleep(2)  # Let watcher detect the change
    watcher.stop_watching()
    
    # Cleanup
    for file_to_remove in [test_file_path, json_file, zip_path, 'watcher_test.txt']:
        try:
            pathlib.Path(file_to_remove).unlink()
        except FileNotFoundError:
            pass
    
    temp_manager.cleanup_temp_files()
    
    print("File system patterns testing completed!")