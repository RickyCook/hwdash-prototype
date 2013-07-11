#!/usr/bin/python2.7

import sys, os, io, subprocess, traceback, re, unicodedata, json, shutil
import StringIO
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

class MyRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            pathchunks = filter(None, self.path.split('/'))
            vpathchunks = list(pathchunks)

            validroots = ('api', 'static')
            if len(vpathchunks) == 0 or vpathchunks[0] in ('index.htm','index.html'):
                vpathchunks = ('static', 'index.htm')

            if not vpathchunks[0] in validroots:
                chunkinfo = self.get_chunk_info(vpathchunks)
                if not chunkinfo:
                    return
                if chunkinfo['format'] in ('html', 'htm'):
                    vpathchunks = ('static', 'index.htm')

            if len(vpathchunks) and vpathchunks[0] == 'api':
                chunkinfo = self.get_chunk_info(vpathchunks[1:])
                if not chunkinfo:
                    return

                b = subprocess.check_output(['/usr/sbin/hwinfo', '--%s' % chunkinfo['hwitem']])
                self.send_response(200)

                self.send_header('Content-type', chunkinfo['formatmime'])
                self.end_headers()
                if chunkinfo['format'] == 'txt':
                    self.wfile.write(b)
                    return

                hwinfo = HWInfo(b)
                if chunkinfo['format'] == 'json':
                    # for node in hwinfo.get_nodes():
                    #     node.get_attributes()
                    # self.wfile.write('{status: "failure"}')
                    self.wfile.write(json.dumps(hwinfo.as_dict()))

                return

            elif len(vpathchunks) and vpathchunks[0] == 'static':
                vpath = '/'.join(vpathchunks)
                abspath = os.path.abspath('./' + vpath)
                if not abspath.startswith(os.getcwd() + '/static/'):
                    self.send_error(403, 'Outside of static directory %s' % vpath)
                    return
                if not os.path.isfile(abspath):
                    self.send_error(403, 'Not a file %s' % vpath)
                    return

                with io.open(abspath, 'rb') as f:
                    shutil.copyfileobj(f, self.wfile)

                return

            else:
                self.send_error(404, 'Route Not Found %s' % self.path)

        except:
            self.send_error(500, 'Exception: %s' % traceback.format_exc())
    def get_chunk_info(self, chunks):
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
            'htm': 'text/html',
            'html': 'text/html',
        }

        format = 'txt'
        hwitem = 'all'
        grouping = 'by-index'

        #
        # Set format (before count for cleaner error output)
        #
        if len(chunks) and chunks[-1].find('.') >= 0:
            chunks[-1], format = chunks[-1].rsplit('.', 2)

        #
        # Count args
        #
        if len(chunks) > 2:
            self.send_error(404, 'Too many arguments %s' % chunks)
            return False

        #
        # Validate/set chunks
        #
        for chunk in chunks:
            if chunk in hwitems:
                hwitem = chunk
            elif chunk in groupings:
                grouping = chunk
            else:
                self.send_error(404, 'Invalid argument %s' % chunk)
                return
        if not format in formats.keys():
            self.send_error(404, 'Invalid format %s' % format)
            return False

        #
        # Can't do anything but basic grouping for txt format
        #
        if format == 'txt' and not grouping == 'by-index':
            self.send_error(404, '%s grouping is unavailable for txt format. Only by-index is available' % format)
            return False

        return {
            'format':     format,
            'formatmime': formats[format],
            'hwitem':     hwitem,
            'grouping':   grouping,
        }
class HWInfo:
    def __init__(self, bytes):
        self.rawtext = bytes.decode('utf-8')
        self.nodes   = None
    def get_nodes(self):
        if self.nodes is None:
            self.do_parse()
        return self.nodes
    def do_parse(self):
        buf = StringIO.StringIO(self.rawtext)
        self.nodes = []
        nodetext = ''
        for line in buf:
            #
            # New node
            #
            if not line.startswith('  ') and not line.strip() == '':
                self.nodes.append(HWNode(nodetext))
                nodetext = ''
            nodetext += line

        self.nodes.append(HWNode(nodetext))

        return
    def as_dict(self):
        return {
            'nodes': [node.as_dict() for node in self.get_nodes()],
        }

class HWNode:
    def __init__(self, nodetext):
        self.rawtext    = nodetext
        self.index      = None
        self.name       = None
        self.created    = None
        self.attributes = None
    def get_attributes(self):
        if self.attributes is None:
            self.do_parse()
        return self.attributes
    def do_parse(self):
        buf = StringIO.StringIO(self.rawtext)
        self.attributes = {}
        createdre = re.compile('^  \[Created at (.+)\]$')
        currentsection = None
        for line in buf:
            #
            # Node details line or property
            #
            if not line.startswith('  ') and not line.strip() == '':
                self.index, self.name = line.strip().split(': ', 1)
            elif createdre.match(line):
                self.created = createdre.match(line).group(1).strip()
            elif not line.strip() == '':
                key, value = line.split(':', 1)

                #
                # Reset section if not indented
                #
                if not key.startswith('    '):
                    currentsection = None

                #
                # Strip whitespace
                #
                key = key.strip()
                value = value.strip()

                #
                # No values are sections
                #
                if value == '':
                    # SECTION
                    currentsection = key
                    self.attributes[key] = {}
                else:
                    # ATTRIBUTE

                    #
                    # What section? (root if none)
                    #
                    section = self.attributes
                    if currentsection:
                        section = section[currentsection]

                    #
                    # Create/append to list if required
                    #
                    if key in section:
                        if not isinstance(section[key], list):
                            section[key] = [section[key]]
                        section[key].append(value)
                    else:
                        section[key] = value
        return

    def as_dict(self):
        self.get_attributes()
        return {
            'index': self.index,
            'name': self.name,
            'created': self.created,
            'attributes': self.attributes,
        }

server = HTTPServer(('127.0.0.1', 8000), MyRequestHandler)
sockinfo = server.socket.getsockname()
print 'Started on', sockinfo[0], 'port', sockinfo[1]

server.serve_forever()