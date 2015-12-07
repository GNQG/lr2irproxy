#coding: utf-8
from urlparse import parse_qs
from urllib import quote,unquote

ln_tags = map(lambda i: u'◆' + str(i), range(1,27)) + [u'LN表新規提案',u'LN表難易度変更提案',u'LN表削除提案']

tag_match = {
    u'◆' : ln_tags,
    u'LN表' : ln_tags
}

def func(q_str,msg,body):
    msg_mod,body_mod = msg,body.decode('cp932')
    q_dict = parse_qs(q_str)

    if q_dict.get('mode') and 'search' in q_dict.get('mode'):
        if q_dict.get('type') and 'insane' in q_dict.get('type'):
            # add chart symbols, insane LV25 link, normal bms list to exlevel list
            alllevel_start = body_mod.find('<div id="menu">',body_mod.find('<!--end search-->'))+len('<div id="menu">')
            alllevel_end = body_mod.find('</div>',alllevel_start)
            alllevel = body_mod[alllevel_start:alllevel_end]
            tmp_up = body_mod[:alllevel_start]
            tmp_down = body_mod[alllevel_end:]

            exlv_template = u'<a href="search.cgi?mode=search&type=insane&exlevel=%s&7keys=1">%s</a> \n'

            alllevel = alllevel.replace(u'1">',u'1">★')
            alllevel = alllevel.replace(u'7keys=1">★24</a>',u'7keys=1">★24</a> ' + exlv_template % (str(25),u'★25') )

            normal_level = exlv_template % ('0',u'☆SP')
            for i in range(31,44):
                normal_level += exlv_template % (str(i), u'☆%d' % (i-30),)
            normal_level += exlv_template % (str(44),u'☆X',) + '<br>'

            body_mod = tmp_up + normal_level + alllevel + tmp_down

        elif q_dict.get('type') and 'tag' in q_dict.get('type'):
            # add links for specific tag
            tag = unquote(q_dict.get('keyword').pop()).decode('cp932')
            levelbox = ''
            for t in tag_match:
                if tag.find(t) == 0:
                    levelbox = u'\n<div id="menu">\n%s</div>\n'
                    box_in = u''
                    tag_template = u'<a href="search.cgi?mode=search&sort=bmsid_desc&keyword=%s&type=tag">%s</a> \n'
                    for tag_append in tag_match[t]:
                        box_in += tag_template % (quote(tag_append.encode('cp932')),tag_append,)
                    levelbox = levelbox % box_in
                    break
            insert_point = body_mod.find('</h3>',body_mod.find('<!--end search-->'))+len('</h3>')
            body_mod = body_mod[:insert_point] + levelbox + body_mod[insert_point:]

    return msg_mod,body_mod.encode('cp932')

if __name__ == '__main__':
    main()
