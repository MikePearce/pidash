#!/usr/bin/env python

import gdata
import gdata.photos.service
import gdata.media
import gdata.geo
import gdata.gauth
import httplib2
import os
import urllib
import json
import datetime
import sqlite3

import webbrowser

from datetime import datetime, timedelta
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage


class getPhotos:
    """ Get the photos from picasa api"""

    def __init__(self):
        self.scope = 'https://picasaweb.google.com/data/'
        self.user_agent = 'pi_dash'
        email = 'mike@pearce.be'
        self.location = 'No location data'
        self.old_lat_long = '0,0'
        self.old_location = self.location
        app_root = os.path.expanduser('~/sites/pi_dash/')
        self.local_storage = os.path.join(app_root, 'static/offline_cache/')

        self.gd_client = self.OAuth2Login(
            os.path.join(app_root, 'config/client_secrets.json'),
            os.path.join(app_root, 'config/credentials.dat'),
            email
        )

        # Connect to db and create table.
        conn = sqlite3.connect(self.local_storage +'photo_cache.sqlite')
        c = conn.cursor()

        # Creat the cache table
        self.create_cache_table(c)

        # Get the photos
        photos = self.get_user_feed_hi_res(
            kind='photo',
            limit=200
        )

        # For each photo
        for photo in photos.entry:

            # Download it
            self.download_photo(photo.content.src)

            # Save the details
            self.store_photo_details(
                photo.timestamp.text,
                photo.geo.Point.pos.text,
                photo.title.text,
                c
            )

        # Commit all the things
        conn.commit()

        # Close the connection
        c.close

        print 'Downloaded 200 photos'

    def OAuth2Login(self, client_secrets, credential_store, email):
        """ oAuth2 login: check and see if there are any stored creds, otherwise, go get some,"""

        storage = Storage(credential_store)
        credentials = storage.get()

        # If there aren't any credentials, go and get some.
        if credentials is None or credentials.invalid:
            flow = flow_from_clientsecrets(client_secrets, scope=scope, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            uri = flow.step1_get_authorize_url()
            webbrowser.open(uri)
            code = raw_input('Enter the authentication code: ').strip()
            credentials = flow.step2_exchange(code)

        # If they haven't expired, use them
        if (credentials.token_expiry - datetime.utcnow()) < timedelta(minutes=5):
            http = httplib2.Http()
            http = credentials.authorize(http)
            credentials.refresh(http)

        # Re-save them
        storage.put(credentials)

        # Create the gd_client
        gd_client = gdata.photos.service.PhotosService(
            source=self.user_agent,
            email=email,
            additional_headers={'Authorization' : 'Bearer %s' % credentials.access_token}
        )

        return gd_client

    def get_user_feed_hi_res(self, kind='album', user='default', limit=None):
        """ Get a set of hi-res images """

        uri = "/data/feed/api/user/%s?kind=%s&imgmax=1024" % (user, kind)
        return self.gd_client.GetFeed(uri, limit=limit)

    def download_photo(self, url):
        """ Download the photo locall, of offline caching """

        store = self.local_storage + "/" + url.split('/')[-1]

        if os.path.isfile(store) is not True:
            urllib.urlretrieve(url, store)

    def store_photo_details(self, ts, location, filename, c):
        """ Store the photo meta locally, for offline caching """

        # Date taken
        timestamp = int(ts) / 1000
        date_taken = (
            datetime.fromtimestamp(
                int(timestamp)
            ).strftime('%Y-%m-%d %H:%M:%S')
        )

        # Geolocation
        geo = self.get_location_details(location)

        c.execute('INSERT INTO photos (filename, geo, date) VALUES (?,?,?)',
                  (filename, geo, date_taken))

    def get_location_details(self, pos):
        """ Grab the location data from google maps API """

        location = 'No Location Available'

        # Check we have data
        if pos is not None:

            # Check it's not a dupe
            lat_long = pos.replace(" ", ",")

            if lat_long != self.old_lat_long:
                url = 'http://maps.googleapis.com/maps/api/geocode/json?latlng=%s&sensor=false' %(lat_long)
                data = json.load(urllib.urlopen(url))
                try:
                    location = data['results'][1]['formatted_address']
                except IndexError:
                    print data['error_message']
                except:
                    print "Some google maps API error"

                self.old_lat_long = lat_long
                self.old_location = location
            else:
                location = self.old_location

        return location

    def create_cache_table(self, c):
        """ Create the cache table """
        c.execute('''DROP TABLE IF EXISTS photos''')
        c.execute(
            '''CREATE TABLE IF NOT EXISTS photos (filename TEXT NOT NULL, geo TEXT NOT NULL, date TEXT NOT NULL)''')


if __name__ == '__main__':

    gp = getPhotos()
