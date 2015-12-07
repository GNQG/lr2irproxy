#coding: utf-8
from os.path import basename,dirname
from glob import glob


dict_master = ['replace_output','edit_request','edit_response']

import_files = map(lambda s: basename(s)[:-3], glob(dirname(__file__)+'/*.py'))
import_files.remove('__init__')

import_dirs = map(lambda s: basename(dirname(s)), glob(dirname(__file__) + '/*/__init__.py') )


__all__ = dict_master + import_files + import_dirs


replace_output = {
    #'/~lavalse/LR2IR/getrankingxml.cgi' : 'create_rival_ranking_xml'
}

edit_request = {

}

edit_response = {
    '/~lavalse/LR2IR/search.cgi' : 'search_mod'
}