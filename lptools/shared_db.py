#coding: utf-8
import sqlite3
import os

conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),'data/shared.db'))
#conn.execute('PRAGMA foreign_keys=ON')
conn.row_factory = sqlite3.Row
