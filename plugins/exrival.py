#coding: utf-8
import urllib2
from urlparse import parse_qs, unquote
import sqlite3
import time

import lxml.html

from lptools import shared_db, dpi_sock, simpleres, lr2files
from plugins import extend_link


extend_link.links.append(lxml.html.fromstring('<a href="exrival">exrival</a>'))

rankinfo = {'bmsmd5':'','name':''}


class AddRivalError(Exception):
    def __init__(self,val):
        self.val = val
    def __unicode__(self):
        return u'[exrival]AddRivalError: ' + unicode(self.val)


def register_scores(lr2id,lu=0):
    cur = shared_db.conn.cursor()
    score_et = dpi_sock.getplayerscore(lr2id,lu)
    score_all = score_et.xpath('/dummyroot/scorelist/score')

    score_list = [{ t.tag: (int(t.text) if t.text.isdigit() else t.text) for t in score} for score in score_all]
    for score in score_list:
        score_tmp = score
        score_tmp['lr2id'] = lr2id
        cur.execute('''
            REPLACE INTO exrival_score
            VALUES(
                :lr2id,:hash,:clear,:notes,:combo,
                :pg,:gr,:gd,:bd,:pr,:minbp,
                :option,:lastupdate
            )
        ''',score_tmp)
    print '[LR2ID:%06d]imported scores: %d' % (lr2id,len(score_list))
    return


def init():
    print 'imported plugin: exrival (manage rivals and emulate rankings in them)'
    cur = shared_db.conn.cursor()

    # create 2 tables if not exists
    try:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS
            exrival_rival(
                lr2id INTEGER NOT NULL UNIQUE,
                current_name TEXT,
                screen_name TEXT,
                lastupdate INTEGER NOT NULL,
                active INTEGER
            )''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS
            exrival_score(
                lr2id INTEGER NOT NULL,
                hash TEXT NOT NULL,
                clear INTEGER NOT NULL,
                notes INTEGER NOT NULL,
                combo INTEGER NOT NULL,
                pg INTEGER NOT NULL,
                gr INTEGER NOT NULL,
                gd INTEGER NOT NULL,
                bd INTEGER NOT NULL,
                pr INTEGER NOT NULL,
                minbp INTEGER NOT NULL,
                option INTEGER NOT NULL,
                lastupdate INTEGER NOT NULL,
                UNIQUE(lr2id, hash)
            )''')
        shared_db.conn.commit()
    except:
        shared_db.conn.rolback()
        print '[exrival] failed to initialize tables.'
        quit

    cur.execute('SELECT lr2id,lastupdate FROM exrival_rival WHERE active != 0')

    active_rivals = cur.fetchall()

    print 'the number of active rivals: %s' % len(active_rivals)

    for rival in active_rivals:
        time_now = int(time.time())
        try:
            register_scores(rival['lr2id'],rival['lastupdate'])
            cur.execute('''
                UPDATE exrival_rival SET lastupdate=? WHERE lr2id=?
            ''',(time_now,rival['lr2id'],))
            shared_db.conn.commit()
        except Exception as e:
            shared_db.conn.rollback()
            print '[exrival] error on registering rival scores of lr2id: %d (%s)' % (rival['lr2id'],e,)
    return


def func(args):
    global rankinfo
    result = args

    q_dict = args['query']
    cur = shared_db.conn.cursor()

    if not 'res' in result:
        # 'replace_output'
        # access to /~lavalse/LR2IR/exrival
        # -> generate a page for managing exrival(s)
        # access to /~lavalse/LR2IR/getrankingxml.cgi
        # -> emulate getrankingxml.cgi using data of exrival

        if args['path'] == '/~lavalse/LR2IR/exrival':

            def append_exrivalbox(tmp_rt):
                # make a page listing exrival(s)
                write_et = tmp_rt.xpath('/html/body/div/div').pop()

                # set button to add a rival
                form_add = lxml.html.fromstring(u'<form><input type="hidden" name="mode" value="add">LR2ID : <input type="text" name="playerid" value=""><input type="submit" value="ライバル追加"></form>')
                write_et.append(form_add)

                # table for exrival(s)
                r_table = lxml.html.fromstring('<table border="0"></table>')
                r_table.append(lxml.html.fromstring(u'<tr><th>LR2ID</th><th>登録名</th><th>現在の名前</th><th>最終更新</th><th>アクティブ</th></tr>'))

                csr = shared_db.conn.cursor()
                csr.execute('''
                    SELECT lr2id,current_name,screen_name,lastupdate,active FROM exrival_rival ORDER BY lr2id ASC
                ''')
                rival_all = csr.fetchall()

                if rival_all:
                    # create exrival list

                    # button to change active state of each rival
                    form_active = lxml.html.fromstring(u'<form method="post"><input type="hidden" name="mode" value="active"><input type="submit" value="設定の更新"><br></form>')

                    for rival in rival_all:
                        rd = dict(rival)
                        rd['checked'] = 'checked' if rd['active'] else ''
                        rd['active'] = u'<input type="checkbox" name="active_{lr2id}" value="1" {checked}>'.format(**rd)
                        rd['lr2id_link'] = u'<a href="search.cgi?mode=mypage&playerid={lr2id}">{lr2id}</a>'.format(**rd)
                        rd['current_name'] = '' if rd['current_name'] is None else unicode(rd['current_name'])
                        rd['screen_name'] = u'未設定' if rd['screen_name'] is None else unicode(rd['screen_name'])
                        rd['lastupdate'] = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(int(rd['lastupdate'])))
                        rd['active'] = u'<input type="checkbox" name="active_{lr2id}" value="1" {checked}>'.format(**rd)
                        r_table.append(lxml.html.fromstring(u'<tr><td>{lr2id_link}</td><td>{screen_name}</td><td>{current_name}</td><td>{lastupdate}</td><td>{active}</td></tr>'.format(**rd)))

                    form_active.append(r_table)
                    write_et.append(form_active)

                else:
                    # only header
                    write_et.append(r_table)

                return tmp_rt


            # to prepare template page of exrival, GET blank mypage with cookies if exists
            tmp_req = dpi_sock.DPIReqMsg('GET','/~lavalse/LR2IR/search.cgi?mode=mypage')
            if args['req'].msg.getheader('cookie'):
                tmp_req.msg['cookie'] = args['req'].msg.getheader('cookie')

            res, body = tmp_req.send_and_recv()
            rt = lxml.html.fromstring(body.decode('cp932',errors='ignore'))

            if args['req'].method == 'GET':
                # GET access to exrival
                # mode=add : add rival

                if q_dict.get('mode') and 'add' in q_dict.get('mode'):
                    try:
                        # page for adding a new rival
                        if q_dict['playerid'] and q_dict['playerid'][0].isdigit():
                            plid = int(q_dict['playerid'][0])
                            cur.execute('SELECT lr2id FROM exrival_rival WHERE lr2id=?',(plid,))
                            if cur.fetchall():
                                raise('requested LR2ID is already in exrival list')
                            preq = dpi_sock.DPIReqMsg('GET','/~lavalse/LR2IR/search.cgi?mode=mypage&playerid=%d' % plid)
                            res,resbody = preq.send_and_recv()
                            pinfo = lxml.html.fromstring(resbody.decode('cp932',errors="ignore"))
                            nameline = pinfo.xpath('/html/body/div/div/h3')
                            if pinfo and len(nameline):
                                nameline = nameline[0]
                                nm = nameline.text[:nameline.text.rfind(u'のマイページ')]
                                box = lxml.html.fromstring(u'<span>LR2ID:%d 現在の名前:%s<br></span>' % (plid,nm,))
                                form = lxml.html.fromstring('<form method="post" action="exrival"></form>')
                                form.append(lxml.html.fromstring(u'固定表示名(任意):<input type="text" name="scrname"><input type="hidden" name="mode" value="add"><input type="hidden" name="lr2id" value="%d"><input type="submit" value="ライバル追加">' % (plid,)))
                                box.append(form)
                                rt.xpath('/html/body/div/div')[0].append(box)
                            else:
                                raise AddRivalError('requested LR2ID does not exist')
                        else:
                            raise AddRivalError('requested LR2ID is invalid')
                    except AddRivalError as e:
                        rt.xpath('/html/body/div/div').pop().text += unicode(e)
                        rt = append_exrivalbox(rt)

                else:
                    # listing all exrival(s)
                    rt = append_exrivalbox(rt)
            else:
                # method == 'POST'

                body_dict = args['req'].body

                if body_dict.get('mode') and 'active' in body_dict.get('mode'):
                    # refresh active states
                    cur.execute('SELECT lr2id FROM exrival_rival')
                    id_all = [int(row['lr2id']) for row in cur.fetchall()]
                    active_list = []

                    for key in body_dict:
                        if key.startswith('active_') and key[7:].isdigit() and body_dict[key][0] == '1':
                            active_list.append(int(key[7:]))

                    try:
                        # UPDATE new active states
                        cur.execute('UPDATE exrival_rival SET active=0')
                        for a_id in active_list:
                            cur.execute('UPDATE exrival_rival SET active=1 WHERE lr2id=?', (a_id,))
                        shared_db.conn.commit()
                        outmsg = u'[exrival] active state was refreshed successfully'
                    except Exception as e:
                        shared_db.conn.rollback()
                        outmsg = u'[exrival] some error occured during changing active state(%s)' % unicode(e)

                    rt.xpath('/html/body/div/div').pop().text += outmsg

                elif body_dict.get('mode') and 'add' in body_dict['mode']:
                    # create new rival to exrival list and import rival score
                    try:
                        lr2id=None
                        if body_dict.get('lr2id') and body_dict['lr2id'][0].isdigit():
                            lr2id = int(body_dict['lr2id'][0])
                        else:
                            raise AddRivalError('requested LR2ID is invalid')

                        if body_dict.get('scrname') and body_dict['scrname']:
                            screen_name = body_dict['scrname'][0].decode('cp932',errors="ignore")
                        else:
                            screen_name = None

                        rivalinfo = dpi_sock.getplayerscore(lr2id)
                        rscores = rivalinfo.xpath('/dummyroot/scorelist/score')
                        current_name = rivalinfo.find('rivalname').text
                        # current_name must not be NoneType
                        if current_name is None: current_name = ''

                        try:
                            # add rival to exrival_rival
                            cur.execute(u'''
                                INSERT INTO exrival_rival(lr2id,current_name,screen_name,lastupdate,active)
                                VALUES(?,?,?,0,1)
                            ''', (lr2id,current_name,screen_name,))
                            shared_db.conn.commit()
                        except Exception as e:
                            shared_db.conn.rollback()
                            raise AddRivalError('SQL error during adding a new rival(%s)' % unicode(e))

                        try:
                            # import rival score
                            time_now = int(time.time())
                            register_scores(lr2id)
                            cur.execute('''
                                UPDATE exrival_rival SET lastupdate=? WHERE lr2id=?
                            ''',(time_now,lr2id,))
                            shared_db.conn.commit()
                        except Exception as e:
                            shared_db.conn.rollback()
                            raise AddRivalError('SQL error during registering score(s)(%s)' % str(e))

                        # all operations succeeded
                        rt.xpath('/html/body/div/div').pop().text += u'Successfully added new rival: (LR2ID:%d)' % (lr2id)

                    except AddRivalError as e:
                        rt.xpath('/html/body/div/div').pop().text += unicode(e)

                rt = append_exrivalbox(rt)

            result['res'] = res
            result['res_etree'] = rt

            result = extend_link.func(result)

        elif args['path'] == '/~lavalse/LR2IR/getrankingxml.cgi':
            # emulate getraningxml.cgi using data in exrival_score table in shared_db
            res = simpleres.SimpleHTTPResponse()
            res.msg['content-type'] = 'text/plain'

            if args['req'].method == 'POST':
                # request from LR2body.exe only has content-types header...
                try:
                    q_dict = parse_qs(args['req'].body)
                except:
                    pass

            bmsmd5 = q_dict.get('songmd5')[0] if q_dict.get('songmd5') else ''
            if not bmsmd5 or len(bmsmd5)>32:
                # getplayerxml does not get course score and '' score
                # if given those, return default getrankingxml.cgi value
                raw = dpi_sock.DPIReqMsg('GET','/~lavalse/LR2IR/getrankingxml.cgi?songmd5=%s' % bmsmd5)
                res, res_body = raw.send_and_recv()
                result['res'] = res
                result['res_body'] = res_body
                return result

            # request body from LR2body.exe contains lr2id of current user
            # use it to get latest score of given bmsmd5
            mylr2id = q_dict.get('id')[0] if q_dict.get('id') else ''
            mylr2id = int(mylr2id) if mylr2id.isdigit() else 0

            # active rivals' scores who played the song of given bmsmd5
            cur.execute('''
                SELECT er.lr2id AS id,current_name,screen_name,
                       clear,notes,combo,pg,gr,minbp
                FROM exrival_rival AS er
                INNER JOIN exrival_score AS es ON er.lr2id=es.lr2id
                WHERE er.active!=0 AND es.hash=? AND er.lr2id!=?
            ''',(bmsmd5,mylr2id,))
            played = cur.fetchall()

            # blank scores for other active rivals
            cur.execute('''
                SELECT lr2id AS id,current_name,screen_name,
                       0 AS clear, 0 AS notes, 0 AS combo, 0 AS pg, 0 AS gr, 0 AS minbp
                FROM exrival_rival
                WHERE active!=0 AND lr2id!=? AND NOT id IN (
                    SELECT lr2id FROM exrival_score WHERE hash=?
                )
            ''',(mylr2id,bmsmd5,))
            notplayed = cur.fetchall()


            # add my best score to ranking from local db
            myscore = []
            if mylr2id > 0 and str(mylr2id) in lr2files.id_db_dict:
                # use local score database
                scdb_cur = lr2files.id_db_dict[str(mylr2id)].cursor()
                scdb_cur.execute('SELECT irid AS id,name FROM player')
                mydata = dict(scdb_cur.fetchone())
                if rankinfo['bmsmd5'] == bmsmd5 and rankinfo['name']:
                    # rankinfo consist of info of this song
                    # rankinfo['name'] contains player's IR rank
                    mydata['name'] = rankinfo['name']
                # after overwriting, initialize rankinfo
                rankinfo['bmsmd5'] = ''
                rankinfo['name'] = ''
                # if already have local score, use it
                # if not, do nothing
                scdb_cur.execute('''
                    SELECT {id} AS id, '{name}' AS name,
                           clear, totalnotes AS notes, maxcombo AS combo,
                           perfect AS pg, great AS gr, minbp
                    FROM score WHERE hash=?
                '''.format(**mydata), (bmsmd5,))
                # len(myscore) = 0 or 1
                myscore = scdb_cur.fetchall()


            # create rankingxml body
            rt = lxml.etree.fromstring('<ranking>\n</ranking>')
            elem_keys = ['name','id','clear','notes','combo','pg','gr','minbp']
            score_template = u'<score>\n%s\t</score>' % (''.join(['\t\t<%s>{%s}</%s>\n' % (key,key,key,) for key in elem_keys]),)
            for score in played + notplayed + myscore:
                sc = dict(score)
                if not 'name' in sc:
                    # myscore already has 'name' element
                    sc['name'] = sc['current_name'] if sc['screen_name'] is None else sc['screen_name']
                sc_et = lxml.etree.fromstring(score_template.format(**sc))
                sc_et.tail = '\n\t'
                rt.append(sc_et)
            rt.text = '\n\t'
            rt[-1].tail = '\n'

            # important: response of getrankingxml.cgi is not xml
            # 1. it starts from '#'
            # 2. xml 'ranking' follows
            # 3. 'lastupdate' element inserted at the end of body
            res_body = '#'
            res_body += lxml.etree.tostring(rt,encoding='cp932').replace('cp932','shift_jis')
            res_body += '\n<lastupdate>%s</lastupdate>' % time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(int(time.time())))

            result['res'] = res
            result['res_body'] = res_body

    else:
        # 'res' in args == True
        # 'edit_response'
        if args['path'] == '/~lavalse/LR2IR/score.cgi':
            # import my rank in IR by parsing response of score.cgi
            if args['req'].method == 'POST':
                try:
                    q_dict = parse_qs(args['req'].body)
                except Exception as e:
                    pass

            try:
                # if score.cgi succeed, ginven body is
                # #{myrank},{the number of total players in IR},{clear rate(not failed)},
                score_res = args['res_body'].split(',')
                if len(score_res) < 4:
                    raise Exception
                rankinfo['bmsmd5'] = q_dict['songmd5'][0]
                rankinfo['name'] = 'IR'+score_res[0]+'/'+score_res[1]
            except Exception as e:
                rankinfo['bmsmd5'] = ''
                rankinfo['name'] = ''

    return result


# initialize
init()

if __name__ == '__main__':
    pass
