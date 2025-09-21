
"""
Like http.server but accepting CORS

Label Studio needs CORS on dataset resources
"""

import http.server
import os
import sys

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    interface = sys.argv[3] if len(sys.argv) > 3 else 'localhost'

    handler = lambda *args: CORSHTTPRequestHandler(*args, directory=directory)

    with http.server.HTTPServer((interface, port), handler) as httpd:
        print(f"Serving at http://localhost:{port} from {os.path.abspath(directory)}")
        httpd.serve_forever()

if __name__ == "__main__":
    main()
