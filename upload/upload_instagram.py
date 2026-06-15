"""
Instagram Reels Upload - VELOCITY HEBREW
"""
import os, requests, time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def upload_to_instagram(video_path, caption, is_story=False):
    media_type = 'STORIES' if is_story else 'REELS'
    print("\n" + "=" * 60)
    print(f"INSTAGRAM {media_type} UPLOAD")
    print("=" * 60)
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN') or os.getenv('FACEBOOK_ACCESS_TOKEN')
    user_id = os.getenv('INSTAGRAM_ACCOUNT_ID') or os.getenv('IG_USER_ID')
    if not access_token: raise ValueError("INSTAGRAM_ACCESS_TOKEN not set")
    if not user_id: raise ValueError("INSTAGRAM_ACCOUNT_ID not set")
    video_path_obj = Path(video_path)
    if not video_path_obj.exists(): raise FileNotFoundError(f"Video not found: {video_path}")
    caption_limited = caption[:2200] if len(caption) > 2200 else caption
    try:
        with open(video_path_obj, 'rb') as vf:
            files = {'file': ('video.mp4', vf, 'video/mp4')}
            temp_resp = requests.post('https://tmpfiles.org/api/v1/upload', files=files, timeout=180)
        if temp_resp.status_code != 200: raise Exception(f"Hosting failed: {temp_resp.status_code}")
        temp_data = temp_resp.json()
        if temp_data.get('status') != 'success': raise Exception(f"Hosting failed: {temp_data}")
        video_url = temp_data['data']['url'].replace('tmpfiles.org/', 'tmpfiles.org/dl/')
        container_url = f"https://graph.instagram.com/v21.0/{user_id}/media"
        params = {'media_type': media_type, 'video_url': video_url, 'access_token': access_token}
        if not is_story:
            params['caption'] = caption_limited
            params['share_to_feed'] = 'true'
        cont_resp = requests.post(container_url, params=params, timeout=60)
        if cont_resp.status_code != 200:
            container_url = f"https://graph.facebook.com/v21.0/{user_id}/media"
            cont_resp = requests.post(container_url, params=params, timeout=60)
            if cont_resp.status_code != 200: raise Exception(f"Container failed: {cont_resp.text}")
        container_id = cont_resp.json().get('id')
        max_wait = 180; waited = 0
        while waited < max_wait:
            status_url = f"https://graph.instagram.com/v21.0/{container_id}"
            st = requests.get(status_url, params={'fields': 'status_code', 'access_token': access_token}, timeout=30).json()
            sc = st.get('status_code', 'UNKNOWN')
            if sc == 'FINISHED': break
            if sc == 'ERROR': raise Exception(st.get('error_message', 'Processing failed'))
            time.sleep(10); waited += 10
        if waited >= max_wait: raise Exception("Processing timed out")
        time.sleep(5)
        pub_url = f"https://graph.instagram.com/v21.0/{user_id}/media_publish"
        pub_resp = requests.post(pub_url, params={'creation_id': container_id, 'access_token': access_token}, timeout=60)
        if pub_resp.status_code != 200: raise Exception(f"Publish failed: {pub_resp.text}")
        media_id = pub_resp.json().get('id')
        return {'id': media_id, 'platform': 'instagram', 'status': 'success'}
    except Exception as e: print(f"[instagram] ERROR: {e}"); raise

if __name__ == '__main__':
    video_file = Path('final_video.mp4')
    if video_file.exists():
        try: upload_to_instagram(str(video_file), "Test")
        except Exception as e: print(f"Failed: {e}")
