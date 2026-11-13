"""把 Artifact 版的 index.html 轉成可以獨立上線的靜態網頁。

Artifact 平台會自動幫頁面補上 <!doctype>、<head> 和基本 reset，
放到 GitHub Pages 這種一般主機就要自己補，順便加上 SEO 與分享縮圖。

用法：python3 build.py <來源 index.html> <輸出 index.html>
"""

import hashlib
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
<style>
:root { color-scheme: light; }
html, body { margin: 0; }
img { max-width: 100%; }
[hidden] { display: none !important; }
</style>
"""


def stamp_assets(html, base_dir):
    """在每個 img/xxx.jpg 後面加上內容雜湊，例如 img/avatar.jpg?v=35290f7c。

    檔案內容一變，網址就變，瀏覽器就會重新抓，不會拿到舊的快取。
    """
    cache = {}

    def repl(match):
        path = match.group(1)
        if path not in cache:
            full = os.path.join(base_dir, path)
            try:
                with open(full, "rb") as fh:
                    cache[path] = hashlib.md5(fh.read()).hexdigest()[:8]
            except OSError:
                cache[path] = ""
        tag = cache[path]
        return path + ("?v=" + tag if tag else "")

    return re.sub(r'(img/[A-Za-z0-9_\-]+\.jpg)(?!\?)', repl, html)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as fh:
        content = fh.read()

    cut = content.index("</style>") + len("</style>")
    head, body = content[:cut], content[cut:]

    # 這個 meta 只有 Artifact 平台看得懂，一般主機用不到
    head = re.sub(r'<meta name="claude:viewport-fit-sides"[^>]*>\s*', "", head)

    out = (
        HEAD_EXTRA.replace("{desc}", DESC).replace("{base}", BASE)
        + head.strip()
        + "\n</head>\n<body>\n"
        + body.strip()
        + "\n</body>\n</html>\n"
    )

    out = stamp_assets(out, os.path.dirname(os.path.abspath(dst)))

    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(out)
    print("wrote", dst, len(out), "bytes")


if __name__ == "__main__":
    main()
