"""AI phrase generation with permanent no-repeat history."""

from __future__ import annotations

import json
import random
import time
from datetime import datetime

import requests

import config
from config import CATEGORIES, CATEGORIES_NATIVE, HISTORY_DIR, MAX_RECENT_CATEGORIES

PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"
RECENT_CATEGORIES_FILE = HISTORY_DIR / "recent_categories.json"

PHRASE_KEY = config.LANGUAGE["history_key"]
LANGUAGE_NAME = config.LANGUAGE["name"]
NATIVE_NAME = config.LANGUAGE["native_name"]

# ==== FALLBACK PHRASES START ====
FALLBACK_PHRASES = [
    {"english": "Hello, nice to meet you.", "native": "שלום, נעים להכיר.", "transliteration": "Shalom, na'im lehakir."},
    {"english": "Thank you very much.", "native": "תודה רבה.", "transliteration": "Toda raba."},
    {"english": "Good morning, have a great day.", "native": "בוקר טוב, שיהיה לך יום נהדר.", "transliteration": "Boker tov, sheyihyeh lecha yom nehedar."},
    {"english": "I love learning new languages.", "native": "אני אוהב ללמוד שפות חדשות.", "transliteration": "Ani ohev lilmod safot chadashot."},
    {"english": "Never give up on your dreams.", "native": "לעולם אל תוותר על החלומות שלך.", "transliteration": "Le'olam al tefater al hachalomot shelcha."},
    {"english": "Every day is a fresh start.", "native": "כל יום הוא התחלה חדשה.", "transliteration": "Kol yom hu hatchala chadasha."},
    {"english": "Believe in yourself always.", "native": "תאמין בעצמך תמיד.", "transliteration": "Ta'amin be'atzmecha tamid."},
    {"english": "Small steps lead to big changes.", "native": "צעדים קטנים מובילים לשינויים גדולים.", "transliteration": "Tze'adim ktanim movilim le'shinuyim gdolim."},
    {"english": "You are stronger than you think.", "native": "אתה חזק יותר ממה שאתה חושב.", "transliteration": "Ata chazak yoter mima ata choshev."},
    {"english": "Happiness is a choice, choose it.", "native": "אושר הוא בחירה, בחר בו.", "transliteration": "Osher hu bechira, bachar bo."},
    {"english": "What time is it please.", "native": "מה השעה בבקשה.", "transliteration": "Ma hasha'a bevakasha."},
    {"english": "Where is the train station.", "native": "איפה תחנת הרכבת.", "transliteration": "Eifo tachanat ha'rakevet."},
    {"english": "How much does this cost.", "native": "כמה זה עולה.", "transliteration": "Kama ze ole."},
    {"english": "Can you help me please.", "native": "אתה יכול לעזור לי בבקשה.", "transliteration": "Ata yachol la'azor li bevakasha."},
    {"english": "I would like a coffee please.", "native": "אני אשמח לקפה בבקשה.", "transliteration": "Ani esmach lekafe bevakasha."},
    {"english": "The food is delicious today.", "native": "האוכל טעים היום.", "transliteration": "Ha'ochel ta'im hayom."},
    {"english": "Have a wonderful weekend.", "native": "שיהיה לך סוף שבוע נפלא.", "transliteration": "Sheyihyeh lecha sof shavua nifla."},
    {"english": "Take care of yourself.", "native": "שמור על עצמך.", "transliteration": "Shmor al atzmecha."},
    {"english": "See you tomorrow my friend.", "native": "נתראה מחר חבר שלי.", "transliteration": "Nitra'e machar chaver sheli."},
    {"english": "The weather is beautiful outside.", "native": "מזג האוויר יפה בחוץ.", "transliteration": "Mezeg ha'avir yafe bachutz."},
    {"english": "I am very happy today.", "native": "אני מאוד שמח היום.", "transliteration": "Ani me'od samach hayom."},
    {"english": "Learning a language opens new doors.", "native": "לימוד שפה פותח דלתות חדשות.", "transliteration": "Limud safa pote'ach dlatot chadashot."},
    {"english": "Keep practicing every single day.", "native": "המשך להתאמן כל יום.", "transliteration": "Hemshech lehit'amen kol yom."},
    {"english": "You can achieve anything you want.", "native": "אתה יכול להשיג כל מה שאתה רוצה.", "transliteration": "Ata yachol lehasig kol ma ata rotze."},
    {"english": "Rest when you are tired.", "native": "נוח כשאתה עייף.", "transliteration": "No'ach kshe'ata ayef."},
    {"english": "Focus on the positive things.", "native": "התמקד בדברים החיוביים.", "transliteration": "Hitmaked badvarim hachiyuviyim."},
    {"english": "Learn from your mistakes.", "native": "למד מהטעויות שלך.", "transliteration": "Lemad me'hate'uyot shelcha."},
    {"english": "Trust the process completely.", "native": "סמוך על התהליך לחלוטין.", "transliteration": "Smoch al hateליך lachluchin."},
    {"english": "Breathe deeply and stay calm.", "native": "נשום עמוק והישאר רגוע.", "transliteration": "Nashom amok vehis'are rago'a."},
    {"english": "Enjoy the little moments in life.", "native": "תיהנה מהרגעים הקטנים בחיים.", "transliteration": "Tihana me'ha'rega'im haktanim bachayim."},
    {"english": "Smile more, worry less.", "native": "חייך יותר, דאג פחות.", "transliteration": "Chayech yoter, de'ag pachot."},
    {"english": "Be kind to everyone you meet.", "native": "היה אדיב לכל מי שאתה פוגש.", "transliteration": "Hihye adiv lechol mi ata pogesh."},
    {"english": "Help others without expecting anything back.", "native": "עזור לאחרים מבלי לצפות לתמורה.", "transliteration": "Azor le'acherim mibli letzapot letmura."},
    {"english": "Forgive yourself and move forward.", "native": "סלח לעצמך והמשך הלאה.", "transliteration": "Slech le'atzmecha vehemshech hala."},
    {"english": "Stay strong in difficult times.", "native": "הישאר חזק בזמנים קשים.", "transliteration": "His'are chazak bizmanim kashim."},
    {"english": "Every moment is a new beginning.", "native": "כל רגע הוא התחלה חדשה.", "transliteration": "Kol rega hu hatchala chadasha."},
    {"english": "Listen to your heart always.", "native": "הקשב ללב שלך תמיד.", "transliteration": "Hakshav lelev shelcha tamid."},
    {"english": "Do what makes you happy.", "native": "עשה מה שעושה אותך מאושר.", "transliteration": "Ase ma she'ose otcha me'usher."},
    {"english": "Your potential is unlimited.", "native": "הפוטנציאל שלך בלתי מוגבל.", "transliteration": "Hapotentzial shelcha bilti mugbal."},
    {"english": "Be brave and take risks.", "native": "היה אמיץ וקח סיכונים.", "transliteration": "Hihye amitz vekach sikunim."},
    {"english": "Celebrate your progress every day.", "native": "חגוג את ההתקדמות שלך כל יום.", "transliteration": "Chagog et hahitkadmut shelcha kol yom."},
    {"english": "Surround yourself with good people.", "native": "הקף את עצמך באנשים טובים.", "transliteration": "Hakif et atzmecha be'anashim tovim."},
    {"english": "Read books and grow your mind.", "native": "קרא ספרים ופתח את המוח שלך.", "transliteration": "Kra sfarim u'ftech et hamoach shelcha."},
    {"english": "Travel and discover new places.", "native": "טייל וגלה מקומות חדשים.", "transliteration": "Tayeil vegalem mekomot chadashim."},
    {"english": "Appreciate what you already have.", "native": "הערך את מה שכבר יש לך.", "transliteration": "Ha'arech et ma she'kvar yesh lecha."},
    {"english": "Dance like nobody is watching.", "native": "רקוד כאילו אף אחד לא מסתכל.", "transliteration": "Rkod ke'ilu af echad lo mistakel."},
    {"english": "Sing from your heart out loud.", "native": "שיר מהלב בקול רם.", "transliteration": "Shir mehalev bekol ram."},
    {"english": "Plant seeds of kindness everywhere.", "native": "שתול זרעי חסד בכל מקום.", "transliteration": "Shtol zr'ei chesed bechol makom."},
    {"english": "Let go of what you cannot control.", "native": "שחרר את מה שאינך יכול לשלוט בו.", "transliteration": "Shachrer et ma she'einch'a yachol lishlot bo."},
    {"english": "Be present in the here and now.", "native": "היה נוכח בהווה.", "transliteration": "Hihye noch'ach bahove."},
]
# ==== FALLBACK PHRASES END ====


def _load_json(path, default):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return default


def _save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_phrase_history():
    data = _load_json(PHRASE_HISTORY_FILE, {"phrases": [], "last_updated": None})
    data.setdefault("phrases", [])
    return data


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    _save_json(PHRASE_HISTORY_FILE, data)


def is_phrase_used(english):
    english_lower = english.lower().strip()
    for p in load_phrase_history()["phrases"]:
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def _history_native(p):
    for key in (PHRASE_KEY, "vietnamese", "native", "translation", "target"):
        value = p.get(key)
        if value:
            return str(value)
    return ""


def add_phrases_to_history(phrases, category):
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            PHRASE_KEY: phrase["native"],
            "transliteration": phrase.get("transliteration", ""),
            "category": category,
            "generated_at": datetime.now().isoformat(),
        })
    save_phrase_history(history)
    print(f"[content] Saved {len(phrases)} phrases (history total: {len(history['phrases'])})")


def get_available_category():
    data = _load_json(RECENT_CATEGORIES_FILE, {"recent_categories": [], "last_updated": None})
    recent = data.get("recent_categories", [])
    available = [c for c in CATEGORIES if c not in recent]
    if not available:
        recent = recent[-5:]
        available = [c for c in CATEGORIES if c not in recent]
        print("[rotation] Reset recent categories")
    selected = random.choice(available)
    recent.append(selected)
    data["recent_categories"] = recent[-MAX_RECENT_CATEGORIES:]
    data["last_updated"] = datetime.now().isoformat()
    _save_json(RECENT_CATEGORIES_FILE, data)
    print(f"[rotation] Category: {selected} ({len(available)} available)")
    return selected


def _normalize_phrase(item):
    if not isinstance(item, dict):
        return None
    english = str(item.get("english", "")).strip()
    native = str(
        item.get(PHRASE_KEY)
        or item.get("native")
        or item.get("vietnamese")
        or item.get("translation")
        or ""
    ).strip()
    translit = str(item.get("transliteration") or item.get("romanization") or item.get("romaji") or "").strip()
    if not english or not native:
        return None
    if len(english.split()) > 16:
        return None
    if "/" in native or "|" in native:
        native = native.split("/")[0].split("|")[0].strip()
    return {
        "english": english.replace("  ", " ").strip(),
        "native": native.strip(),
        "transliteration": translit.strip().strip("[]"),
    }


def _history_keys(history):
    used_en = set()
    used_nat = set()
    for p in history.get("phrases", []):
        en = str(p.get("english", "")).lower().strip()
        nat = _history_native(p).lower().strip()
        if en:
            used_en.add(en)
        if nat:
            used_nat.add(nat)
    return used_en, used_nat


def generate_phrases(category_english: str, num_phrases: int = 5) -> list:
    category_native = CATEGORIES_NATIVE[category_english]
    history = load_phrase_history()
    used_en, used_nat = _history_keys(history)
    recent_english = [
        p["english"] for p in history["phrases"] if p.get("category") == category_english
    ][-30:]

    models = [config.AI_MODEL]
    if "gemini-fast" not in models:
        models.append("gemini-fast")

    if config.POLLINATIONS_API_KEY:
        for attempt in range(5):
            model = models[0] if attempt < 3 else models[-1]
            try:
                phrases = _request_phrases(category_english, category_native, recent_english, num_phrases, attempt, model)
                unique = []
                for item in phrases:
                    p = _normalize_phrase(item)
                    if not p:
                        continue
                    key_en = p["english"].lower().strip()
                    key_nat = p["native"].lower().strip()
                    if key_en in used_en or key_nat in used_nat:
                        continue
                    if any(key_en == u["english"].lower().strip() for u in unique):
                        continue
                    used_en.add(key_en)
                    used_nat.add(key_nat)
                    unique.append(p)
                    if len(unique) >= num_phrases:
                        break
                if len(unique) >= num_phrases:
                    add_phrases_to_history(unique[:num_phrases], category_english)
                    return unique[:num_phrases]
                print(f"[content] Attempt {attempt + 1}: only {len(unique)} fresh phrases (need {num_phrases})")
            except Exception as exc:  # noqa: BLE001 - network boundary
                print(f"[content] Attempt {attempt + 1} failed ({model}): {exc}")
            time.sleep(1.5 * (attempt + 1))
    else:
        print("[content] No POLLINATIONS_API_KEY, using fallback phrases")

    fresh_fallback = []
    for p in FALLBACK_PHRASES:
        if p["english"].lower().strip() in used_en or p["native"].lower().strip() in used_nat:
            continue
        fresh_fallback.append(p)
    if not fresh_fallback:
        raise RuntimeError("Phrase API unavailable and no unused fallback phrases left; refusing to reuse phrases")
    chosen = fresh_fallback[:num_phrases]
    if len(chosen) < num_phrases:
        print(f"[content] Only {len(chosen)} fresh fallback phrases; building a shorter lesson")
    add_phrases_to_history(chosen, category_english)
    return chosen


def _request_phrases(category_english, category_native, recent_english, num_phrases, attempt, model=None):
    avoid = ""
    if recent_english:
        avoid = "\nDo NOT reuse any of these phrases:\n" + "\n".join(f"- {p}" for p in recent_english)

    prompt = f"""Create {num_phrases * 6} unique {category_english} phrases for English speakers learning {LANGUAGE_NAME}.
{avoid}

Rules:
1. Keep every phrase short and natural (4-11 words in English).
2. Use natural commas for TTS breathing pauses.
3. Each phrase must be speakable in 2-4 seconds.
4. Write clean {LANGUAGE_NAME} in {NATIVE_NAME} with correct accents and orthography. One translation only, no slashes.
5. Transliteration is a friendly Roman-script pronunciation guide for English speakers (not IPA).
6. Vary the sentence patterns and emotions. No duplicates.
7. Phrases must feel like real everyday language, not textbook filler.

Return ONLY a JSON array:
[{{"english": "...", "native": "...", "transliteration": "..."}}]"""

    response = requests.post(
        "https://gen.pollinations.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {config.POLLINATIONS_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model or config.AI_MODEL,
            "messages": [
                {"role": "system", "content": f"You are a {LANGUAGE_NAME} teacher creating short, natural, varied bilingual phrases. Reply with JSON only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": min(0.95 + attempt * 0.02, 1.0),
        },
        timeout=90,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].strip()

    if "```json" in content:
        content = content.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0].strip()

    start = content.find("[")
    end = content.rfind("]")
    if start >= 0 and end > start:
        content = content[start:end + 1]

    data = json.loads(content)
    if not isinstance(data, list):
        raise ValueError("AI did not return a JSON array")
    return data
