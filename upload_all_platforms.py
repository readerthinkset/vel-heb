"""
VELOCITY HEBREW - Unified Social Media Upload Script
"""

import os, sys, json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

upload_dir = Path(__file__).parent / "upload"
if upload_dir.exists() and str(upload_dir) not in sys.path:
    sys.path.insert(0, str(upload_dir))

uploaders = {}
modules = [
    ("upload_facebook", "upload_to_facebook", "fb"),
    ("upload_instagram", "upload_to_instagram", "ig"),
    ("upload_to_youtube", "upload_to_youtube", "yt"),
    ("upload_vk", "upload_to_vk", "vk"),
    ("upload_telegram", "upload_to_telegram", "tg"),
    ("upload_twitter", "upload_to_twitter", "tw"),
    ("upload_threads", "upload_to_threads", "th"),
    ("upload_tiktok", "upload_to_tiktok", "tk"),
]
for mod_name, func_name, key in modules:
    try:
        mod = __import__(mod_name, fromlist=[func_name])
        uploaders[key] = getattr(mod, func_name)
    except Exception as e:
        print(f"[!] {mod_name} not available: {e}")
        uploaders[key] = None


def get_latest_reel():
    video_dir = Path("output/video")
    if not video_dir.exists(): return None
    reels = list(video_dir.glob("*/final_reel.mp4"))
    if not reels: return None
    latest = max(reels, key=lambda p: p.stat().st_mtime)
    meta = {}
    mf = latest.parent / "metadata.json"
    if mf.exists():
        with open(mf, encoding="utf-8") as f: meta = json.load(f)
    return {"video_path": str(latest), "metadata": meta, "category": meta.get("category_english", "Hebrew Learning"), "phrases": meta.get("phrases", [])}


def generate_caption(phrases, category, platform="facebook"):
    base = [f"Learn Hebrew with VELOCITY HEBREW!", "", f"Category: {category}", "", f"Master Hebrew one phrase at a time! Today's {category} lesson:", ""]
    for i, p in enumerate(phrases[:5], 0):
        base.append(f"{i+1}. {p['english']}")
        base.append(f"   {p.get('hebrew', '')}")
        base.append(f"   [{p.get('transliteration', '')}]")
        base.append("")
    base.extend(["Tip: Repeat each phrase out loud 3 times!", "Like this video if you learned something new!", "Comment your favorite phrase below!", f"Follow for daily Hebrew lessons!", ""])
    base.extend([f"#learnhebrew", f"#hebrewlessons", f"#hebrewforbeginners", "#languagelearning", f"#hebrewvocabulary", f"#velocityhebrew", f"#dailyhebrew", f"#hebrew", "#learnlanguages"])
    return "\n".join(base)


def upload_to_all_platforms(video_path, caption, category, phrases=None):
    results = {"timestamp": datetime.now().isoformat(), "category": category, "video": video_path, "uploads": {}, "platforms_attempted": [], "platforms_successful": [], "platforms_skipped": [], "platforms_failed": []}
    print("\n" + "="*80)
    print(f"VELOCITY HEBREW - MULTI-PLATFORM UPLOAD")
    print("="*80)
    if not Path(video_path).exists(): print(f"Video not found"); 
    # === STANDARDIZED STATUS REPORT ===
    print("\n" + "=" * 60)
    print("UPLOAD STATUS REPORT")
    print("=" * 60)
    success_list = [p.lower() for p in results.get("platforms_successful", [])]
    failed_list = [p.lower() for p in results.get("platforms_failed", [])]
    skipped_list = [p.lower() for p in results.get("platforms_skipped", [])]
    for pname in ["INSTAGRAM", "FACEBOOK", "YOUTUBE", "THREADS", "TIKTOK"]:
        pl = pname.lower()
        if pl in success_list: status = "SUCCESS"
        elif pl in failed_list: status = "FAILED"
        elif pl in skipped_list: status = "SKIPPED"
        else: status = "-"
        print(f"{pname}: {status}")
    print("=" * 60)
    return results
    platforms = [("facebook", "fb", "Facebook"), ("instagram", "ig", "Instagram"), ("youtube", "yt", "YouTube"), ("vk", "vk", "VK"), ("telegram", "tg", "Telegram"), ("twitter", "tw", "Twitter"), ("threads", "th", "Threads"), ("tiktok", "tk", "TikTok")]
    for pname, key, dname in platforms:
        results["platforms_attempted"].append(pname)
        func = uploaders.get(key)
        if func:
            try:
                if pname == "youtube":
                    from upload_to_youtube import generate_video_metadata
                    yt_title, yt_desc, yt_tags = generate_video_metadata(category, len(phrases) if phrases else 5, phrases)
                    r = func(video_path=video_path, title=yt_title, description=yt_desc, tags=yt_tags, category_id='22')
                elif pname == "vk":
                    r = func(video_path=video_path, description=caption, title=f"Hebrew: {category}")
                elif pname == "facebook":
                    r = func(video_path=video_path, description=caption, title=f"Hebrew: {category}")
                elif pname == "instagram":
                    r = func(video_path=video_path, caption=caption, is_story=False)
                elif pname == "telegram":
                    r = func(video_path=video_path, caption=caption)
                elif pname == "twitter":
                    r = func(video_path=video_path, caption=caption)
                elif pname == "threads":
                    r = func(video_path=video_path, text=caption)
                elif pname == "tiktok":
                    r = func(video_path=video_path, description=caption)
                if r:
                    results["uploads"][pname] = r
                    results["platforms_successful"].append(pname)
                else: results["platforms_failed"].append(pname)
            except Exception as e:
                results["uploads"][pname] = {"status": "failed", "error": str(e)}
                results["platforms_failed"].append(pname)
        else:
            results["uploads"][pname] = {"status": "skipped"}
            results["platforms_skipped"].append(pname)
    s = len(results["platforms_successful"]); f = len(results["platforms_failed"]); sk = len(results["platforms_skipped"])
    print(f"\nSUMMARY: {s} success, {f} failed, {sk} skipped")
    rf = Path("output") / f"upload_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    rf.parent.mkdir(exist_ok=True)
    with open(rf, "w", encoding="utf-8") as f: json.dump(results, f, indent=2, ensure_ascii=False)
    
    # === STANDARDIZED STATUS REPORT ===
    print("\n" + "=" * 60)
    print("UPLOAD STATUS REPORT")
    print("=" * 60)
    success_list = [p.lower() for p in results.get("platforms_successful", [])]
    failed_list = [p.lower() for p in results.get("platforms_failed", [])]
    skipped_list = [p.lower() for p in results.get("platforms_skipped", [])]
    for pname in ["INSTAGRAM", "FACEBOOK", "YOUTUBE", "THREADS", "TIKTOK"]:
        pl = pname.lower()
        if pl in success_list: status = "SUCCESS"
        elif pl in failed_list: status = "FAILED"
        elif pl in skipped_list: status = "SKIPPED"
        else: status = "-"
        print(f"{pname}: {status}")
    print("=" * 60)
    return results


def main():
    print("\n" + "="*80)
    print(f"VELOCITY HEBREW - AUTOMATED UPLOAD")
    print("="*80)
    reel = get_latest_reel()
    if not reel: print("No reel found"); sys.exit(1)
    caption = generate_caption(reel['phrases'], reel['category'])
    upload_to_all_platforms(reel['video_path'], caption, reel['category'], reel['phrases'])

if __name__ == "__main__": main()
