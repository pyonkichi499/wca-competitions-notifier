"""Configuration and constants for the WCA Kanto Notifier."""

import os

from dotenv import load_dotenv

load_dotenv()

# WCA API Configuration
WCA_API_BASE_URL = "https://raw.githubusercontent.com/robiningelbrecht/wca-rest-api/master/api"
WCA_JAPAN_COMPETITIONS_URL = f"{WCA_API_BASE_URL}/competitions/JP.json"

# Twitter API Configuration
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

# Cloud Storage Configuration (for production)
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "")
GCS_STATE_FILE = "notified_competitions.json"

# Local Storage Configuration (for development)
LOCAL_STATE_FILE = os.getenv("LOCAL_STATE_FILE", "data/notified_competitions.json")

# Environment
ENV = os.getenv("ENV", "development")  # "development" or "production"

# Kanto region keywords for filtering
KANTO_KEYWORDS = [
    # Tokyo
    "Tokyo", "東京",
    # Kanagawa
    "Kanagawa", "神奈川", "Yokohama", "横浜", "Kawasaki", "川崎",
    # Chiba
    "Chiba", "千葉",
    # Saitama
    "Saitama", "埼玉", "Omiya", "大宮",
    # Ibaraki
    "Ibaraki", "茨城",
    # Tochigi
    "Tochigi", "栃木",
    # Gunma
    "Gunma", "群馬",
    # Regional names
    "Kanto", "関東",
    "Shonan", "湘南",
    "Minatomirai", "みなとみらい",
]

# WCA Event code to Japanese name mapping
EVENT_NAMES = {
    "333": "3x3x3",
    "222": "2x2x2",
    "444": "4x4x4",
    "555": "5x5x5",
    "666": "6x6x6",
    "777": "7x7x7",
    "333bf": "3x3x3目隠し",
    "333oh": "3x3x3片手",
    "333fm": "3x3x3最少手数",
    "333mbf": "3x3x3複数目隠し",
    "444bf": "4x4x4目隠し",
    "555bf": "5x5x5目隠し",
    "clock": "クロック",
    "minx": "メガミンクス",
    "pyram": "ピラミンクス",
    "skewb": "スキューブ",
    "sq1": "スクエア1",
}

# Tweet template
TWEET_TEMPLATE = """🧊 新しいWCA大会が発表されました！

📅 {name}
🗓 {date}
📍 {location}
🎯 {events}

詳細・申込み👇
{url}

#WCA #スピードキューブ #ルービックキューブ"""
