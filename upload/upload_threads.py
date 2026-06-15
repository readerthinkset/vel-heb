"""
Threads Upload - VELOCITY HEBREW
"""
import os, requests, time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

def upload_to_threads(video_path, text):
    access_token = os.getenv('THREADS_ACCESS_TOKEN')
    user_id = os.getenv('THREADS_USER_ID')
    if not access_token: raise ValueError("THREADS_ACCESS_TOKEN not set")
    if not user_id: raise ValueError("THREADS_USER_ID not set")
    video_url = None
    try:
        with open(video_path, 'rb') as vf:
            r = requests.post('https://file.io/?expires=1d', files={'file': vf}, timeout=60)
        if r.status_code == 200 and r.json().get('success'): video_url = r.json().get('link')
    except: pass
    if not video_url:
        try:
            with open(video_path, 'rb') as vf:
                r = requests.post('https://tmpfiles.org/api/v1/upload', files={'file': ('video.mp4', vf, 'video/mp4')}, timeout=180)
            if r.status_code == 200:
                u = r.json().get('data', {}).get('url', '')
                if u: video_url = u.replace('tmpfiles.org/', 'tmpfiles.org/dl/')
        except: pass
    if not video_url: raise Exception("Hosting failed")
    for ver in ['v1.0', 'v18.0']:
        url = f"https://graph.threads.net/{ver}/{user_id}/threads"
        r = requests.post(url, params={'media_type': 'VIDEO', 'video_url': video_url, 'text': text[:500], 'access_token': access_token}, timeout=60)
        if r.status_code == 200:
            cid = r.json().get('id')
            if cid:
                max_wait = 120; waited = 0
                while waited < max_wait:
                    s = requests.get(f"https://graph.threads.net/v1.0/{cid}", params={'fields': 'status', 'access_token': access_token}, timeout=30).json()
                    if s.get('status') == 'FINISHED': break
                    if s.get('status') == 'ERROR': raise Exception(s.get('error_message'))
                    time.sleep(10); waited += 10
                if waited >= max_wait: raise Exception("Timed out")
                pub = requests.post(f"https://graph.threads.net/v1.0/{user_id}/threads_publish", params={'creation_id': cid, 'access_token': access_token}, timeout=60)
                if pub.status_code == 200: return {'id': pub.json().get('id'), 'platform': 'threads', 'status': 'success'}
                raise Exception(f"Publish failed: {pub.text}")
    raise Exception("Container creation failed")

if __name__ == '__main__':
    v = Path('final_video.mp4')
    if v.exists():
        try: upload_to_threads(str(v), "Test")
        except: pass
