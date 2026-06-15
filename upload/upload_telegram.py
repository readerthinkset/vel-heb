"""
Upload to Telegram - VELOCITY HEBREW
"""
import os, requests
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

def upload_to_telegram(video_path, caption):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    channel_id = os.getenv('TELEGRAM_CHANNEL_ID') or os.getenv('TELEGRAM_CHAT_ID')
    if not bot_token or bot_token == "***": return {'status': 'skipped'}
    if not channel_id or channel_id == "***": return {'status': 'skipped'}
    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    with open(video_path, 'rb') as vf:
        resp = requests.post(url, files={'video': vf}, data={'chat_id': channel_id, 'caption': caption, 'parse_mode': 'HTML'}, timeout=300)
        if resp.status_code == 200 and resp.json().get('ok'): return resp.json()
        raise Exception(f"Telegram error: {resp.text}")

if __name__ == "__main__":
    v = Path("final_video.mp4")
    if v.exists(): upload_to_telegram(str(v), "Test")
