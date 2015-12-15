#coding: utf-8

'''
send/recv HTTP message to/from www.dream-pro.info without name tlanslation
'''

import socket
from httplib import HTTPMessage, HTTPResponse
from StringIO import StringIO
from zlib import decompress

# IPv4 address of www.dream-pro.info
WWW_DREAM_PRO_INFO = '202.215.80.119'


class DPIReqMsg():
    '''
    struct HTTP request message to www.dream-pro.info
    Host header is forcibly rewrited to 'www.dream-pro.info'
    '''
    def __init__(self, method, path, version='HTTP/1.1'):
        self.method = method.upper()
        self.path = path
        self.version = version
        self.msg = HTTPMessage(StringIO())
        self.body = ''

    def setheader(self,key,val):
        self.msg[key]=val

    def setbody(self,body):
        self.body = body

    def importmsg(self,httpmsg):
        # if httplib.HTTPMessage is already prepared, you can use it.
        self.msg = httpmsg

    def __str__(self):
        self.msg['Host'] = 'www.dream-pro.info'
        if self.body:
            self.msg['content-length'] = str(len(self.body))
        s  = ''
        s += '%s %s %s\n' % (self.method, self.path, self.version)
        s += str(self.msg)
        s += '\n' # end of header
        s += self.body
        return s

    def send_and_recv(self):
        try:
            # because www.dream-pro.info is tlanslated to 127.0.0.1 using hosts' entry,
            # send message to www.dream-pro.info with socket.socket to make
            # http connection
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.connect((WWW_DREAM_PRO_INFO,80))
            sock.sendall(str(self))
        except:
            print 'SocketError'
            return

        res = HTTPResponse(sock)
        res.begin()
        res_body = res.read()
        res.close()

        if 'transfer-encoding' in res.msg:
            # httplib.HTTPResponse automatically concatenate chunked response
            # but do not delete 'transfer-encoding' header
            # so the header must be deleted
            res.msg.__delitem__('transfer-encoding')
        compmeth = res.msg.getheader('content-encoding','').lower()
        if compmeth and compmeth.find('identity') != 0 :
            # response body is compressed with some method
            offset = 0
            if compmeth.find('gzip') != -1:
                # if body is gziped, header offset value is 47
                # if not, offset value is 0
                # this server does not support sdch...
                offset += 47
            res_body = decompress(res_body,offset)
            res.msg['content-encoding'] = 'identity'

        return res, res_body

def main():
    pass

if __name__ == '__main__':
    main()
