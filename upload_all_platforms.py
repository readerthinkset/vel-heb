"""
Multi-Platform Video Uploader - VELOCITY HEBREW
Automated upload script supporting Facebook, Instagram, YouTube, and other platforms.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

try:
    from upload_facebook import upload_to_facebook
except ImportError:
    upload_to_facebook = None

try:
    from upload_instagram import upload_to_instagram
except ImportError:
    upload_to_instagram = None

try:
    from upload_to_youtube import upload_to_youtube
except ImportError:
    upload_to_youtube = None

try:
    from upload_vk import upload_to_vk
except ImportError:
    upload_to_vk = None

try:
    from upload_telegram import upload_to_telegram
except ImportError:
    upload_to_telegram = None

try:
    from upload_twitter import upload_to_twitter
except ImportError:
    upload_to_twitter = None

try:
    from upload_threads import upload_to_threads
except ImportError:
    upload_to_threads = None

try:
    from upload_tiktok import upload_to_tiktok
except ImportError:
    upload_to_tiktok = None


def get_latest_reel():
    base_dir = Path(__file__).parent.parent if (Path(__file__).parent / "output").exists() else Path(__file__).parent
    video_dir = base_dir / "output" / "video"

    if not video_dir.exists():
        return None

    reel_dirs = [d for d in video_dir.iterdir() if d.is_dir()]
    if not reel_dirs:
        return None

    reel_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    for reel_dir in reel_dirs:
        video_file = reel_dir / "final_reel.mp4"
        metadata_file = reel_dir / "metadata.json"

        if video_file.exists() and metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            return {
                "dir": reel_dir,
                "video_path": str(video_file),
                "metadata": metadata,
                "category": metadata.get("category_english", "General"),
                "phrases": metadata.get("phrases", [])
            }

    return None


def generate_caption(phrases, category, platform="general"):
    if platform == "instagram":
        caption_lines = [
            f"Learn Hebrew with VELOCITY HEBREW! 🇮🇱✨",
            f"Topic: {category}",
            f"",
            f"Today's phrases:"
        ]
        for i, phrase in enumerate(phrases, 1):
            caption_lines.append(f"{i}. {phrase['english']}")
            caption_lines.append(f"   -> {phrase.get('hebrew', '')} ({phrase.get('transliteration', '')})")
            caption_lines.append("")
        hashtags = [
            "#learnhebrew", "#hebrewlessons", "#hebrewforbeginners",
            "#languagelearning", "#hebrewvocabulary", "#velocityhebrew",
            "#dailyhebrew", "#hebrew", "#learnlanguages",
            "#hebrewteacher", "#speakhebrew", "#hebrewpractice",
            "#bilingual", "#hebrewwords", "#languagetips"
        ]
        caption_lines.extend(hashtags)
    else:
        caption_lines = [
            f"Learn Hebrew with VELOCITY HEBREW!",
            f"",
            f"Category: {category}",
            f"",
            f"Today's phrases:",
            f""
        ]
        for i, phrase in enumerate(phrases[:5], 1):
            caption_lines.append(f"{i}. {phrase['english']}")
            caption_lines.append(f"   -> {phrase.get('hebrew', '')} ({phrase.get('transliteration', '')})")
            caption_lines.append("")
        hashtags = [
            "#learnhebrew", "#hebrewlessons", "#hebrewforbeginners",
            "#languagelearning", "#hebrewvocabulary", "#velocityhebrew",
            "#dailyhebrew", "#hebrew", "#learnlanguages", "#hebrewteacher"
        ]
        caption_lines.extend(hashtags)
    return "\n".join(caption_lines)


def upload_to_all_platforms(video_path, caption, category, phrases=None):
    results = {
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "video": video_path,
        "uploads": {},
        "platforms_attempted": [],
        "platforms_successful": [],
        "platforms_skipped": [],
        "platforms_failed": []
    }

    print("\n" + "=" * 80)
    print("VELOCITY HEBREW - MULTI-PLATFORM UPLOAD")
    print("=" * 80)
    print(f"Video: {video_path}")
    print(f"Category: {category}")
    print(f"Caption length: {len(caption)} characters")
    print("=" * 80)

    if not Path(video_path).exists():
        print(f"[ERROR] Video file not found: {video_path}")
        return results

    platforms = [
        ("facebook", upload_to_facebook, "Facebook"),
        ("instagram", upload_to_instagram, "Instagram"),
        ("youtube", upload_to_youtube, "YouTube"),
        ("vk", upload_to_vk, "VK"),
        ("telegram", upload_to_telegram, "Telegram"),
        ("twitter", upload_to_twitter, "Twitter"),
        ("threads", upload_to_threads, "Threads"),
        ("tiktok", upload_to_tiktok, "TikTok"),
    ]

    for platform_name, upload_func, display_name in platforms:
        print(f"\n{display_name} UPLOAD...")
        results["platforms_attempted"].append(platform_name)

        if upload_func:
            try:
                upload_result = None
                if platform_name == "facebook":
                    upload_result = upload_func(video_path=video_path, description=caption, title=f"Hebrew: {category}")
                elif platform_name == "instagram":
                    upload_result = upload_func(video_path=video_path, caption=caption, is_story=False)
                elif platform_name == "youtube":
                    num_phrases = len(phrases) if phrases else 5
                    from upload_to_youtube import generate_video_metadata
                    yt_title, yt_description, yt_tags = generate_video_metadata(category, num_phrases, phrases)
                    upload_result = upload_func(video_path=video_path, title=yt_title, description=yt_description, tags=yt_tags, category_id='22')
                elif platform_name == "vk":
                    upload_result = upload_func(video_path=video_path, description=caption, title=f"Hebrew: {category}")
                elif platform_name == "telegram":
                    upload_result = upload_func(video_path=video_path, caption=caption)
                elif platform_name == "twitter":
                    upload_result = upload_func(video_path=video_path, caption=caption)
                elif platform_name == "threads":
                    upload_result = upload_func(video_path=video_path, text=caption)
                elif platform_name == "tiktok":
                    upload_result = upload_func(video_path=video_path, description=caption)

                if upload_result:
                    results["uploads"][platform_name] = upload_result
                    results["platforms_successful"].append(platform_name)
                else:
                    results["uploads"][platform_name] = {"status": "failed", "error": "Upload function returned None"}
                    results["platforms_failed"].append(platform_name)
            except Exception as e:
                error_msg = str(e)
                results["uploads"][platform_name] = {"status": "failed", "error": error_msg}
                results["platforms_failed"].append(platform_name)
                print(f"  Error: {error_msg}")
        else:
            results["uploads"][platform_name] = {"status": "skipped", "reason": "Module not available"}
            results["platforms_skipped"].append(platform_name)

    print("\n" + "=" * 60)
    print("UPLOAD STATUS REPORT")
    print("=" * 60)
    for pname, pkey in [("INSTAGRAM", "instagram"), ("FACEBOOK", "facebook"), ("YOUTUBE", "youtube"),
                          ("THREADS", "threads"), ("TIKTOK", "tiktok")]:
        pinfo = results["uploads"].get(pkey, {})
        if pinfo and pinfo.get("status") == "success":
            pid = pinfo.get("id", "N/A")
            print(f"{pname}: SUCCESS (ID: {pid})")
        elif pinfo and pinfo.get("status") == "skipped":
            print(f"{pname}: SKIPPED")
        elif pinfo:
            err = str(pinfo.get("error", ""))[:80]
            print(f"{pname}: FAILED - {err}")
        else:
            pl = pkey.lower()
            failed = pl in [p.lower() for p in results.get("platforms_failed", [])]
            skipped = pl in [p.lower() for p in results.get("platforms_skipped", [])]
            print(f"{pname}: {'FAILED' if failed else ('SKIPPED' if skipped else '-')}")
    print("=" * 60)

    results_file = Path("output") / f"upload_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results_file.parent.mkdir(exist_ok=True)
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results


def main():
    print("\n" + "=" * 80)
    print("VELOCITY HEBREW - AUTOMATED UPLOAD")
    print("=" * 80)

    reel = get_latest_reel()
    if not reel:
        print("\nNo reel found! Run facebook_reels_automation.py first.")
        sys.exit(1)

    print(f"\nFound latest reel:")
    print(f"   Category: {reel['category']}")
    print(f"   Video: {reel['video_path']}")
    print(f"   Phrases: {len(reel['phrases'])}")

    caption = generate_caption(reel['phrases'], reel['category'], platform="facebook")
    print(f"\nGenerated caption ({len(caption)} chars):")
    print("-" * 80)
    print(caption[:500] + "..." if len(caption) > 500 else caption)
    print("-" * 80)

    results = upload_to_all_platforms(reel['video_path'], caption, reel['category'], reel['phrases'])
    results["phrases"] = reel['phrases']

    successful = len(results.get("platforms_successful", []))
    failed = len(results.get("platforms_failed", []))
    skipped = len(results.get("platforms_skipped", []))

    if successful > 0:
        print(f"\nUpload complete! {successful} platform(s) successful.")
        if skipped > 0:
            print(f"{skipped} platform(s) skipped - add credentials to enable them")
        sys.exit(0)
    elif failed > 0:
        print(f"\nAll attempted uploads failed ({failed} failed, {skipped} skipped).")
        print("Check the error messages above and verify your credentials")
        sys.exit(1)
    else:
        print(f"\nAll uploads skipped ({skipped} skipped).")
        print("Add credentials in GitHub Secrets to enable uploads")
        sys.exit(1)


if __name__ == "__main__":
    main()
