import os
import requests
from bs4 import BeautifulSoup
import subprocess

PTT_URL = "https://www.ptt.cc/bbs/Lifeismoney/index.html"
HEADERS = {'cookie': 'over18=1'}
TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
STATE_FILE = "last_sent.txt"


def send_telegram_message(message):
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
    res = requests.get(PTT_URL, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    print("soup=" + str(soup))
    articles = soup.select("div.title a")
    # print("articles=" + articles)

    if not articles:
        print("⚠️ 找不到文章")
        return

    new_articles = []
    found_last = False

    # 收集最新文章，逆序排列（最舊的先推）
    for tag in reversed(articles):
        title = tag.text.strip()
        relative_link = tag['href']
        full_url = "https://www.ptt.cc" + relative_link

        if full_url == last_url:
            found_last = True
            break
        else:
            new_articles.append((title, full_url))

    if not new_articles:
        print("🔁 沒有新文章")
        return

    # 推送新文章（先推最舊的）
    for title, url in reversed(new_articles):
        message = f"[PTT省錢版新文章]\n{title}\n{url}"
        send_telegram_message(message)

    # 儲存最新發送過的那一篇
    latest_url = new_articles[0][1]
    save_last_url(latest_url)
    commit_last_url()


if __name__ == "__main__":
    check_new_posts()
