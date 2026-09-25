"""
Direct Resumable Instagram Reel & Story Uploader via Meta Graph API v21.0
With Auto Payload Compression (<12MB) & Smart Container Processing Polling.
Uses Facebook Page Access Token directly for connected Instagram Business accounts.
"""
import os
import sys
import time
import json
import requests
import pathlib
import subprocess

def upload_to_instagram(video_path, caption="", is_story=False):
    media_type = 'STORIES' if is_story else 'REELS'
    print("\n" + "=" * 60)
    print(f"INSTAGRAM {media_type} UPLOAD (Direct Resumable v21.0 + Auto-Compress)")
    print("=" * 60)

    # 1. Directly use Facebook Page Access Token or Instagram Access Token
    access_token = (
        os.getenv('FACEBOOK_ACCESS_TOKEN') or 
        os.getenv('FB_ACCESS_TOKEN') or 
        os.getenv('INSTAGRAM_ACCESS_TOKEN') or 
        os.getenv('IG_ACCESS_TOKEN')
    )
    
    # 2. Instagram Business Account ID
    user_id = os.getenv('INSTAGRAM_ACCOUNT_ID') or os.getenv('IG_USER_ID')

    if not access_token:
        print("[instagram] ⚠️ Skipping - missing access token")
        return {'status': 'skipped', 'reason': 'Missing access token', 'platform': 'instagram'}

    if not user_id:
        print("[instagram] ⚠️ Skipping - missing INSTAGRAM_ACCOUNT_ID")
        return {'status': 'skipped', 'reason': 'Missing Instagram Account ID', 'platform': 'instagram'}

    def mask(t):
        return f"{t[:6]}...{t[-4:]}" if t and len(t) > 10 else ("SET" if t else "MISSING")

    print(f"[instagram] Target Account ID: {user_id}")
    print(f"[instagram] Token: {mask(access_token)}")

    video_path_obj = pathlib.Path(video_path)
    if not video_path_obj.exists():
        print(f"[instagram] ❌ Video file not found: {video_path}")
        return {'status': 'failed', 'error': 'Video file not found', 'platform': 'instagram'}

    # Auto-compress video if payload > 12 MB to ensure 100% Meta direct upload success
    upload_file_path = str(video_path_obj)
    file_size = video_path_obj.stat().st_size
    
    if file_size > 12 * 1024 * 1024:
        print(f"[instagram] ℹ️ File size ({file_size/(1024*1024):.2f} MB) > 12MB. Optimizing with FFmpeg...")
        compressed_path = str(video_path_obj.parent / f"ig_opt_{video_path_obj.name}")
        try:
            cmd = [
                "ffmpeg", "-y", "-i", str(video_path_obj),
                "-fs", "11M",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                "-movflags", "+faststart",
                compressed_path
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            if os.path.exists(compressed_path) and os.path.getsize(compressed_path) > 0:
                upload_file_path = compressed_path
                file_size = os.path.getsize(compressed_path)
                print(f"[instagram] ✅ Optimized size: {file_size/(1024*1024):.2f} MB")
        except Exception as comp_err:
            print(f"[instagram] ⚠️ FFmpeg optimization notice: {comp_err}")

    api_base = "https://graph.facebook.com/v21.0"

    try:
        # Step 1: Create Resumable Container directly without extra pre-flight requests
        print(f"[instagram] Step 1: Creating resumable {media_type} container directly...")
        c_data = {
            'media_type': 'STORIES' if is_story else 'REELS',
            'upload_type': 'resumable',
            'caption': caption[:2200] if caption else '',
            'access_token': access_token
        }
        if not is_story:
            c_data['share_to_feed'] = 'false'

        c_res = requests.post(f"{api_base}/{user_id}/media", data=c_data, timeout=30)
        if c_res.status_code not in (200, 201):
            err_data = {}
            try:
                err_data = c_res.json().get('error', {})
            except Exception:
                pass
            err_msg = err_data.get('message', c_res.text)
            err_code = err_data.get('code')
            err_subcode = err_data.get('error_subcode')
            if err_subcode == 2207050:
                hint = " [ACCOUNT CHECKPOINT: Instagram has restricted this account. Log in via the Instagram mobile app or web to clear the checkpoint / prompt.]"
                raise Exception(f"Container creation failed: {err_msg} (code: {err_code}, subcode: {err_subcode}){hint}")
            raise Exception(f"Container creation failed: {err_msg} (code: {err_code}, subcode: {err_subcode})")

        c_data_res = c_res.json()
        container_id = c_data_res.get('id')
        upload_uri = c_data_res.get('uri')
        print(f"[instagram] ✅ Container ID: {container_id}")

        # Step 2: Transfer Video Bytes
        print("[instagram] Step 2: Transferring video bytes to Meta Servers...")
        with open(upload_file_path, 'rb') as f:
            video_bytes = f.read()

        up_headers = {
            'Authorization': f'OAuth {access_token}',
            'offset': '0',
            'file_size': str(file_size),
            'Content-Type': 'video/mp4'
        }

        up_res = requests.post(upload_uri, headers=up_headers, data=video_bytes, timeout=120)
        if up_res.status_code not in (200, 201):
            err = up_res.json().get('error', {}).get('message', up_res.text) if up_res.text else 'Transfer error'
            raise Exception(f"Video binary transfer failed: {err}")

        print(f"[instagram] ✅ Video Bytes Transferred Successfully!")

        # Step 3: Wait for Meta Container Processing and Publish
        print("[instagram] Step 3: Waiting for Meta to process container...")
        max_wait = 180
        waited = 0
        while waited < max_wait:
            time.sleep(45 if waited == 0 else 30)
            waited += 45 if waited == 0 else 30
            print(f"[instagram] Publishing media (waited {waited}s)...")
            pub_res = requests.post(
                f"{api_base}/{user_id}/media_publish",
                data={'creation_id': container_id, 'access_token': access_token},
                timeout=60
            )
            if pub_res.status_code in (200, 201):
                break
            err_msg = ""
            try:
                err_msg = pub_res.json().get('error', {}).get('message', '')
            except Exception:
                pass
            if waited >= max_wait:
                raise Exception(f"Publish failed after {max_wait}s: {err_msg or pub_res.text}")
            print(f"[instagram] Not ready yet, retrying in 30s...")

        if pub_res.status_code in (200, 201):
            media_id = pub_res.json().get('id', container_id)
            print(f"[instagram] 🎉 SUCCESS! Media ID: {media_id} (waited {waited}s)")
            print(f"INSTAGRAM: SUCCESS (ID: {media_id})")
            return {'status': 'success', 'id': media_id, 'platform': 'instagram', 'wait_s': waited}
        else:
            err = pub_res.json().get('error', {}).get('message', pub_res.text)
            raise Exception(f"Publish failed: {err}")

    except Exception as e:
        print(f"[instagram] ❌ Error: {e}")
        return {'status': 'failed', 'error': str(e), 'platform': 'instagram'}
