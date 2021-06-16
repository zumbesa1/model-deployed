import spotipy 
import sys
from tensorflow import keras
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
import time
import pandas as pd 
import numpy as np

# Spotify App credentials 
# ----------------------------------
cid ='c1db8928479f4dfd9493cb7b194e6d10' 
secret = '0b10756f55784276954fa668f56373f8' 
username = 'Michael.schneidermx' 

scope = 'user-library-read playlist-modify-public playlist-read-private'
redirect_uri='http://localhost:8910/callback'
client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
token = util.prompt_for_user_token(username, scope, cid, secret, redirect_uri)

if token:
    sp = spotipy.Spotify(auth=token)
else:
    print("Can't get token for", username) 

#Credentials to access the Spotify Music Data
manager = SpotifyClientCredentials(cid,secret)
sp = spotipy.Spotify(client_credentials_manager=manager) 

#END: Spotify credentials setup 
# ----------------------------------


# Load the Keras ML Model
# ----------------------------------
model = keras.models.load_model("app/assets/spotify_v2.h5")



# Functions called from View.py
# ----------------------------------

def features(song_uri):

    track_features = []

    # get the song id from the uri 
    temp = song_uri.split("track/",1)[1]
    song_id = temp.split('?',1)[0]

    track, columns,track_data,album_data = get_songs_features(song_id)



    track_features.append(track)
    #song_features = pd.DataFrame(track_features,columns=columns)
    song_features = pd.DataFrame(track_features)
    #print(song_features.shape)
    song_features = song_features.astype('float32')
    #print(song_features)
    #song_features = song_features.to_dict('records')[0]
    song_features = song_features.values.tolist()
    #print(song_features)
    

    mood = predict_mood(song_features)

    return mood,track_data,album_data

def get_album_tracks(album_id, root_track_id, root_mood):
    album_tracks = sp.album_tracks(album_id)
    recommendations = []

    tracks = album_tracks['items']

    

    for track in tracks:
        if root_track_id != track['id']: 
            track_features = []
            track_id = track['id']
            track_name = track['name']
            track_artists = track['artists']
            track_duration = track['duration_ms']
            track_number = track['track_number']
            track_preview_url = track['preview_url']
            track_mood = ""
            track_popularity = ""

            feat = sp.audio_features(track_id)        
            features, columns = prepate_featuredata(feat)
            track_features.append(features)
            song_features = pd.DataFrame(track_features)
            song_features = song_features.astype('float32')
            song_features = song_features.values.tolist()

            track_mood = predict_mood(song_features)

            track_meta = sp.track(track_id)
            track_popularity = track_meta['popularity']

            track_data = {
                'id': track_id,
                'name': track_name,
                'artists': track_artists,
                'duration' :track_duration,
                'popularity': track_popularity,
                'tracknr': track_number,
                'preview_url': track_preview_url,
                'mood': track_mood
            }

            recommendations.append(track_data)

    recommendations = get_most_popular_tracks(recommendations, root_mood)

    return recommendations

def get_playlist_Tracks(playlist_url, desired_mood):

    playlist_id = get_id_outof_link(playlist_url, "playlist")

    playlist_data = sp.playlist_items(playlist_id)

    playlist_tracks = playlist_get_Tracks(playlist_data)

    desired_tracks = filter_tracks_by_mood(playlist_tracks, desired_mood)

    return desired_tracks

# END: Functions called from View.py
# ----------------------------------
   


# Functions called from spotify.py
# ----------------------------------


def predict_mood(song_features):
        try:
            # Predict the song mood        
            pred = model.predict(song_features)
            pred = np.around(pred,0)

            #[row,columns]
            res = np.where(pred==1)
            res = res[1]
            
            # Map the moods to the val
            if res == 0:
                mood = 'calm'
            elif res == 1:
                mood = 'energetic'
            elif res == 2:
                mood = 'happy'
            elif res == 3:
                mood = 'sad'     

            
            return mood
        except:
            return "error"

def get_songs_features(track_ids):

    meta = sp.track(track_ids)
    features = sp.audio_features(track_ids)

    album_data,track_data = prepate_metadata(meta)
    
    track_features, columns = prepate_featuredata(features)

    return track_features,columns,track_data, album_data

def prepate_metadata(meta):

    album = {
        'id': meta['album']['id'],
        'name': meta['album']['name'],
        'img_uri': meta['album']['images'][0]['url'],
        'release_date' : meta['album']['release_date'] ,
        'artist_name': meta['album']['artists'][0]['name'],
        'artist_id': meta['album']['artists'][0]['id'],
        'artist_uri': meta['album']['artists'][0]['uri']
    }
    track = {
        'name': meta['name'],
        'artists': meta['artists'],
        'duration': meta['duration_ms'],
        'preview_url': meta['preview_url'],
        'popularty': meta['popularity'],
        'id': meta['id']
    }  

    return album, track

def prepate_featuredata(features):

        # features
    acousticness = features[0]['acousticness']
    danceability = features[0]['danceability']
    energy = features[0]['energy']
    instrumentalness = features[0]['instrumentalness']
    liveness = features[0]['liveness']
    valence = features[0]['valence']
    loudness = features[0]['loudness']
    speechiness = features[0]['speechiness']
    tempo = features[0]['tempo']

    track_features = [danceability, acousticness,
            energy, instrumentalness, liveness, valence, loudness, speechiness, tempo]
    columns = ['danceability','acousticness','energy','instrumentalness',
                'liveness','valence','loudness','speechiness','tempo']

    return track_features,columns

def get_most_popular_tracks(recommendations, root_mood):
    most_popular_and_same_mood = []
    recommendations_length = 0

    for recommendation in recommendations:        
        if recommendation['mood'] == root_mood:
            most_popular_and_same_mood.append(recommendation)
            recommendations_length = recommendations_length+1

    if  recommendations_length> 4:
        most_popular_and_same_mood = reduce_list(most_popular_and_same_mood)

    return most_popular_and_same_mood

def reduce_list(tracks_list):
    popularities_list = []
    for track in tracks_list:
        popularity = track['popularity']
        popularities_list.append(popularity)

    
    pop_list_size = len(popularities_list)
    popularities_list.sort()

    while 5 <= pop_list_size:
        for track in tracks_list:
            if track['popularity'] == min(popularities_list):
                tracks_list.remove(track)
        pop_list_size = pop_list_size-1  
        popularities_list.remove(min(popularities_list))

    return tracks_list

def get_id_outof_link(url, entity):
    id = ""

    if entity == "playlist":
        temp = url.split("playlist/",1)[1]
        id = temp.split('?',1)[0]

    elif entity == "track":
        temp = url.split("track/",1)[1]
        id = temp.split('?',1)[0]

    elif entity == "album":
        temp = url.split("album/",1)[1]
        id = temp.split('?',1)[0]


    if id == "":
        return "Sorry, there is no ID we can find"
    

    return id

def playlist_get_Tracks(data):
    items = data['items']
    tracks_list = []
    predicted_mood = "lol"
    for item in items:
        track_features = []
        track = item['track'] 
      
        feat = sp.audio_features(track['id'])        
        features, columns = prepate_featuredata(feat)
        track_features.append(features)
        song_features = pd.DataFrame(track_features)
        song_features = song_features.astype('float32')
        song_features = song_features.values.tolist()

        duration = convert_ms_to_min(track['duration_ms'],)

        predicted_mood = predict_mood(song_features)
        track_data = {            
            'track_id': track['id'],
            'track_name': track['name'],
            'track_artists': track['artists'],
            'track_duration': duration,
            'track_preview_url': track['preview_url'],
            'track_popularty': track['popularity'],
            'track_mood': predicted_mood,
            'album_id': track['album']['id'],
            'album_name': track['album']['name'],
            'album_img_uri': track['album']['images'][0]['url'],
            'album_release_date' : track['album']['release_date'] ,
            'album_artist_name': track['album']['artists'][0]['name'],
            'album_artist_id': track['album']['artists'][0]['id'],
            'album_artist_uri': track['album']['artists'][0]['uri']
        }
        tracks_list.append(track_data)



    return tracks_list

def filter_tracks_by_mood(tracks, mood):
    new_tracks_list = []

    for track in tracks:
        if track['track_mood'] == mood:
            new_tracks_list.append(track)

    return new_tracks_list

def convert_ms_to_min(ms):
    millis = ms
    seconds=(millis/1000)%60
    seconds = int(seconds)
    minutes=(millis/(1000*60))%60

    duration =  ("%d:%d" % (minutes, seconds))

    return duration
# END : Functions called from spotify.py
# ----------------------------------