#coding: utf-8
from os.path import basename,dirname
from glob import glob
from urlparse import urlparse
from urllib import unquote

dict_master = ['replace_output','edit_request','edit_response']

import_files = map(lambda s: basename(s)[:-3], glob(dirname(__file__)+'/*.py'))
import_files.remove('__init__')

import_dirs = map(lambda s: basename(dirname(s)), glob(dirname(__file__) + '/*/__init__.py') )


__all__ = dict_master + import_files + import_dirs


def replace_output(args):
    q_dict = args['query']

    # for exgrade
    if args['path'] == '/~lavalse/LR2IR/exgrade':
        return 'exgrade'

    # for exrival
    if args['path'] == '/~lavalse/LR2IR/exrival' or args['path'] == '/~lavalse/LR2IR/getrankingxml.cgi':
        return 'exrival'

    return ''


def edit_request(args):
    result = []

    return result


def edit_response(args):
    result = []
    q_dict = args['query']


    # for etend_link
    if args['path'] == '/~lavalse/LR2IR/search.cgi':
        if args['res'].msg.get('content-type','').startswith('text/html'):
            result.append('extend_link')

    # for exgrade
    if args['path'] == '/~lavalse/LR2IR/search.cgi':
        if q_dict.get('mode'):
            mode = q_dict.get('mode')[0]
            if 'ranking' == mode or 'mypage' == mode:
                result.append('exgrade')

    # for mod_insane_box
    if args['path'] == '/~lavalse/LR2IR/search.cgi':
        if q_dict.get('mode'):
            mode = q_dict.get('mode')[0]
            if 'search' == mode and q_dict.get('type'):
                search_type = q_dict.get('type')[0]
                if 'insane' == search_type:
                    result.append('mod_insane_box')

    # for related_tags
    if args['path'] == '/~lavalse/LR2IR/search.cgi':
        if q_dict.get('mode'):
            mode = q_dict.get('mode')[0]
            if 'search' == mode and q_dict.get('type'):
                search_type = q_dict.get('type')[0]
                if 'tag' == search_type:
                    result.append('related_tags')


    return result
