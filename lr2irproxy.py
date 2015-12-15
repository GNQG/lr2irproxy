#coding: utf-8

from os.path import abspath, basename, dirname
from glob import glob
from urlparse import urlparse
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from lptools import dpi_sock


#
# import all *.py file(s) and module folder(s) under ./plugins
# as submodule(s) of plugins module
#
# overwrite_rule_dict : names of dictionaries about mapping rules of overwriting
#                       (defined at ir_overwrite/__init__.py)
#
overwrite_rule = ['replace_output','edit_request','edit_response']
import_files = map(lambda s: basename(s)[:-3], glob(abspath(dirname(__file__))+'/plugins/*.py'))
import_dirs = map(lambda s: basename(dirname(s)), glob(abspath(dirname(__file__)) + '/plugins/*/__init__.py') )
fromlist = overwrite_rule + import_files + import_dirs
plugins = __import__('plugins',globals(),locals(),fromlist,)


# IPv4 address of www.dream-pro.info
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
#        self.protocol_version = 'HTTP/1.1'
        self.req_body = self.rfile.read(int(self.headers.getheader('content-length',0)))
        parsed_path = urlparse(self.path)
        prsd_path = parsed_path.path
        prsd_query = parsed_path.query

        # create original request message
        req = dpi_sock.DPIReqMsg(self.command,self.path,self.request_version)
        req.importmsg(self.headers)
        req.setbody(self.req_body)

        plist = plugins.replace_output(req)
        if plist:
            # replace whole output
            for pname in plist:
                sub_mod =getattr(plugins,pname)
                res, res_body = sub_mod.func(req)
        else:
            # send a request to www.dream-pro.info

            plist = plugins.edit_request(req)
            for pname in plist:
                # modify http request header or body
                sub_mod = getattr(plugins,pname)
                req = sub_mod.func(req)

            # send/recv HTTP message
            res, res_body = req.send_and_recv()

            plist = plugins.edit_response(req,res)
            for pname in plist:
                # modify http response from www.dream-pro.info
                sub_mod = getattr(plugins,pname)
                res, res_body = sub_mod.func(req,res,res_body)

        self.send_response(res.status,res.reason)

        if 'connection' in res.msg.keys():
            res.msg.__delitem__('connection')
        if 'keep-alive' in res.msg.keys():
            res.msg.__delitem__('keep-alive')
        res.msg['content-length'] = str(len(res_body))
        for hdr in res.msg:
            self.send_header(hdr,res.msg[hdr])
        self.end_headers()

        self.wfile.write(res_body)
        return

    do_GET  = do_all
    do_POST = do_all
    do_HEAD = do_all



def main():
    server = HTTPServer(('www.dream-pro.info', 80), lr2irproxy)
    print 'Starting server, use <Ctrl-C> to stop'
    try:
        server.serve_forever()
    except:
        pass


if __name__ == '__main__':
    main()
