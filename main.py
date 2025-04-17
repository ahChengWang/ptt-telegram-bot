import os
import requests
from bs4 import BeautifulSoup
import subprocess

PTT_URL = "https://www.ptt.cc/bbs/Lifeismoney/index.html"
# HEADERS = {'cookie': 'over18=1'}
TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
STATE_FILE = "last_sent.txt"


def send_telegram_message(message):
    print("TG_TOKEN=", str(TG_TOKEN))
    print("TG_CHAT_ID=", str(TG_CHAT_ID))
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {
        "chat_id": TG_CHAT_ID,
        "text": message
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("✅ 已推送 Telegram")
    else:
        print("❌ 傳送失敗：", response.text)


def load_last_url():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


def save_last_url(url):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(url)


def commit_last_url():
    subprocess.run(["git", "config", "--global", "user.name", "ptt-bot"])
    subprocess.run(["git", "config", "--global",
                   "user.email", "ptt-bot@example.com"])
    subprocess.run(["git", "add", STATE_FILE])
    subprocess.run(["git", "commit", "-m", "update last_sent url"])
    subprocess.run(["git", "push"])


def check_new_posts():
    last_url = load_last_url()
    res = requests.get(PTT_URL)
    print(res.text)
    soup = BeautifulSoup(res.text, "html.parser")
    entries = soup.select("div.r-ent div.title a")
    new_info_articles = []
    found_last = False

    # 從最舊到最新掃描，保證順序一致
    for tag in reversed(entries):
        title = tag.text.strip()
        relative_url = tag["href"]
        full_url = "https://www.ptt.cc" + relative_url

        # 已發送過的文章，停止往後看
        if full_url == last_url:
            found_last = True
            break

        if title.startswith("[情報]"):
            new_info_articles.append((title, full_url))

    if not new_info_articles:
        print("🔁 無新 [情報] 文章")
        return

    # 發送推播（最舊的在前）
    for title, url in reversed(new_info_articles):
        message = f"📢 [情報更新]\n{title}\n{url}"
        send_telegram_message(message)

    # 記錄這次推播的最新那篇（第一篇最靠近最新的）
    latest_sent_url = new_info_articles[0][1]
    save_last_url(latest_sent_url)
    commit_last_url()


if __name__ == "__main__":
    check_new_posts()
