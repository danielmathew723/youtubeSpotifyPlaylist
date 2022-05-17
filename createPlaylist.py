# all the libraries we'll need
import json
import os
import requests
import sys
from youtube_title_parse import get_artist_title

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

# this is for the Google API, which specifies what we're going to do with the data we retrieve
scopes = ["https://www.googleapis.com/auth/youtube.readonly"]


# get id of youtube playlist that you are taking videos from
def get_playlist_id(playlist_name):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "client_secret_386197436539-v4o3p4ov2kt7f4j039p1r1qt4jfekimk.apps.googleusercontent.com.json"

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_console()
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    request = youtube.playlists().list(
        part="snippet",
        maxResults=25,
        mine=True
    )
    response = request.execute()
    # everything above was taken from the Google API
    # and everything below is what I added in
    # what this does is it takes the data retrieved by the API and parses it out so that I can get the only piece of data I actually need,
    # which is the id of the youtube playlist
    for item in response['items']:
        if item['snippet']['title'] == playlist_name:
            return item['id']
        else:
            continue


# get titles from the playlist
def get_song_titles(playlist_id):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "client_secret_386197436539-v4o3p4ov2kt7f4j039p1r1qt4jfekimk.apps.googleusercontent.com.json"

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_console()
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    request = youtube.playlistItems().list(
        part="snippet",
        maxResults=50,
        playlistId=playlist_id,
    )
    response = request.execute()
    # ^ from Google API
    # everything down here is from yours truly
    # this parsed out the API response, and just returned the titles of each song in the yt playlist
    # then it put each song title in a list and returned that list
    playlist_items = response['items']
    song_titles = []
    for item in playlist_items:
        title = item['snippet']['title']
        # the function below was downloaded from the Internet
        artist, song = get_artist_title(title)
        song_titles.append(song)
    return song_titles


# creates spotify playlist and returns its id
def create_spotify_playlist(playlist_name, id, token):  # requires a name, a user id, and a token that the person can make off the Spotify website
    playlist_body = json.dumps({  # request body data which is being turned into json script
        "name": playlist_name,
        "public": True
    })

    # playlist endpoint: not sure what it does but it's necessary
    playlist_endpoint = f"https://api.spotify.com/v1/users/{id}/playlists"
    # makes an http request (meaning it searches up whatever is in the parameters on the browser)
    playlist_request = requests.post(
        playlist_endpoint,  # this and everything below is based off Spotify Web API docs
        data=playlist_body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    )
    # ^ from Spotify API, which creates a Spotify playlist and needs the id of the user and a token
    # the token authorizes the app to make a playlist
    # not as much work needed from me here down below
    # just had to find the id of the playlist from the response given by Spotify and return it
    playlist_json = playlist_request.json()
    playlist_id = playlist_json["id"]
    return playlist_id


# searches spotify for song titles and adds it to newly created playlist
def add_songs(query, playlist_id, token):  # token is the same, playlist_id was given by the function above
    # query is the only thing that is different: it just means the song title, so when the API adds a song to a playlist,
    # it knows the name of the song that needs to be added
    search_endpoint = f"https://api.spotify.com/v1/search?q={query}&type=track"

    search_request = requests.get(
        search_endpoint,
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    search_json = search_request.json()
    search_id = search_json["tracks"]["items"][0]["id"]
    # Add liked songs to Spotify playlist
    add_items_endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?uris=spotify%3Atrack%3A{search_id}"
    add_items_request = requests.post(
        add_items_endpoint,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    # ^ all from Spotify API
    # nothing needed from me except adding the token, playlist id, and the query


# now we gotta run everything
if __name__ == '__main__':
    print("Hello! This app will take your liked songs in a YouTube playlist of your choice and "
          "add them to a newly created playlist on your Spotify!")
    # loops so that if an incorrect playlist name was inputted, it would re-prompt the user
    while True:
        try:
            yt_playlist_name = input("Enter the exact name of the YouTube playlist that has your favorite songs: ")
            yt_playlist_id = get_playlist_id(yt_playlist_name)
            break
        except:
            print("There is no playlist that matches that name.")

    try:
        song_titles = get_song_titles(yt_playlist_id)
    except:  # exits the program if there was an error in retrieving the songs
        print("There was an error in retrieving your songs.")
        sys.exit()

    # asks user for user id
    sp_user_id = input(
        "Enter your Spotify user ID. This can be found by going to your profile, clicking 'Share', and copying your Spotify URI. "
        "The string of numbers and letters after 'spotify:user:' is your ID: ")

    # asks user for the name of the playlist they want to make
    sp_playlist_name = input(
        "Now we're gonna make a new playlist on your Spotify. Enter the name you would like for the playlist: ")

    # wow lot's of text
    # asks user to input a token to authorize the program. Without it, we won't be able to make a playlist or add songs
    token = input(
        "Now go to this url https://developer.spotify.com/console/post-playlists/?user_id=&body=%7B%22name%22%3A%22New%20Playlist%22%2C%22description%22%3A%22New%20playlist%20description%22%2C%22public%22%3Afalse%7D, "
        "click Get Token, and checkmark either playlist-modify-public or private (it doesn't matter which). "
        "Click Request Token and copy and paste it here: ")

    # makes a playlist and returns the id in this variable
    sp_playlist_id = create_spotify_playlist(sp_playlist_name, sp_user_id, token)

    # i have to change the titles so that the Spotify API can use them
    # it requires that each space be a '+' or a '%20'
    # after changing the names, I put the new titles into another list
    alt_song_titles = []
    for title in song_titles:
        new_title = ''
        for letter in title:
            if letter == ' ':
                new_title += '+'  # replacing spaces with '+' because spotify api reads it like that
            elif letter.isalnum():
                new_title += letter
            else:
                break
        alt_song_titles.append(new_title)

    # this adds each song from the new list into the playlist
    for title in alt_song_titles:
        add_songs(title, sp_playlist_id, token)

    print("Check your Spotify!")
