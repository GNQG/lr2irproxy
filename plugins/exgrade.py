#coding: utf-8
import urllib2
from urlparse import parse_qs, unquote
import json
import sqlite3
import types
import time

import lxml.html

from lptools import shared_db, dpi_sock
from plugins import extend_link


extend_link.links.append(lxml.html.fromstring('<a href="exgrade">exgrade</a>'))



class AddGradeError(Exception):
    def __init__(self,val):
        self.val = val
    def __unicode__(self):
        return u'[exgrade]AddGradeError: ' + unicode(self.val)


def register_achiever(cid_hash_list):
    cur = shared_db.conn.cursor()
    ranking_all = [dpi_sock.getranking(course['hash']) for course in cid_hash_list]
    ranking = [ranking.xpath('/dummyroot/ranking/score') for ranking in ranking_all]
    achievers_list = [
        (course['courseid'],
        [int(score.find('id').text) for score in scores if int(score.find('clear').text)>1],)
        for course,scores in zip(cid_hash_list,ranking)]
    for course in achievers_list:
        for ach in course[1]:
            c = int(course[0])
            a = int(ach)
            cur.execute('''
                REPLACE INTO exgrade_achiever VALUES(?,?)
            ''',(c,a,))
    return


def init():
    print 'imported plugin: exgrade (manage unofficial grades)'
    cur = shared_db.conn.cursor()

    # create 3 tables if not exists
    try:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS
            exgrade_set(
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                lastupdate INTEGER NOT NULL,
                active INTEGER
            )''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS
            exgrade_grade(
                set_id INTEGER NOT NULL,
                level REAL NOT NULL,
                courseid INTEGER NOT NULL,
                hash TEXT NOT NULL,
                name TEXT,
                expr TEXT NOT NULL,
                FOREIGN KEY(set_id) REFERENCES exgrade_set(id)
                UNIQUE(set_id, level)
            )''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS
            exgrade_achiever(
                crs_id INTEGER NOT NULL,
                lr2id INTEGER NOT NULL,
                FOREIGN KEY(crs_id) REFERENCES exgrade_grade(courseid)
                UNIQUE(crs_id, lr2id)
            )''')
        shared_db.conn.commit()
    except:
        shared_db.conn.rolback()
        print '[exgrade] failed to initialize tables.'
        quit

    cur.execute('''
        SELECT id FROM exgrade_set
        WHERE active != 0 AND lastupdate<?
    ''',(int(time.time())-86400,))

    active_old_id = cur.fetchall()

    for aoid in active_old_id:
        time_now = int(time.time())
        cur.execute('''
            SELECT courseid,hash FROM exgrade_grade
            WHERE set_id=:id
        ''',aoid)
        crs_list = cur.fetchall()
        try:
            register_achiever(crs_list)
            cur.execute('''
                UPDATE exgrade_set SET lastupdate=? WHERE id=?
            ''',(time_now,aoid['id'],))
            shared_db.conn.commit()
        except Exception as e:
            shared_db.conn.rollback()
            print '[exgrade] SQL error on registering achiever(s) of grade set id %d(%s)' % (aoid['id'],e,)
    return


def func(args):
    result = args

    q_dict = args['query']
    cur = shared_db.conn.cursor()

    if not 'res' in result:
        # 'replace_output'
        # access to /~lavalse/LR2IR/exgrade
        # generate a page for managing exgrade(s)

        def append_exgradebox(tmp_rt):
            # make a page listing exgrade set(s)
            write_et = tmp_rt.xpath('/html/body/div/div').pop()

            # set button to add exgrade set
            form_add = lxml.html.fromstring(u'<form><input type="hidden" name="mode" value="add"><input type="submit" value="追加"></form>')
            write_et.append(form_add)

            # table for exgrade sets
            gs_table = lxml.html.fromstring('<table border="0"></table>')
            gs_table.append(lxml.html.fromstring(u'<tr><th>ID</th><th>段位セット</th><th>最終更新</th><th>アクティブ</th></tr>'))

            csr = shared_db.conn.cursor()
            csr.execute('''
                SELECT id,name,lastupdate,active FROM exgrade_set ORDER BY id ASC
            ''')
            gradeset_all = csr.fetchall()

            if gradeset_all:
                # create exgrade sets list

                # button to change active state of each grade set
                form_active = lxml.html.fromstring(u'<form method="post"><input type="hidden" name="mode" value="active"><input type="submit" value="アクティブ状態更新"><br></form>')

                for gradeset in gradeset_all:
                    gs = dict(gradeset)
                    gs['name'] = u'<a href="exgrade?setid={id}">{name}</a>'.format(**gs)
                    gs['lastupdate'] = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(int(gs['lastupdate'])))
                    gs['checked'] = 'checked' if gs['active'] else ''
                    gs['active'] = u'<input type="checkbox" name="active_{id}" value="1" {checked}>'.format(**gs)
                    gs_table.append(lxml.html.fromstring(u'<tr><td>{id}</td><td>{name}</td><td>{lastupdate}</td><td>{active}</td></tr>'.format(**gs)))

                form_active.append(gs_table)
                write_et.append(form_active)

            else:
                # only header
                write_et.append(gs_table)

            return tmp_rt


        # to prepare template page of exgrade, GET blank mypage with cookies if exists
        tmp_req = dpi_sock.DPIReqMsg('GET','/~lavalse/LR2IR/search.cgi?mode=mypage')
        if args['req'].msg.getheader('cookie'):
            tmp_req.msg['cookie'] = args['req'].msg.getheader('cookie')

        res, body = tmp_req.send_and_recv()
        rt = lxml.html.fromstring(body.decode('cp932',errors='ignore'))

        if args['req'].method == 'GET':
            # GET access to exgrade
            # mode  = add : add exgrade set from json
            # setid = n   : view info(all courses) of each exgrade set

            if q_dict.get('mode') and 'add' in q_dict.get('mode'):
                # page for adding a new exgrade

                box = lxml.html.fromstring('<form id="addgradeset" method="post" action="exgrade" enctype="multipart/form-data"></form>')
                box.append(lxml.html.fromstring('<span><input id="r_web" type="radio" name="ags" onchange="selectData();"><label for="r_web">from json on web</label><br></span>'))
                box.append(lxml.html.fromstring('<span><input id="r_loc" type="radio" name="ags" onchange="selectData();"><label for="r_loc">from local json</label><br></span>'))
                box.append(lxml.html.fromstring('<span id="ags_data"></span>'))
                script_str =\
'''
function selectData() {
      ch_web = document.getElementById("r_web").checked;
      ch_loc = document.getElementById("r_loc").checked;

      target = document.getElementById("ags_data");

      if (ch_web == true) {
        target.innerHTML = "<input type=\\"text\\" name=\\"jsonurl\\"> <input type=\\"submit\\">";
      }
      else if (ch_loc == true) {
        target.innerHTML = "<input type=\\"file\\" name=\\"json\\"> <input type=\\"submit\\">";
      }
    }
'''
                script = lxml.html.fromstring('<script type="text/javascript" language="javascript">%s</script>' % script_str)

                rt.xpath('/html/body/div/div')[0].append(box)
                rt.xpath('/html/head')[0].append(script.xpath('//script')[0])

            elif q_dict.get('setid') and q_dict.get('setid')[0].isdigit():
                # view info(all courses) of each exgrade set

                cur.execute('''
                    SELECT expr,name,courseid
                    FROM exgrade_grade
                    WHERE set_id=?
                    ORDER BY level ASC
                ''', (int(q_dict.get('setid')[0]),))
                grades = cur.fetchall()

                box = lxml.html.fromstring('<table border="0"></table>')
                box.append(lxml.html.fromstring(u'<tr><th>段位</th><th>コース名</th></tr>'))

                for grade in grades:
                    gd = dict(grade)
                    gd['name'] = u'<a href="search.cgi?mode=ranking&courseid={courseid}">{name}</a>'.format(**gd)
                    box.append(lxml.html.fromstring(u'<tr><td>{expr}</td><td>{name}</td></tr>'.format(**gd)))

                rt.xpath('/html/body/div/div')[0].append(box)

            else:
                # listing all exgrade(s)
                rt = append_exgradebox(rt)
        else:
            # method == 'POST'

            body_dict = args['req'].body

            if body_dict.get('mode') and 'active' in body_dict.get('mode'):
                # change active state of grade sets
                cur.execute('SELECT id FROM exgrade_set')
                id_all = [int(row['id']) for row in cur.fetchall()]
                active_list = []

                for key in body_dict:
                    if key.startswith('active_') and key[7:].isdigit() and body_dict[key][0] == '1':
                        active_list.append(int(key[7:]))

                try:
                    # UPDATE new active states
                    cur.execute('UPDATE exgrade_set SET active=0')
                    for a_id in active_list:
                        cur.execute('UPDATE exgrade_set SET active=1 WHERE id=?', (a_id,))
                    shared_db.conn.commit()
                    outmsg = u'[exgrade] active state was refreshed successfully'
                except Exception as e:
                    shared_db.conn.rollback()
                    outmsg = u'[exgrade] some error occured during changing active state(%s)' % unicode(e)

                rt.xpath('/html/body/div/div').pop().text += outmsg

            else:
                # create new exgrade set from json
                gset = None
                try:
                    # import json
                    if body_dict.get('jsonurl'):
                        try:
                            jsonres = urllib2.urlopen(unquote(body_dict['jsonurl'].pop()))
                            gset = json.loads(jsonres.read())
                        except urllib2.URLError as e:
                            raise AddGradeError('failed to get json on web(%s)' % unicode(e))
                        except ValueError as e:
                            raise AddGradeError('invalid json file')
                    elif body_dict.get('json'):
                        try:
                            gset = json.loads(body_dict['json'].pop())
                        except:
                            raise AddGradeError('failed to load local json')
                    else:
                        raise AddGradeError('invalid request')

                    # json loaded successfully
                    # check json
                    try:
                        gset_name = unicode(gset['name'])
                        if type(gset['order']) == types.ListType:
                            gset_order = gset['order']
                        else:
                            raise AddGradeError('value "order" is not a list')
                    except KeyError as e:
                        raise AddGradeError(u'JSON does not contain "%s" key.' % e.args[0])

                    try:
                        gset_order_new = []
                        for grade in gset_order:
                            if type(grade) != types.ListType:raise TypeError

                            grade_d = {}
                            grade_d['courseid'] = int(grade[0])
                            grade_d['expr'] = unicode(grade[1])

                            crsinfo = dpi_sock.getcourseinfo(grade_d['courseid'])
                            if crsinfo == None:
                                raise Exception('could not get course infomation, check courseid %d' % grade_d['courseid'])
                            crs_et = crsinfo.xpath('/courselist/course').pop()

                            grade_d['name'] = crs_et.find('title').text
                            grade_d['hash'] = crs_et.find('hash').text

                            gset_order_new.append(grade_d)
                    except TypeError:
                        raise AddGradeError('course entry must be a list contains at least 2 elements [int courseid, string repr].')
                    except IndexError:
                        raise AddGradeError('course entry must be a list contains at least 2 elements [int courseid, string repr].')
                    except AttributeError:
                        raise AddGradeError('invalid course infomation')
                    except Exception as e:
                        raise AddGradeError('error(%s)' % unicode(e))

                    try:
                        # add grade set and all grades to shared db
                        cur.execute(u'''
                            INSERT INTO exgrade_set(name,lastupdate,active)
                            VALUES(?,0,1)
                        ''', (gset_name,))
                        cur.execute(u'''
                            SELECT id FROM exgrade_set WHERE name=?
                        ''',(gset_name,))
                        set_id = cur.fetchone()['id']
                        level = 1.
                        for grade in gset_order_new:
                            params_dict = dict([('set_id',set_id), ('level', level)] + grade.items())
                            cur.execute('''
                                INSERT INTO exgrade_grade(set_id,level,courseid,hash,name,expr)
                                VALUES(:set_id,:level,:courseid,:hash,:name,:expr)
                            ''',params_dict)
                            level += 1.
                        shared_db.conn.commit()
                    except Exception as e:
                        shared_db.conn.rollback()
                        raise AddGradeError('SQL error during adding courses(%s)' % unicode(e))

                    try:
                        # import data of achiever(s) for each grade(s)
                        time_now = int(time.time())
                        register_achiever(gset_order_new)
                        cur.execute('''
                            UPDATE exgrade_set SET lastupdate=? WHERE id=?
                        ''',(time_now,set_id,))
                        shared_db.conn.commit()
                    except:
                        shared_db.conn.rollback()
                        raise AddGradeError('SQL error during registering achiever(s)')

                    # all operations succeeded
                    rt.xpath('/html/body/div/div').pop().text += u'Successfully imported: %s' % (gset_name)

                except AddGradeError as e:
                    rt.xpath('/html/body/div/div').pop().text += unicode(e)

            rt = append_exgradebox(rt)

        result['res'] = res
        result['res_etree'] = rt

    else:
        # 'edit_response'
        if not 'res_etree' in result:
            result['res_etree'] = lxml.html.fromstring(result['res_body'].decode('cp932',errors='ignore'))
        rt = result['res_etree']

        if q_dict.get('mode') and 'ranking' in q_dict.get('mode'):
            # access to /~lavalse/LR2IR/search.cgi with query 'mode=ranking'
            # adds exgrade(s) info to each user
            ranking_table = rt.xpath('/html/body/div/div/table')[-1]
            try:
                ranking_lr2id = [(int(parse_qs(tr[1][0].get('href'))['playerid'].pop()),) for tr in ranking_table[1::2]]
            except:
                ranking_lr2id = []
            exgrades = []
            for lr2id in ranking_lr2id:
                cur.execute('''
                    SELECT expr FROM exgrade_grade AS eg
                    INNER JOIN (
                        SELECT set_id, MAX(level) AS maxlv FROM exgrade_grade
                        WHERE courseid IN (SELECT crs_id FROM exgrade_achiever WHERE lr2id=?)
                              AND set_id IN (SELECT id FROM exgrade_set WHERE active != 0)
                        GROUP BY set_id
                    ) AS bg ON eg.set_id=bg.set_id AND eg.level=bg.maxlv
                    ORDER BY eg.set_id ASC
                    ''', lr2id)
                exgrades.append(cur.fetchall())
            def update_text(s):
                if s[0]:
                    s[1][2].append(lxml.html.fromstring('<br>'))
                    s[1][2][0].tail = '/'.join([exg['expr'] for exg in s[0]])
                return s
            map(update_text, zip(exgrades,ranking_table[1::2]))

        if (q_dict.get('mode') and 'mypage' in q_dict.get('mode')) and (q_dict.get('playerid')):
            # access to /~lavalse/LR2IR/search.cgi with query 'mode=ranking'
            # adds exgrade(s) info to mypage
            try:
                playerid = int(q_dict.get('playerid')[0])
                grade_cell = rt.xpath('/html/body/div/div/table[@border="0"]/tr/td')
            except:
                playerid = 0
            if playerid and len(grade_cell) > 2:
                grade_cell = grade_cell[2]
                cur.execute('''
                    SELECT expr FROM exgrade_grade AS eg
                    INNER JOIN (
                        SELECT set_id, MAX(level) AS maxlv FROM exgrade_grade
                        WHERE courseid IN (SELECT crs_id FROM exgrade_achiever WHERE lr2id=?)
                              AND set_id IN (SELECT id FROM exgrade_set WHERE active!=0)
                        GROUP BY set_id
                    ) AS bg ON eg.set_id=bg.set_id AND eg.level=bg.maxlv
                    ORDER BY eg.set_id ASC
                    ''', (playerid,))
                exgrades = cur.fetchall()
                if exgrades:
                    grade_cell.text += ' / ' + ' / '.join([exg['expr'] for exg in exgrades])

    return extend_link.func(result)


# initialize
init()

if __name__ == '__main__':
    pass
