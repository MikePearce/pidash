#!/usr/bin/env python

# import the Flask class from the flask module
from flask import Flask, render_template, flash, redirect, url_for
from lib.photos import Photos

# create the application object
app = Flask(__name__)

app.config.update(dict(
    SECRET_KEY='development key',
))

@app.route('/')
def welcome():
    photos = Photos()

    fotos = photos.get_photo_list()

    return render_template(
        'welcome.html',
        photos=fotos
    )

# start the server with the 'run()' method
if __name__ == '__main__':

    # gunicorn
    #app.run(debug=True, threaded=True)

    # Flask
    app.run(debug=True)