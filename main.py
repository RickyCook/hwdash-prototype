#!/usr/bin/python2.7

import sys, os, io, subprocess
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

class MyRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            vpath = self.path
            if self.path in ('/', '/index.htm'):
                vpath = '/static/index.htm'

            if vpath.startswith('/api/'):
                apipath = vpath.lstrip('/api')
                b = subprocess.check_output('/usr/sbin/hwinfo')
                self.send_response(200)

                if vpath.endswith('.json'):
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write('{status: "failure"}')
                else:
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b)

                return

            if vpath.startswith('/static/'):
                path = os.path.abspath('./' + vpath)
                if not path.startswith(os.getcwd() + '/static/'):
                    self.send_error(403, 'Outside of static directory %s' % vpath)
                    return
                if not os.path.isfile(path):
                    self.send_error(403, 'Not a file %s' % vpath)
                    return

                with io.open(path, 'r') as f:
                    b = f.read(1)
                    while(b):
                        self.wfile.write(b)
                        b = f.read(1)

                return

            else:
                self.send_error(404, 'Route Not Found %s' % self.path)

        except Exception as e:
            self.send_error(500, 'Exception: %s' % e)

server = HTTPServer(('127.0.0.1', 8000), MyRequestHandler)
sockinfo = server.socket.getsockname()
print 'Started on', sockinfo[0], 'port', sockinfo[1]

server.serve_forever()