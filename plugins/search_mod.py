#coding: utf-8
from urlparse import urlparse
from urllib import quote,unquote

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
##    try:
##        rt = lxml.html.fromstring(body_mod)
##    except:
##        return res,res_body

    # add chart symbols, insane LV25 link, normal bms list to exlevel list
    if q_dict.get('mode') and 'search' in q_dict.get('mode'):
        if q_dict.get('type') and 'insane' in q_dict.get('type'):
            exlv_template = u'<a href="search.cgi?mode=search&type=insane&exlevel=%s&7keys=1">%s</a> \n'
            insane_box = rt.xpath('/html/body/div[@align="center"]/div[@id="box"]/div[@id="menu"]')[1]
            insane25 = lxml.html.fromstring(exlv_template % ('25','25'))
            insane_box.insert(insane_box.index(insane_box.find('br').getprevious()), insane25)
            def update_text(s):
                if s.text: s.text = u'★' + s.text
                return s
            map(lambda s:update_text(s),insane_box.getchildren())
            normallist = [exlv_template % ('0',u'☆SP')]+[exlv_template % (str(30+lv),u'☆'+str(lv),) for lv in range(1,14)]+[exlv_template % ('44',u'☆X')]
            insane_box.insert(0,lxml.html.fromstring(''.join(normallist)+'<br>'))

    # add links for specific tag
    if q_dict.get('mode') and 'search' in q_dict.get('mode'):
        if q_dict.get('type') and 'tag' in q_dict.get('type') and q_dict.get('keyword'):
            tag = unquote(q_dict.get('keyword').pop()).decode('cp932')
            levelbox = ''
            for t in tag_match:
                if tag.find(t) == 0:
                    levelbox = u'\n<div id="menu">\n%s</div>\n'
                    box_in = u''
                    tag_template = u'<a href="search.cgi?mode=search&sort=bmsid_desc&keyword=%s&type=tag">%s</a> \n'
                    for tag_append in tag_match[t]:
                        box_in += tag_template % (tag_append,tag_append,)
                    levelbox = levelbox % box_in
                    break
            if levelbox:
                rt.xpath('/html/body/div/div/h3')[0].addnext(lxml.html.fromstring(levelbox))


    return result

if __name__ == '__main__':
    pass
