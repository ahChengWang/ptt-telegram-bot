import os
import requests
import time
from bs4 import BeautifulSoup
import subprocess

PTT_URL = "https://www.pttweb.cc/bbs/Lifeismoney?m=0"
HEADERS = {
    "cookie": "over18=1",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Connection": "keep-alive",
    "Cookie": "_gid=GA1.2.951163347.1744857895; _ga_DZ6Y3BY9GW=GS1.1.1744887842.171.1.1744887842.0.0.0; _ga=GA1.2.1231348713.1606230154; cf_clearance=C5t15vY8Ic4rcFYVc8wT4qplXpLAeXHC17TyE6abueo-1744887843-1.2.1.1-.pbW1QYvzjnrD.STJsIis52f6PMq958qqmhXOpakyst.TpGMk2t2g95di9jR0wsQyaDCfifM6rqsKkhjc10JJdrk0PqbWb_f_8FuxFP2mEOFH55pFozw8PH4hHjYqpsRDYbhtLvbJzZTcz0S2QZ4dLpnHN_wZmPYE4HiirUOcE8FhFjkpGeC__bfBgQVGdYqzi2S5u_JaAFtfvMUK6qnRDwCdN15DA_0et_aZNY1.0IFsTeQ2cqniR6LW68DG96x64JZ91uUGLOI1hExtqLTvhgIRuH6A474_rkMdogYX3nlTAssypyjs3nWnP4fOqddIvdO904A1D34o0UI0uJ72jfYnvFk9Knv1q4MhvjqsEI"
}

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
STATE_FILE = "last_sent.txt"


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("✅ 已推送 Telegram")
    else:
        print("❌ 傳送失敗：", response.text)
    time.sleep(3)


def load_last_urls():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


def save_last_urls(url):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(url)


def commit_last_url():

    repo_url = f"https://{os.environ['GH_PAT']}@github.com/ahChengWang/ptt-telegram-bot.git"
    subprocess.run(["git", "config", "--global", "user.name",
                   os.environ.get("GIT_NAME", "ptt-bot")])
    subprocess.run(["git", "config", "--global", "user.email",
                   os.environ.get("GIT_EMAIL", "ptt@example.com")])
    
    # 先檢查是否有 remote origin，若有則移除
    subprocess.run(["git", "remote", "remove", "origin"], check=False)
    subprocess.run(["git", "remote", "add", "origin", repo_url], check=True)

    # 切回 main 分支（從 detached HEAD 切換）
    subprocess.run(["git", "checkout", "-B", "main"], check=True)

    # 加入變更、commit
    subprocess.run(["git", "add", "last_sent.txt"], check=True)
    result = subprocess.run(["git", "commit", "-m", "update last_sent url"],
                            check=False, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)

    if "nothing to commit" not in result.stdout:
        # ✅ 強制推送，解決 fetch first 錯誤
        subprocess.run(["git", "push", "--force-with-lease", "origin", "main"], check=True)
        print("✅ 已推送至 GitHub")
    else:
        print("ℹ️ 無需推送：內容未變化")


def check_new_posts():
    last_url = load_last_urls()
    res = requests.get(PTT_URL, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    latest_title = ""

    containers = soup.select("div.e7-container")
    new_info_articles = []

    for container in containers:
        type_tag = container.select_one("div.e7-type")
        title_tag = container.select_one("span.e7-title span")
        link_tag = container.select_one("a.e7-article-default")

        if not (type_tag and title_tag and link_tag):
            continue

        if "情報" not in type_tag.text.strip() or "全台捐血" in link_tag.text.strip():

            continue

        full_url = "https://www.pttweb.cc" + link_tag["href"]
        title = title_tag.text.strip()

        if full_url == last_url:
            latest_title = title
            break

        new_info_articles.append((title, full_url))

    if not new_info_articles:
        print("🔁 無新 [情報] 文章:近一篇 " + latest_title)
        return

    # 發送推播（最舊的在前）
    for title, url in reversed(new_info_articles):
        message = f"<b><b>🌟[情報更新]🌟</b></b>\n{title}\n{url}"

        send_telegram_message(message)

    # 記錄最新一篇文章
    latest_sent_url = new_info_articles[0][1]
    save_last_urls(latest_sent_url)
    commit_last_url()


if __name__ == "__main__":
    check_new_posts()
