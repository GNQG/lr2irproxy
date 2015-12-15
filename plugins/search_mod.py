#coding: utf-8
from urlparse import parse_qs,urlparse
from urllib import quote,unquote

import lxml.html

from lptools import shared_db


ln_tags = map(lambda i: u'◆' + str(i), range(1,27)) + [u'LN表新規提案',u'LN表難易度変更提案',u'LN表削除提案']
ins2_tags = map(lambda i: u'▼' + str(i), range(0,25) + [u'?'])

tag_match = {
    u'◆' : ln_tags,
    u'LN表' : ln_tags,
    u'▼' : ins2_tags
}

def init():
    cur = shared_db.conn.cursor()
    cur.execute('''
        SELECT name FROM sqlite_master
        WHERE type="table"
        ''')
    tablenames = [t['name'] for t in cur.fetchall()]

    if not 'grade_set' in tablenames:
        cur.execute('''
            CREATE TABLE grade_set(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                active INTEGER
            )''')
        shared_db.conn.commit()
    if not 'grade_grade' in tablenames:
        cur.execute('''
            CREATE TABLE grade_grade(
                set_id INTEGER NOT NULL,
                level REAL NOT NULL,
                courseid INTEGER NOT NULL,
                hash TEXT NOT NULL,
                name TEXT,
                expr TEXT NOT NULL,
                FOREIGN KEY(set_id) REFERENCES grade_set(id)
                UNIQUE(set_id, level)
            )''')
        shared_db.conn.commit()
    if not 'grade_achiever' in tablenames:
        cur.execute('''
            CREATE TABLE grade_achiever(
                crs_id INTEGER NOT NULL,
                lr2id INTEGER NOT NULL,
                FOREIGN KEY(crs_id) REFERENCES grade_grade(courseid)
                UNIQUE(courseid, lr2id)
            )''')
        shared_db.conn.commit()

    cur.execute('''
        SELECT courseid,hash FROM grade_grade gg
        INNER JOIN grade_set gs ON gg.set_id=gs.id
        WHERE gs.active != 0
    ''')
    crs_list = cur.fetchall()
    achievers_list = [(crs['courseid'],get_achiever(crs['hash'])) for crs in crs_list]
    for crs in achievers_list:
        for ach in crs[1]:
            cur.execute(''''
                REPLACE INTO grade_achiever
                VALUES(?,?)
                WHERE crs_id=? AND lr2id=?
            ''',(crs[0],ach,crs[0],ach,))
    conn.commit()

    return

def func(req,res,res_body):
    body_mod = res_body.decode('cp932',errors='ignore')
    parsed = urlparse(req.path)
    path = parsed.path
    q_dict = parse_qs(parsed.query)

    try:
        rt = lxml.html.fromstring(body_mod)
    except:
        return res,res_body

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

    # add 3rd party grade to ranking page
    if q_dict.get('mode') and 'ranking' in q_dict.get('mode'):
        ranking_table = rt.xpath('/html/body/div/div/table')[-1]
        ranking_lr2id = [(int(parse_qs(tr[1][0].get('href'))['playerid'].pop()),) for tr in ranking_table[1::2]]
        cur = shared_db.conn.cursor()
        exgrades = []
        for lr2id in ranking_lr2id:
            cur.execute('''
                SELECT expr FROM grade_grade AS gg
                INNER JOIN (
                    SELECT set_id, MAX(level) AS maxlv FROM grade_grade
                    WHERE courseid IN (SELECT courseid FROM grade_achiever WHERE lr2id=?)
                    GROUP BY set_id
                ) AS bg ON gg.set_id=bg.set_id AND gg.level=bg.maxlv
                ORDER BY gg.set_id ASC
                ''', lr2id)
            exgrades.append(cur.fetchall())
        def update_text(s):
            if s[0]:
                s[1][2].append(lxml.html.fromstring('<br>'))
                s[1][2][0].tail = '/'.join([exg['expr'] for exg in s[0]])
            return s
        map(update_text, zip(exgrades,ranking_table[1::2]))

    def quote_unicode_to_cp932(a):
        if not a.get('href'):return a
        qs = parse_qs(urlparse(a.get('href')).query)
        if qs.get('keyword'):
            a.set('href',a.get('href').replace(qs['keyword'][0],quote(qs['keyword'][0].encode('cp932'))))
        if qs.get('tag'):
            a.set('href',a.get('href').replace(qs['tag'][0],quote(qs['tag'][0].encode('cp932'))))
        return a
    map(quote_unicode_to_cp932, rt.xpath('//a'))
    body_mod = lxml.html.tostring(rt,encoding='cp932')

    return res,body_mod

if __name__ == '__main__':
    init()
