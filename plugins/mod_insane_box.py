#coding: utf-8

import lxml.html

def func(args):
    '''
    add chart symbols, SP insane LV25 link, SP normal bms list to exlevel list
    step 1. : add SP insane LV25 link
    step 2. : add chart symbol '★' to all links
    step 3. : add normal bms set
    '''
    result = args
    if not 'res_etree' in result:
        result['res_etree'] = lxml.html.fromstring(result['res_body'].decode('cp932',errors='ignore'))
    rt = result['res_etree']

    q_dict = args['query']


    exlv_template = u'<a href="search.cgi?mode=search&type=insane&exlevel=%d&%dkeys=1">%s</a> \n'
    # [0] is menu-bar, modified by extend_link plugin
    insane_box = rt.xpath('/html/body/div[@align="center"]/div[@id="box"]/div[@id="menu"]')[1]

    # step 1.
    insane25 = lxml.html.fromstring(exlv_template % (25,7,'25',))
    # the last element before <br> is '★???'
    # insane25 must be inserted into just left of it
    # => insert into just right of prebious element of '★???', '★24'
    insane_box.insert(insane_box.index(insane_box.find('br').getprevious()), insane25)

    # step 2.
    def update_text(s):
        if s.text: s.text = u'★' + s.text
        return
    # all elements in insanebox are insane level
    # all link expression should be prefixed '★'
    map(lambda s:update_text(s),insane_box.getchildren())

    # step 3.
    # normal level set uses exlevel 31-43(☆1-☆13) and 44(☆X)
    normallist = [exlv_template % (0,7,u'☆SP',)]+ \
        [exlv_template % (30+lv,7,u'☆'+str(lv),) for lv in range(1,14)]+ \
        [exlv_template % (44,7,u'☆X',)]
    insane_box.insert(0,lxml.html.fromstring(''.join(normallist)+'<br>'))

    return result

if __name__ == '__main__':
    main()

def main():
    pass
