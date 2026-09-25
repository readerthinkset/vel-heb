"""
Direct Resumable Instagram Reel & Story Uploader via Meta Graph API v21.0
With Auto Payload Compression (<12MB) & Smart Container Processing Polling.
Enhanced with dynamic Facebook Page Instagram account discovery & multi-credential fallback.
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

    # 1. Gather all available credentials from environment
    ig_access_token = (os.getenv('INSTAGRAM_ACCESS_TOKEN') or os.getenv('IG_ACCESS_TOKEN') or '').strip()
    fb_access_token = (os.getenv('FACEBOOK_ACCESS_TOKEN') or os.getenv('FB_ACCESS_TOKEN') or '').strip()
    fb_page_id = (os.getenv('FACEBOOK_PAGE_ID') or os.getenv('FB_PAGE_ID') or '').strip()
    explicit_user_id = (os.getenv('INSTAGRAM_ACCOUNT_ID') or os.getenv('IG_USER_ID') or '').strip()

    def mask(t):
        return f"{t[:6]}...{t[-4:]}" if t and len(t) > 10 else ("SET" if t else "MISSING")

    print(f"[instagram] Credentials: IG Token={mask(ig_access_token)}, FB Token={mask(fb_access_token)}")
    print(f"[instagram] Target IDs: FB Page ID={fb_page_id or 'None'}, Configured IG ID={explicit_user_id or 'None'}")

    # 2. Query Facebook Page to discover the officially connected Instagram Business Account
    connected_ig_id = None
    if fb_page_id:
        for t_label, t_val in [("FB Page Token", fb_access_token), ("IG Token", ig_access_token)]:
            if not t_val:
                continue
            try:
                print(f"[instagram] Checking linked Instagram account on Page {fb_page_id} using {t_label}...")
                ig_r = requests.get(
                    f"https://graph.facebook.com/v21.0/{fb_page_id}?fields=instagram_business_account&access_token={t_val}",
                    timeout=15
                )
                if ig_r.status_code == 200:
                    acct = ig_r.json().get('instagram_business_account')
                    if acct and acct.get('id'):
                        connected_ig_id = str(acct['id']).strip()
                        print(f"[instagram] ✅ Discovered connected Instagram Business Account ID: {connected_ig_id}")
                        break
                    else:
                        print(f"[instagram] ℹ️ Page {fb_page_id} has no connected 'instagram_business_account'.")
                else:
                    err_resp = ig_r.json().get('error', {})
                    print(f"[instagram] ⚠️ Page check with {t_label} returned {ig_r.status_code}: {err_resp.get('message')}")
            except Exception as e:
                print(f"[instagram] ⚠️ Page check error: {e}")

    # 3. Build candidate (user_id, token, label) list
    candidates = []
    seen = set()

    def add_candidate(uid, tok, label):
        if uid and tok and (uid, tok) not in seen:
            seen.add((uid, tok))
            candidates.append((uid, tok, label))

    # A) Page-Linked Instagram account + FB Page Token (preferred for Page-connected accounts)
    if connected_ig_id and fb_access_token:
        add_candidate(connected_ig_id, fb_access_token, f"Page-Linked IG ({connected_ig_id}) + FB Page Token")

    # B) Configured Instagram Account ID + Instagram Token
    if explicit_user_id and ig_access_token:
        add_candidate(explicit_user_id, ig_access_token, f"Configured IG ({explicit_user_id}) + IG Token")

    # C) Page-Linked Instagram account + Instagram Token
    if connected_ig_id and ig_access_token:
        add_candidate(connected_ig_id, ig_access_token, f"Page-Linked IG ({connected_ig_id}) + IG Token")

    # D) Configured Instagram Account ID + FB Page Token
    if explicit_user_id and fb_access_token:
        add_candidate(explicit_user_id, fb_access_token, f"Configured IG ({explicit_user_id}) + FB Page Token")

    # E) Fallback to any remaining combination
    fallback_id = explicit_user_id or connected_ig_id
    fallback_token = ig_access_token or fb_access_token
    if fallback_id and fallback_token:
        add_candidate(fallback_id, fallback_token, f"Fallback ({fallback_id})")

    if not candidates:
        print("[instagram] ⚠️ Skipping - no Instagram Account ID or Access Token available")
        return {'status': 'skipped', 'reason': 'No credentials available', 'platform': 'instagram'}

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
        # Step 1: Create Resumable Container
        container_id = None
        upload_uri = None
        active_user_id = None
        active_token = None
        last_error = None

        print(f"[instagram] Step 1: Creating resumable {media_type} container (testing {len(candidates)} credential candidate(s))...")

        for u_id, tok, label in candidates:
            print(f"[instagram] Trying credential candidate: {label}...")
            c_data = {
                'media_type': 'STORIES' if is_story else 'REELS',
                'upload_type': 'resumable',
                'caption': caption[:2200] if caption else '',
                'access_token': tok
            }
            if not is_story:
                c_data['share_to_feed'] = 'false'

            c_res = requests.post(f"{api_base}/{u_id}/media", data=c_data, timeout=30)
            if c_res.status_code in (200, 201):
                res_json = c_res.json()
                container_id = res_json.get('id')
                upload_uri = res_json.get('uri')
                active_user_id = u_id
                active_token = tok
                print(f"[instagram] ✅ Container created successfully with {label}! Container ID: {container_id}")
                break
            else:
                err_data = {}
                try:
                    err_data = c_res.json().get('error', {})
                except Exception:
                    pass
                err_msg = err_data.get('message', c_res.text)
                err_code = err_data.get('code')
                err_subcode = err_data.get('error_subcode')
                err_type = err_data.get('type')
                last_error = f"{err_msg} (code: {err_code}, subcode: {err_subcode}, type: {err_type})"
                print(f"[instagram] ⚠️ Candidate {label} failed: {last_error}")

        if not container_id:
            raise Exception(f"Container creation failed across all candidates. Last error: {last_error}")

        print("[instagram] Step 2: Transferring video bytes to Meta Servers...")
        with open(upload_file_path, 'rb') as f:
            video_bytes = f.read()

        up_headers = {
            'Authorization': f'OAuth {active_token}',
            'offset': '0',
            'file_size': str(file_size),
            'Content-Type': 'video/mp4'
        }

        up_res = requests.post(upload_uri, headers=up_headers, data=video_bytes, timeout=120)
        if up_res.status_code not in (200, 201):
            err = up_res.json().get('error', {}).get('message', up_res.text) if up_res.text else 'Transfer error'
            raise Exception(f"Video binary transfer failed: {err}")

        print(f"[instagram] ✅ Video Bytes Transferred Successfully!")

        print("[instagram] Step 3: Waiting for Meta to process container...")
        max_wait = 180
        waited = 0
        while waited < max_wait:
            time.sleep(45 if waited == 0 else 30)
            waited += 45 if waited == 0 else 30
            print(f"[instagram] Publishing media (waited {waited}s)...")
            pub_res = requests.post(
                f"{api_base}/{active_user_id}/media_publish",
                data={'creation_id': container_id, 'access_token': active_token},
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
