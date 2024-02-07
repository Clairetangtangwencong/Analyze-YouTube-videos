from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import urllib.parse as p
import re
import os
import pickle
import math
import pandas as pd
from datetime import date
from datetime import timedelta

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

def youtube_authenticate():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "credentials.json"
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build(api_service_name, api_version, credentials=creds)

# authenticate to YouTube API
youtube = youtube_authenticate()

def parse_channel_url(url):
    """
    This function takes channel `url` to check whether it includes a
    channel ID, user ID or channel name
    """
    path = p.urlparse(url).path
    id = path.split("/")[-1]
    if "/c/" in path:
        return "c", id
    elif "/channel/" in path:
        return "channel", id
    elif "/user/" in path:
        return "user", id

def get_channel_id_by_url(youtube, url):
    """
    Returns channel ID of a given `id` and `method`
    - `method` (str): can be 'c', 'channel', 'user'
    - `id` (str): if method is 'c', then `id` is display name
        if method is 'channel', then it's channel id
        if method is 'user', then it's username
    """
    # parse the channel URL
    method, id = parse_channel_url(url)
    if method == "channel":
        # if it's a channel ID, then just return it
        return id
    elif method == "user":
        # if it's a user ID, make a request to get the channel ID
        response = get_channel_details(youtube, forUsername=id)
        items = response.get("items")
        if items:
            channel_id = items[0].get("id")
            return channel_id
    elif method == "c":
        # if it's a channel name, search for the channel using the name
        # may be inaccurate
        response = search(youtube, q=id, maxResults=1)
        items = response.get("items")
        if items:
            channel_id = items[0]["snippet"]["channelId"]
            return channel_id
    raise Exception(f"Cannot find ID:{id} with {method} method")

def get_channel_videos(youtube, **kwargs):
    return youtube.search().list(
        **kwargs
    ).execute()


def get_channel_details(youtube, **kwargs):
    return youtube.channels().list(
        part="statistics,snippet,contentDetails",
        **kwargs
    ).execute()

def get_video_id_by_url(url):
    """
    Return the Video ID from the video `url`
    """
    # split URL parts
    parsed_url = p.urlparse(url)
    # get the video ID by parsing the query of the URL
    video_id = p.parse_qs(parsed_url.query).get("v")
    if video_id:
        return video_id[0]
    else:
        raise Exception(f"Wasn't able to parse video URL: {url}")
        
def get_video_details(youtube, **kwargs):
    return youtube.videos().list(
        part="snippet,contentDetails,statistics",
        **kwargs
    ).execute()

def print_video_infos(video_response):
    today_date = date.today()
    items = video_response.get("items")[0]
    # get the snippet, statistics & content details from the video response
    snippet         = items["snippet"]
    statistics      = items["statistics"]
    content_details = items["contentDetails"]
    # get infos from the snippet
    # channel_title = snippet["channelTitle"]
    title         = snippet["title"]
    #description   = snippet["description"]
    publish_time  = snippet["publishedAt"]
    # get stats infos
    comment_count = statistics["commentCount"]
    like_count    = statistics["likeCount"]
    view_count    = statistics["viewCount"]
    stats = {
        "Video Title": title,
        "Views":view_count,
        "Likes":like_count,
        "Comments":comment_count 
    }
    stats_df = pd.DataFrame(stats, index = [today_date])
    """
    stats = [title, view_count, like_count, comment_count]
    """
    return stats_df

channel_url = "https://www.youtube.com/channel/UCJL8hLQRqF28KRIwiMlnO7w"
# get the channel ID from the URL
channel_id = get_channel_id_by_url(youtube, channel_url)
# get the channel details
response = get_channel_details(youtube, id=channel_id)
# extract channel infos
snippet = response["items"][0]["snippet"]
statistics = response["items"][0]["statistics"]

channel_video_count = statistics["videoCount"]

# the following is grabbing channel videos
# number of pages you want to get
n_pages = math.ceil(int(channel_video_count) / 5)
# counting number of videos grabbed
n_videos = 0
next_page_token = None
video_urls = []
for i in range(n_pages):
    params = {
        'part': 'snippet',
        'q': '',
        'channelId': channel_id,
        'type': 'video',
    }
    if next_page_token:
        params['pageToken'] = next_page_token
    res = get_channel_videos(youtube, **params)
    channel_videos = res.get("items")
    for video in channel_videos:
        n_videos += 1
        video_id = video["id"]["videoId"]
        # easily construct video URL by its ID
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        video_urls.append(video_url)
    # if there is a next page, then add it to our parameters
    # to proceed to the next page
    if "nextPageToken" in res:
        next_page_token = res["nextPageToken"]

video_data = pd.DataFrame(columns=["Video Title", "Views", "Likes", "Comments"])
for i in video_urls:
    video_id = get_video_id_by_url(i)
    # make API call to get video info
    response = get_video_details(youtube, id=video_id)
    # print extracted video infos
    single_video_data = print_video_infos(response)
    video_data = pd.concat([video_data,single_video_data])

path = "/Users/clairetang/1 platform monitor/API/Data/"

today_date = date.today().strftime("%Y-%m-%d")
yesterday_date = (date.today() - timedelta(days = 1)).strftime("%Y-%m-%d")

yesterday_df = pd.read_csv(path + yesterday_date + ".csv")

up_to_today_df = pd.concat([video_data.reset_index(), yesterday_df], join="outer")

up_to_today_df.to_csv(path + today_date + ".csv", index = False)
