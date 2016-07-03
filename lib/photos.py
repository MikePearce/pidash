#!/usr/bin/env python

import sqlite3
import os

class Photos:
    """ Get the photos from picasa api"""

    def __init__(self):
        app_root = os.path.expanduser('~/sites/pi_dash/')
        self.local_storage = os.path.join(app_root, 'static/offline_cache/')

        # Connect to db and create table.
        conn = sqlite3.connect(self.local_storage +'/photo_cache.sqlite')
        self.c = conn.cursor()

    def get_photo_list(self):

        self.c.execute("SELECT * FROM photos LIMIT 10")
        res = self.c.fetchall()

        return res