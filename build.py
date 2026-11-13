"""把 src/index.html（樣板）＋ videos.json（影片資料）組成可以上線的 index.html。

樣板是從 Artifact 設計稿來的，Artifact 平台會自動補 doctype／head，
放到 GitHub Pages 這種一般主機就要自己補，順便加上 SEO 與分享縮圖。

用法：python3 build.py src/index.html index.html
"""

import hashlib
import html
import json
import os
import re
import sys

BASE = "https://hc8983.github.io/shuaigou/"
DESC = (
    "帥勾老師 — 把國文課搬到手機上。孟子、荀子、朱自清，每天一支課堂短片；"
    "下課之後就是「下課去」的旅行紀錄。"
)

HEAD_EXTRA = """<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{desc}">
<meta name="theme-color" content="#3C6CA8">
<link rel="canonical" href="{base}">
<link rel="icon" href="img/avatar.jpg">
<link rel="apple-touch-icon" href="img/avatar.jpg">
<meta property="og:type" content="website">
<meta property="og:site_name" content="帥勾老師">
<meta property="og:title" content="帥勾老師">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{base}">
<meta property="og:image" content="{base}img/avatar.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="帥勾老師">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{base}img/avatar.jpg">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "帥勾老師",
  "description": "{desc}",
  "url": "{base}",
  "image": "{base}img/avatar.jpg",
  "jobTitle": "國文老師",
  "sameAs": [
    "https://www.youtube.com/@handsomehook2024",
    "https://www.instagram.com/deckard_bishop/",
    "https://www.threads.com/@deckard_bishop",
    "https://www.facebook.com/p/%E5%B8%A5%E5%8B%BE%E8%80%81%E5%B8%AB-61578846517354/"
  ]
}
</script>
<style>
:root { color-scheme: light; }
html, body { margin: 0; }
img { max-width: 100%; }
[hidden] { display: none !important; }
</style>
"""


def thumb(video_id):
    """YouTube 縮圖直連。maxres 偶爾不存在，壞掉就退回 hq。"""
    hq = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    return (
        f'src="https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg" '
        f"onerror=\"this.onerror=null;this.src='{hq}'\""
    )


def fmt_date(iso):
    return iso.replace("-", ".")


def render_vlog(v):
    if not v:
        return ""
    ep = re.search(r"EP\s*\d+", v["title"], re.I)
    label = ep.group(0).upper().replace(" ", "") if ep else "最新一集"
    title = html.escape(v["title"])
    return (
        f'<a class="vlog" href="https://www.youtube.com/watch?v={v["id"]}">\n'
        f'      <img {thumb(v["id"])} alt="{title}">\n'
        f'      <div class="vlog-body">\n'
        f'        <span class="series">下課去 · {label}</span>\n'
        f"        <h3>{title}</h3>\n"
        f'        <span class="meta">{fmt_date(v["date"])}</span>\n'
        f"      </div>\n"
        f"    </a>"
    )


def render_clips(clips):
    out = []
    for v in clips:
        title = html.escape(v["title"])
        out.append(
            f'      <a class="card" href="https://www.youtube.com/watch?v={v["id"]}">\n'
            f'        <div class="shot"><img {thumb(v["id"])} alt="">'
            f'<span class="play">▶</span></div>\n'
            f"        <h3>{title}</h3>\n"
            f'        <time datetime="{v["date"]}">{fmt_date(v["date"])}</time>\n'
            f"      </a>"
        )
    return "\n\n".join(out)


def inject_videos(page):
    try:
        with open("videos.json", encoding="utf-8") as fh:
            data = json.load(fh)
    except OSError:
        print("找不到 videos.json，先跑 sync_videos.py", file=sys.stderr)
        raise

    clips = data.get("clips", [])
    page = page.replace("<!--VLOG-->", render_vlog(data.get("vlog")))
    page = page.replace("<!--CLIPS-->", render_clips(clips))
    page = re.sub(
        r'(<span class="count">)最近 \d+ 支(</span>)',
        rf"\g<1>最近 {len(clips)} 支\g<2>",
        page,
    )
    return page


def stamp_assets(page, base_dir):
    """在 img/xxx.jpg 後面加上內容雜湊，換圖時瀏覽器才不會拿到舊快取。"""
    cache = {}

    def repl(match):
        path = match.group(1)
        if path not in cache:
            try:
                with open(os.path.join(base_dir, path), "rb") as fh:
                    cache[path] = hashlib.md5(fh.read()).hexdigest()[:8]
            except OSError:
                cache[path] = ""
        tag = cache[path]
        return path + ("?v=" + tag if tag else "")

    return re.sub(r"(img/[A-Za-z0-9_\-]+\.jpg)(?!\?)", repl, page)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as fh:
        content = fh.read()

    cut = content.index("</style>") + len("</style>")
    head, body = content[:cut], content[cut:]

    # 這個 meta 只有 Artifact 平台看得懂
    head = re.sub(r'<meta name="claude:viewport-fit-sides"[^>]*>\s*', "", head)

    out = (
        HEAD_EXTRA.replace("{desc}", DESC).replace("{base}", BASE)
        + head.strip()
        + "\n</head>\n<body>\n"
        + body.strip()
        + "\n</body>\n</html>\n"
    )

    out = inject_videos(out)
    out = stamp_assets(out, os.path.dirname(os.path.abspath(dst)))

    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(out)
    print("wrote", dst, len(out), "bytes")


if __name__ == "__main__":
    main()
