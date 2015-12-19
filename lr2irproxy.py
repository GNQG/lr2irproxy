#coding: utf-8

from os.path import abspath, basename, dirname
from glob import glob
from urlparse import urlparse, parse_qs
from cgi import parse_header, parse_multipart
from urllib import quote
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

import lxml.html

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
#        self.req_body = self.rfile.read(int(self.headers.getheader('content-length',0)))
        self.req_body = ''
        parsed_path = urlparse(self.path)
        prsd_path = parsed_path.path
        prsd_query = parsed_path.query

        query_dict = parse_qs(prsd_query)
        if self.command == 'POST':
            ctype, pdict = parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                self.req_body = parse_multipart(self.rfile,pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                self.req_body = parse_qs(self.rfile.read(int(self.headers.getheader('content-length',0))))
            else:
                self.req_body = self.rfile.read(int(self.headers.getheader('content-length',0)))

        # create original request message
        req = dpi_sock.DPIReqMsg(self.command,self.path,self.request_version)
        req.importmsg(self.headers)
        req.setbody(self.req_body)

        args = {'req' : req, 'path' : prsd_path, 'query' : query_dict}

        pname = plugins.replace_output(args)
        if pname:
            # replace whole output
            sub_mod =getattr(plugins,pname)
            args = sub_mod.func(args)
        else:
            # send a request to www.dream-pro.info

            plist = plugins.edit_request(args)
            for pname in plist:
                # modify http request header or body
                sub_mod = getattr(plugins,pname)
                args = sub_mod.func(args)

            # send/recv HTTP message
            res, res_body = req.send_and_recv()

            args['res'] = res
            args['res_body'] = res_body

            plist = plugins.edit_response(args)
            for pname in plist:
                # modify http response from www.dream-pro.info
                sub_mod = getattr(plugins,pname)
                args = sub_mod.func(args)


        if 'res_etree' in args:
            # update args['res_body'] because if args['res_etree'] exists
            # that is newer than args['res_body']
            def quote_unicode_to_cp932(a):
                if not a.get('href'):return a
                qs = parse_qs(urlparse(a.get('href')).query)
                if qs.get('keyword'):
                    a.set('href',a.get('href').replace(qs['keyword'][0],quote(qs['keyword'][0].encode('cp932'))))
                if qs.get('tag'):
                    a.set('href',a.get('href').replace(qs['tag'][0],quote(qs['tag'][0].encode('cp932'))))
                return a
            map(quote_unicode_to_cp932, args['res_etree'].xpath('//a'))
            args['res_body'] = lxml.html.tostring(args['res_etree'],encoding='cp932')


        # send response to client
        self.send_response(args['res'].status,args['res'].reason)

        if 'connection' in args['res'].msg.keys():
            args['res'].msg.__delitem__('connection')
        if 'keep-alive' in args['res'].msg.keys():
            args['res'].msg.__delitem__('keep-alive')
        args['res'].msg['content-length'] = str(len(args['res_body']))
        for hdr in args['res'].msg:
            self.send_header(hdr,args['res'].msg[hdr])
        self.end_headers()


        self.wfile.write(args['res_body'])
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
