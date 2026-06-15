"""
Upload to VK - VELOCITY HEBREW
"""
import os, vk_api
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

def upload_to_vk(video_path, description="", title=""):
    access_token = os.getenv('VK_ACCESS_TOKEN')
    group_id = os.getenv('VK_GROUP_ID')
    if not access_token or access_token == "***": return {'status': 'skipped'}
    if not group_id or group_id == "***": return {'status': 'skipped'}
    try: group_id_int = int(str(group_id).lstrip('-'))
    except: return {'status': 'skipped'}
    try:
        vk_session = vk_api.VkApi(token=access_token)
        vk = vk_session.get_api(); upload = vk_api.VkUpload(vk_session)
        message = description or "Learn with VELOCITY HEBREW!"
        video = upload.video(video_file=str(video_path), name=title or 'VELOCITY HEBREW', description=description[:220] if description else '', group_id=group_id_int, wallpost=0)
        attachment = f"video{video['owner_id']}_{video['video_id']}"
        post = vk.wall.post(owner_id=-group_id_int, from_group=1, message=message, attachments=attachment)
        return {'success': True, 'video_id': video['video_id'], 'post_id': post['post_id'], 'post_url': f"https://vk.com/wall-{group_id_int}_{post['post_id']}"}
    except Exception as e: raise Exception(f"VK Error: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2: print("Usage: python upload_vk.py <video>"); sys.exit(1)
    result = upload_to_vk(sys.argv[1]); print(result)
