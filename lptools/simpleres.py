#coding: utf-8
from httplib import HTTPMessage
from StringIO import StringIO

class SimpleHTTPResponse():
    '''
    simple HTTP response class like httplib.HTTPResponce
    '''
    def __init__(self):
        self.msg = HTTPMessage(StringIO())
        # default status is 200
        self.status = 200
        self.reason = 'OK'

    def setstatus(self,status):
        self.status = int(status)

    def setreason(self, reason):
        self.reason = reason


def main():
    pass

if __name__ == '__main__':
    main()
