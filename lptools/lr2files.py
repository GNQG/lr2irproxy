#coding: utf-8

import sqlite3
import os
from glob import glob

import lxml.etree

# path to LR2files
LR2files = '../LR2files'

scoredb_path = glob(os.path.join(LR2files,'Database/Score/*.db'))
scoredb_dict = {}
id_db_dict = {}

for scoredb in scoredb_path:
    dbname = os.path.basename(scoredb)
    username = dbname[:dbname.find('.db')]
    scoredb_dict[username] = sqlite3.connect(scoredb)
    scoredb_dict[username].row_factory = sqlite3.Row
    cur = scoredb_dict[username].cursor()
    cur.execute('SELECT irid FROM player WHERE irid IS NOT NULL')
    irid = cur.fetchone()
    if irid:
        id_db_dict[str(irid['irid'])] = scoredb_dict[username]



def main():
    pass

if __name__ == '__main__':
    main()
