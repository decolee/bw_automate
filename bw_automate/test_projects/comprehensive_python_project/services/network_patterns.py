"""
Network Programming and API Client Patterns
Testing various network operations, HTTP clients, socket programming
"""

import asyncio
import socket
import ssl
import urllib.request
import urllib.parse
import urllib.error
from urllib.parse import urljoin, urlparse
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Union, Any
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
import logging

# HTTP Client Patterns
class HTTPClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session_headers = {'User-Agent': 'TestClient/1.0'}
    
    def get(self, endpoint: str, params: Dict = None) -> Dict:
        url = urljoin(self.base_url, endpoint)
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"
        
        try:
            request = urllib.request.Request(url, headers=self.session_headers)
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            logging.error(f"HTTP Error {e.code}: {e.reason}")
            raise
        except urllib.error.URLError as e:
            logging.error(f"URL Error: {e.reason}")
            raise
    
    def post(self, endpoint: str, data: Dict) -> Dict:
        url = urljoin(self.base_url, endpoint)
        json_data = json.dumps(data).encode('utf-8')
        
        headers = self.session_headers.copy()
        headers['Content-Type'] = 'application/json'
        
        request = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
        
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            logging.error(f"POST request failed: {e}")
            raise

# Socket Programming Patterns
class SocketServer:
    def __init__(self, host: str = 'localhost', port: int = 8080):
        self.host = host
        self.port = port
        self.socket = None
        
    def start_server(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            logging.info(f"Server listening on {self.host}:{self.port}")
            
            while True:
                client_socket, address = self.socket.accept()
                self.handle_client(client_socket, address)
                
        except KeyboardInterrupt:
            logging.info("Server shutting down...")
        finally:
            if self.socket:
                self.socket.close()
    
    def handle_client(self, client_socket: socket.socket, address: tuple):
        try:
            data = client_socket.recv(1024).decode('utf-8')
            response = f"Echo: {data}"
            client_socket.send(response.encode('utf-8'))
        except Exception as e:
            logging.error(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()

class SocketClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
    
    def send_message(self, message: str) -> str:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.host, self.port))
                sock.send(message.encode('utf-8'))
                response = sock.recv(1024).decode('utf-8')
                return response
        except ConnectionRefusedError:
            logging.error(f"Connection refused to {self.host}:{self.port}")
            raise
        except socket.timeout:
            logging.error("Socket timeout")
            raise

# SSL/TLS Patterns
class SecureHTTPSClient:
    def __init__(self, verify_ssl: bool = True):
        self.verify_ssl = verify_ssl
        
    def secure_get(self, url: str) -> Dict:
        context = ssl.create_default_context()
        if not self.verify_ssl:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
        try:
            request = urllib.request.Request(url)
            with urllib.request.urlopen(request, context=context) as response:
                return {
                    'status': response.getcode(),
                    'headers': dict(response.headers),
                    'data': response.read().decode('utf-8')
                }
        except ssl.SSLError as e:
            logging.error(f"SSL Error: {e}")
            raise

# Async Network Patterns
class AsyncHTTPClient:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    async def async_get(self, url: str) -> Dict:
        # Simulated async HTTP request (would use aiohttp in real scenario)
        await asyncio.sleep(0.1)  # Simulate network delay
        
        loop = asyncio.get_event_loop()
        request = urllib.request.Request(url)
        
        try:
            response = await loop.run_in_executor(
                None, 
                lambda: urllib.request.urlopen(request, timeout=self.timeout)
            )
            
            with response:
                return {
                    'url': url,
                    'status': response.getcode(),
                    'data': response.read().decode('utf-8')
                }
        except Exception as e:
            logging.error(f"Async GET failed for {url}: {e}")
            raise
    
    async def batch_requests(self, urls: List[str]) -> List[Dict]:
        tasks = [self.async_get(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

# Web Scraping Patterns
class WebScraper:
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; WebScraper/1.0)'
        }
    
    def scrape_page(self, url: str) -> Dict:
        time.sleep(self.delay)  # Rate limiting
        
        request = urllib.request.Request(url, headers=self.headers)
        
        try:
            with urllib.request.urlopen(request) as response:
                html_content = response.read().decode('utf-8')
                
                # Simple HTML parsing (would use BeautifulSoup in real scenario)
                title_start = html_content.find('<title>')
                title_end = html_content.find('</title>')
                title = html_content[title_start+7:title_end] if title_start != -1 and title_end != -1 else "No title"
                
                return {
                    'url': url,
                    'title': title,
                    'content_length': len(html_content),
                    'status': response.getcode()
                }
        except Exception as e:
            logging.error(f"Scraping failed for {url}: {e}")
            return {'url': url, 'error': str(e)}
    
    def scrape_multiple(self, urls: List[str], max_workers: int = 5) -> List[Dict]:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(self.scrape_page, urls))
        return results

# API Rate Limiting Patterns
class RateLimitedClient:
    def __init__(self, requests_per_second: float = 1.0):
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        self.lock = threading.Lock()
    
    def make_request(self, url: str) -> Dict:
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
        
        request = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(request) as response:
                return {
                    'status': response.getcode(),
                    'data': response.read().decode('utf-8')
                }
        except Exception as e:
            logging.error(f"Rate limited request failed: {e}")
            raise

# Network Configuration Patterns
class NetworkConfig:
    def __init__(self):
        self.proxy_settings = {}
        self.timeout_settings = {}
        self.retry_settings = {}
    
    def configure_proxy(self, proxy_url: str, username: str = None, password: str = None):
        self.proxy_settings = {
            'url': proxy_url,
            'username': username,
            'password': password
        }
        
        # Configure urllib to use proxy
        if username and password:
            proxy_handler = urllib.request.ProxyHandler({
                'http': f'http://{username}:{password}@{proxy_url}',
                'https': f'https://{username}:{password}@{proxy_url}'
            })
        else:
            proxy_handler = urllib.request.ProxyHandler({
                'http': proxy_url,
                'https': proxy_url
            })
        
        opener = urllib.request.build_opener(proxy_handler)
        urllib.request.install_opener(opener)
    
    def set_timeouts(self, connect_timeout: int = 10, read_timeout: int = 30):
        self.timeout_settings = {
            'connect': connect_timeout,
            'read': read_timeout
        }
        
        # Configure socket default timeout
        socket.setdefaulttimeout(connect_timeout)

# REST API Client Pattern
class RESTAPIClient:
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.default_headers = {'Content-Type': 'application/json'}
        
        if api_key:
            self.default_headers['Authorization'] = f'Bearer {api_key}'
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"
        
        request_data = None
        if data:
            request_data = json.dumps(data).encode('utf-8')
        
        request = urllib.request.Request(
            url, 
            data=request_data, 
            headers=self.default_headers, 
            method=method
        )
        
        try:
            with urllib.request.urlopen(request) as response:
                response_data = response.read().decode('utf-8')
                return {
                    'status': response.getcode(),
                    'data': json.loads(response_data) if response_data else None
                }
        except urllib.error.HTTPError as e:
            error_response = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
            return {
                'status': e.code,
                'error': error_response
            }
    
    def get(self, endpoint: str, params: Dict = None) -> Dict:
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict) -> Dict:
        return self._make_request('POST', endpoint, data=data)
    
    def put(self, endpoint: str, data: Dict) -> Dict:
        return self._make_request('PUT', endpoint, data=data)
    
    def delete(self, endpoint: str) -> Dict:
        return self._make_request('DELETE', endpoint)

# Network Utility Functions
def check_connectivity(host: str, port: int, timeout: int = 5) -> bool:
    """Check if a host:port is reachable"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            return result == 0
    except Exception:
        return False

def get_local_ip() -> str:
    """Get local IP address"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(('8.8.8.8', 80))
            return sock.getsockname()[0]
    except Exception:
        return '127.0.0.1'

def parse_url_components(url: str) -> Dict:
    """Parse URL into components"""
    parsed = urlparse(url)
    return {
        'scheme': parsed.scheme,
        'netloc': parsed.netloc,
        'path': parsed.path,
        'params': parsed.params,
        'query': parsed.query,
        'fragment': parsed.fragment,
        'hostname': parsed.hostname,
        'port': parsed.port,
        'username': parsed.username,
        'password': parsed.password
    }

# Example usage and testing patterns
if __name__ == "__main__":
    # HTTP Client testing
    client = HTTPClient("https://api.example.com")
    
    # Socket programming testing
    server = SocketServer('localhost', 8080)
    client_sock = SocketClient('localhost', 8080)
    
    # Async patterns testing
    async def test_async():
        async_client = AsyncHTTPClient()
        urls = ["https://example.com", "https://google.com"]
        results = await async_client.batch_requests(urls)
        return results
    
    # Web scraping testing
    scraper = WebScraper(delay=2.0)
    urls_to_scrape = ["https://example.com", "https://python.org"]
    scrape_results = scraper.scrape_multiple(urls_to_scrape)
    
    # Rate limiting testing
    rate_limited = RateLimitedClient(requests_per_second=0.5)
    
    # Network utilities testing
    connectivity = check_connectivity('google.com', 80)
    local_ip = get_local_ip()
    url_parts = parse_url_components('https://user:pass@example.com:8080/path?query=1#fragment')
    
    print(f"Connectivity test: {connectivity}")
    print(f"Local IP: {local_ip}")
    print(f"URL components: {url_parts}")