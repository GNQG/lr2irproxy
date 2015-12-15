#coding: utf-8
from os.path import basename,dirname
from glob import glob
from urlparse import urlparse, parse_qs
from urllib import unquote

dict_master = ['replace_output','edit_request','edit_response']

import_files = map(lambda s: basename(s)[:-3], glob(dirname(__file__)+'/*.py'))
import_files.remove('__init__')

import_dirs = map(lambda s: basename(dirname(s)), glob(dirname(__file__) + '/*/__init__.py') )


__all__ = dict_master + import_files + import_dirs


def replace_output(req):
    result = []
    parsed = urlparse(req.path)
    path = parsed.path
    q_dict = parse_qs(parsed.query)
    if path == '/~lavalse/LR2IR/exgrade':
        result.append('exgrade')
    #'/~lavalse/LR2IR/getrankingxml.cgi' : 'create_rival_ranking_xml'

    return result


def edit_request(req):
    result = []
    parsed = urlparse(req.path)
    path = parsed.path
    query = parse_qs(parsed.query)

    return result


def edit_response(req,res):
    result = []
    parsed = urlparse(req.path)
    path = parsed.path
    query = parse_qs(parsed.query)

    if path == '/~lavalse/LR2IR/search.cgi':
        result.append('search_mod')

    return result
