import http.server
import socketserver
import requests
import urllib.parse
import os

PORT = 8000
DIRECTORY = "."

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve filteredSpotData.json from data directory (sibling to viewer)
        if self.path == '/filteredSpotData.json':
            try:
                # Resolve path relative to this script
                current_dir = os.path.dirname(os.path.abspath(__file__))
                data_path = os.path.join(current_dir, '..', 'data', 'filteredSpotData.json')
                
                with open(data_path, 'rb') as f:
                    content = f.read()
                    
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            except FileNotFoundError:
                self.send_error(404, "Data file not found")
                return
            except Exception as e:
                self.send_error(500, str(e))
                return
            
        # Proxy endpoint
        if self.path.startswith('/proxy'):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            target_url = params.get('url', [None])[0]

            if not target_url:
                self.send_error(400, "Missing 'url' parameter")
                return

            try:
                # Headers to mimic a valid request
                headers = {
                    "Referer": "https://www.surfline.com/",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                
                # Stream the content
                resp = requests.get(target_url, headers=headers, stream=True)
                
                self.send_response(resp.status_code)
                for k, v in resp.headers.items():
                    # Forward relevant headers, exclude hop-by-hop
                    if k.lower() not in ['connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailer', 'transfer-encoding', 'upgrade', 'content-encoding', 'content-length']:
                        self.send_header(k, v)
                
                self.end_headers()
                
                for chunk in resp.iter_content(chunk_size=8192):
                    self.wfile.write(chunk)
                    
            except Exception as e:
                print(f"Proxy error: {e}")
                self.send_error(500, str(e))
            return

        # Default behavior for static files in the current directory (viewer)
        # Handle root alias
        if self.path == '/':
            self.path = '/index.html'
            
        return super().do_GET()

print(f"Serving on port {PORT}")
with http.server.ThreadingHTTPServer(("", PORT), ProxyHandler) as httpd:
    httpd.serve_forever()
