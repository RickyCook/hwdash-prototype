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
                apipathchunks = vpath.split('/')[2:]

                hwitems = (
                    'all',
                    'bios',
                    'block',
                    'bluetooth',
                    'braille',
                    'bridge',
                    'camera',
                    'cdrom',
                    'chipcard',
                    'cpu',
                    'disk',
                    'dsl',
                    'dvb',
                    'fingerprint',
                    'floppy',
                    'framebuffer',
                    'gfx-card',
                    'hub',
                    'ide',
                    'isapnp',
                    'isdn',
                    'joystick',
                    'keyboard',
                    'memory',
                    'modem',
                    'monitor',
                    'mouse',
                    'netcard',
                    'network',
                    'partition',
                    'pci',
                    'pcmcia',
                    'pcmcia-ctrl',
                    'pppoe',
                    'printer',
                    'scanner',
                    'scsi',
                    'smp',
                    'sound',
                    'storage-ctrl',
                    'sys',
                    'tape',
                    'tv',
                    'usb',
                    'usb-ctrl',
                    'vbe',
                    'wlan',
                    'zip',
                )
                groupings = (
                    'by-index',
                )
                formats = {
                    'txt': 'text/plain',
                    'json': 'application/json',
                }

                format = 'txt'
                hwitem = 'all'
                grouping = 'by-index'

                #
                # Set format (before count for cleaner error output)
                #
                if apipathchunks[-1].find('.') >= 0:
                    apipathchunks[-1], format = apipathchunks[-1].rsplit('.', 2)

                #
                # Count args
                #
                if len(apipathchunks) > 2:
                    self.send_error(404, 'Too many arguments %s' % apipathchunks)
                    return

                #
                # Validate/set chunks
                #
                for chunk in apipathchunks:
                    if chunk in hwitems:
                        hwitem = chunk
                    elif chunk in groupings:
                        grouping = chunk
                    else:
                        self.send_error(404, 'Invalid argument %s' % chunk)
                        return
                if not format in formats.keys():
                    self.send_error(404, 'Invalid format %s' % format)
                    return

                #
                # Can't do anything but basic grouping for txt format
                #
                if format == 'txt' and not grouping == 'by-index':
                    self.send_error(404, '%s grouping is unavailable for txt format. Only by-index is available' % format)
                    return

                b = subprocess.check_output(['/usr/sbin/hwinfo', '--%s' % hwitem])
                self.send_response(200)

                self.send_header('Content-type', formats[format])
                self.end_headers()
                if format == 'txt':
                    self.wfile.write(b)
                    return

                hwinfo = HWInfo(b)
                if format == 'json':
                    self.wfile.write('{status: "failure"}')

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
class HWInfo:
    def __init__(self, bytes):
        self.rawtext = bytes.decode('utf-8')
class HWNode:
    def __init__(self, nodetext):
        self.rawtext = nodetext

server = HTTPServer(('127.0.0.1', 8000), MyRequestHandler)
sockinfo = server.socket.getsockname()
print 'Started on', sockinfo[0], 'port', sockinfo[1]

server.serve_forever()