"""
Twitter/X Upload - VELOCITY HEBREW
"""
import os, sys, time, tweepy
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

def upload_to_twitter(video_path, caption):
    api_key = os.getenv('TWITTER_API_KEY', '').strip()
    api_secret = os.getenv('TWITTER_API_SECRET', '').strip()
    at = os.getenv('TWITTER_ACCESS_TOKEN', '').strip()
    aSecret = os.getenv('TWITTER_ACCESS_SECRET', '').strip()
    if not all([api_key, api_secret, at, aSecret]): raise ValueError("Missing Twitter credentials")
    auth = tweepy.OAuth1UserHandler(api_key, api_secret, at, aSecret)
    api_v1 = tweepy.API(auth)
    client = tweepy.Client(consumer_key=api_key, consumer_secret=api_secret, access_token=at, access_token_secret=aSecret)
    media = api_v1.media_upload(filename=str(video_path), media_category='tweet_video', chunked=True)
    time.sleep(5)
    tweet = client.create_tweet(text=caption[:280], media_ids=[media.media_id])
    return {'id': tweet.data['id'], 'url': f"https://twitter.com/i/web/status/{tweet.data['id']}", 'platform': 'twitter'}

if __name__ == '__main__':
    v = Path('final_video.mp4')
    if v.exists(): upload_to_twitter(v, "Test")
