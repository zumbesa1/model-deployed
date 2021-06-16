from flask import request,render_template, url_for, redirect
from tensorflow import keras
import numpy as np

from app import spotify
from app import app


app_data = {
    "name":         "Spotify",
    "description":  "Spotify",
    "author":       "ZHAW ",
    "html_title":   "Spotify App",
    "project_name": "Spotify App",
    "keywords":     "flask, webapp, Hubspot, curaMed"
}


@app.route('/',methods=['GET', 'POST'])
def index():
    return render_template("home.html",app_data=app_data)
    
@app.route('/mood', methods=['GET','POST'])
def getmood():
    if request.method == 'POST':
        song_uri = request.form['song_uri']

        # preprocess -> get values from spotify api 
        # Test song "1v07K6OsaUuhyqf9Z2KBOk"
        mood,track_data, album_data = spotify.features(song_uri)

        recommendations = spotify.get_album_tracks(album_data['id'], track_data['id'], mood)

        
        if mood == "error":
            return render_template("error.html",app_data=app_data)
        else:
            return render_template(
                'prediction.html',
                app_data=app_data, 
                track = track_data, 
                mood=mood, album=album_data, 
                recommendations= recommendations
                )

    return render_template("index.html", app_data=app_data)




@app.route('/playlist',  methods=['GET','POST'])
def favplaylist():
    show_data = False
    tracks_data = []
    if request.method == 'POST':
        playlist_url = request.form['playlist_uri']
        desired_mood = request.form['mood_selection']
        
        tracks_data = spotify.get_playlist_Tracks(playlist_url, desired_mood)

        show_data = True


    return render_template(
        "playlist.html", 
        app_data=app_data, 
        show_data = show_data,
        tracks = tracks_data
        )




@app.route('/predict')
def about():
    return render_template("predict.html")
