#coding: utf-8
from urllib import unquote

import lxml.html


ln_tags = map(lambda i: u'◆' + str(i), range(1,27)) + [u'LN表新規提案',u'LN表難易度変更提案',u'LN表削除提案']
ins2_tags = map(lambda i: u'▼' + str(i), range(0,25) + [u'?'])

tag_match = {
    u'◆' : ln_tags,
    u'LN表' : ln_tags,
    u'▼' : ins2_tags
}


def func(args):
    result = args
    if not 'res_etree' in result:
        result['res_etree'] = lxml.html.fromstring(result['res_body'].decode('cp932',errors='ignore'))
    rt = result['res_etree']

    q_dict = args['query']
    # add links for specific tag
    if q_dict.get('keyword'):
        tag = unquote(q_dict.get('keyword').pop()).decode('cp932',"ignore")
        tag_box = ''
        for t in tag_match:
            if tag.find(t) == 0:
                tag_box = u'\n<div id="menu">\n%s</div>\n'
                box_in = u''
                tag_template = u'<a href="search.cgi?mode=search&sort=bmsid_desc&keyword=%s&type=tag">%s</a> \n'
                for tag_append in tag_match[t]:
                    box_in += tag_template % (tag_append,tag_append,)
                tag_box = tag_box % box_in
                break
        if tag_box:
            rt.xpath('/html/body/div/div/h3')[0].addnext(lxml.html.fromstring(tag_box))


    return result

if __name__ == '__main__':
    pass
