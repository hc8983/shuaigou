"""抓帥勾老師 YouTube 頻道的最新影片，存成 videos.json。

資料來源是 YouTube 官方的 RSS，不用 API 金鑰、不會有額度問題，
但只會回傳最新 15 支。要列出「全部影片」才需要改用 YouTube Data API。

用法：python3 sync_videos.py
"""

import html
import json
import re
import subprocess
import sys

CHANNEL_ID = "UCHQSmKCEB0z53qVwtFOlOwQ"
FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"

# 標題結尾的頻道標籤，顯示時拿掉
TAIL = re.compile(r"\s*[｜|]\s*#?帥勾老師\s*$")
# 「下課去」系列＝長片，其餘當短影片
VLOG_MARK = "下課去"


def fetch(url):
    """用 curl 抓，macOS 上的 Python 偶爾會有 SSL 憑證問題。"""
    out = subprocess.run(
        ["curl", "-sSL", "--max-time", "30", url],
        capture_output=True,
        check=True,
    )
    return out.stdout.decode("utf-8")


def clean_title(raw):
    title = html.unescape(raw).strip()
    title = TAIL.sub("", title)
    title = re.sub(r"^【[^】]*】\s*", "", title)   # 拿掉【帥勾老師下課去】這種前綴
    return title.strip()


def parse(xml):
    videos = []
    for entry in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        vid = re.search(r"<yt:videoId>(.*?)</yt:videoId>", entry)
        title = re.search(r"<title>(.*?)</title>", entry)
        pub = re.search(r"<published>(.*?)</published>", entry)
        if not (vid and title and pub):
            continue
        raw_title = html.unescape(title.group(1))
        date = pub.group(1)[:10]
        videos.append(
            {
                "id": vid.group(1),
                "title": clean_title(title.group(1)),
                "date": date,
                "is_vlog": VLOG_MARK in raw_title,
            }
        )
    return videos


def main():
    videos = parse(fetch(FEED))
    if not videos:
        print("抓不到任何影片，不覆寫 videos.json", file=sys.stderr)
        return 1

    vlogs = [v for v in videos if v["is_vlog"]]
    clips = [v for v in videos if not v["is_vlog"]]

    data = {
        "channel_id": CHANNEL_ID,
        "vlog": vlogs[0] if vlogs else None,
        "clips": clips[:14],
    }

    with open("videos.json", "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print(f"寫入 videos.json：短片 {len(data['clips'])} 支"
          f"，下課去 {'1' if data['vlog'] else '0'} 支")
    return 0


if __name__ == "__main__":
    sys.exit(main())
