#coding: utf-8

from urlparse import urlparse
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from httplib import HTTPMessage, HTTPResponse
import socket
from zlib import decompress

from ir_overwrite import *

WWW_DREAM_PRO_INFO = '202.215.80.119'

class lr2irproxy(BaseHTTPRequestHandler):
    '''
    '''
    def create_request(self):
        '''
        create an original HTTP request message with body from class variables.
        '''
        out = '%s %s %s\r\n' % (self.command, self.path, self.request_version)
        out += ''.join(self.headers.headers)
        out += '\r\n'
        out += self.req_body

        return out

    def do_all(self):
        '''
        for all methods, use this handling function.
        '''
        self.req_body = self.rfile.read(int(self.headers.getheader('content-length',0)))
        parsed_path = urlparse(self.path)
        prsd_path = parsed_path.path
        prsd_query = parsed_path.query

        if prsd_path in replace_output:
            # replace whole output
            status,reason,res_msg,res_body = \
                eval('%s.func(prsd_path,prsd_query,self.req_body)' % (replace_output[prsd_path],))
        else:
            # send a request to www.dream-pro.info
            if prsd_path in edit_request:
                # modify http request header or body
                req_msg = eval('%s.func(self.headers,self.req_body)' % (replace_output[prsd_path],))
            else:
                # use default http request header and body by client
                req_msg = self.create_request()

            # socket
            try:
                # because www.dream-pro.info is tlanslated to 127.0.0.1 using hosts' entry,
                # send message to www.dream-pro.info with socket.socket to make
                # http connection
                sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                sock.connect((WWW_DREAM_PRO_INFO,80))
                sock.sendall(req_msg)
            except:
                print 'SocketError'
                return

            res = HTTPResponse(sock)
            res.begin()
            version = res.version
            status = res.status
            reason = res.reason
            res_msg = res.msg
            res_body = res.read()
            res.close()

            compmeth = res_msg.getheader('content-encoding','').lower()
            if compmeth and compmeth.find('identity') != 0 :
                if res_msg.getheader('content-length'):
                    res.msg.__delitem__('content-length')
                offset = 0
                if compmeth.find('gzip') != -1:
                    offset += 47
                res_body = decompress(res_body,offset)
            res_msg['content-encoding'] = 'Identity'

            for h in ('tranfer-encoding','connection'):
                if h in res_msg.keys():
                    res_msg.__delitem__(h)


            if prsd_path in edit_response:
                # modify http response from www.dream-pro.info
                res_msg, res_body = eval('%s.func(prsd_query,res_msg,res_body)' % (edit_response[prsd_path],))

        self.send_response(status,reason)

        for hdr in res_msg:
            self.send_header(hdr,res_msg[hdr])
        self.end_headers()

        self.wfile.write(res_body)
        return

    do_GET  = do_all
    do_POST = do_all

def main():
    server = HTTPServer(('www.dream-pro.info', 80), lr2irproxy)
    print 'Starting server, use <Ctrl-C> to stop'
    try:
        server.serve_forever()
    except:
        pass

if __name__ == '__main__':
    main()