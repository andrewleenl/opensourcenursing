#!/usr/bin/env python3
"""Fix the Medical-Surgical Nursing chapter pages on OpenSourceNursing.ca.

Run it from your site folder (the one with index.html and the Ch01_... files).
It changes only the Ch*.html chapter files:

  1. Renames the book from "Pathophysiology for Nurses" to
     "Medical-Surgical Nursing: A Canadian Open Text".
  2. Points each chapter's "All Chapters" button to the chapter list
     (index.html#medsurg) instead of the old index.html#patho.
  3. Adds share previews (Open Graph and Twitter tags) and a canonical
     address, using each chapter's own title and description, with the
     site's share image (og-image.png).
  4. Gives chapters that have no main heading (h1) a hidden one with the
     chapter title, for screen readers and search engines. The page looks
     exactly the same.

Before changing anything it copies every chapter it will change into a
backup folder (chapter_backup_YYYYMMDD-HHMMSS). Running it a second time
does nothing to chapters that are already fixed.
"""
import datetime
import glob
import html
import json
import os
import re
import shutil
import sys

SITE = "https://opensourcenursing.ca"
OLD_FULL = "Pathophysiology for Nurses: A Canadian Open Text"
NEW_FULL = "Medical-Surgical Nursing: A Canadian Open Text"
OLD_SHORT = "Pathophysiology for Nurses"
NEW_SHORT = "Medical-Surgical Nursing"
MARK = "<!-- osn-share-preview -->"
H1_MARK = "<!-- osn-main-heading -->"
IMG_ALT = "OpenSourceNursing.ca: free Canadian nursing textbooks, lecture slides and clinical tools"
OLD_IMG_LINES = (
    f'<meta property="og:image" content="{SITE}/icon-512.png">\n'
    '<meta property="og:image:alt" content="OpenSourceNursing.ca logo">\n'
    '<meta name="twitter:card" content="summary">'
)
NEW_IMG_LINES = (
    f'<meta property="og:image" content="{SITE}/og-image.png">\n'
    '<meta property="og:image:width" content="1200">\n'
    '<meta property="og:image:height" content="630">\n'
    f'<meta property="og:image:alt" content="{IMG_ALT}">\n'
    '<meta name="twitter:card" content="summary_large_image">'
)
VH_CSS = ("position:absolute!important;width:1px!important;height:1px!important;padding:0!important;"
          "margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;"
          "white-space:nowrap!important;border:0!important")


def share_block(page_url, title, desc):
    t = html.escape(title, quote=True)
    d = html.escape(desc, quote=True)
    return (
        f"\n{MARK}\n"
        f'<link rel="canonical" href="{page_url}">\n'
        '<meta property="og:type" content="article">\n'
        '<meta property="og:site_name" content="OpenSourceNursing.ca">\n'
        '<meta property="og:locale" content="en_CA">\n'
        f'<meta property="og:url" content="{page_url}">\n'
        f'<meta property="og:title" content="{t}">\n'
        f'<meta property="og:description" content="{d}">\n'
        f'<meta property="og:image" content="{SITE}/og-image.png">\n'
        '<meta property="og:image:width" content="1200">\n'
        '<meta property="og:image:height" content="630">\n'
        f'<meta property="og:image:alt" content="{IMG_ALT}">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:title" content="{t}">\n'
        f'<meta name="twitter:description" content="{d}">\n'
        f'<meta name="twitter:image" content="{SITE}/og-image.png">'
    )


def fix(text, filename):
    notes = []
    n_full = text.count(OLD_FULL)
    text = text.replace(OLD_FULL, NEW_FULL)
    n_short = text.count(OLD_SHORT)
    text = text.replace(OLD_SHORT, NEW_SHORT)
    if n_full or n_short:
        notes.append(f"book name x{n_full + n_short}")

    n_link = text.count("index.html#patho")
    text = text.replace("index.html#patho", "index.html#medsurg")
    if n_link:
        notes.append(f"All Chapters link x{n_link}")

    if MARK not in text:
        tm = re.search(r"<title>(.*?)</title>", text, re.S)
        if tm:
            title = html.unescape(re.sub(r"\s+", " ", tm.group(1)).strip())
            dm = re.search(r'<meta\s+name="description"\s+content="([^"]*)"\s*/?>', text)
            desc = html.unescape(dm.group(1)) if dm else f"{title}. Free open textbook chapter, CC BY-NC-SA 4.0."
            # Cloudflare serves chapters without ".html", so use that address.
            page_url = f"{SITE}/{os.path.splitext(filename)[0]}"
            anchor = dm.end() if dm else tm.end()
            text = text[:anchor] + share_block(page_url, title, desc) + text[anchor:]
            notes.append("share preview")
    elif OLD_IMG_LINES in text:
        # Chapters fixed by the first version of this script: switch to the big share image.
        text = text.replace(OLD_IMG_LINES, NEW_IMG_LINES)
        text = text.replace(f'<meta name="twitter:image" content="{SITE}/icon-512.png">',
                            f'<meta name="twitter:image" content="{SITE}/og-image.png">')
        notes.append("share image")

    if H1_MARK not in text and not re.search(r"""<h1\b|['"]h1['"]""", text):
        heading = None
        dm = re.search(r'<script id="data" type="application/json">(.*?)</script>', text, re.S)
        if dm:
            try:
                meta = json.loads(dm.group(1)).get("meta", {})
                if meta.get("title"):
                    heading = f"Chapter {meta.get('chapter', '')}: {meta['title']}".replace("Chapter : ", "")
            except ValueError:
                pass
        if not heading:
            tm = re.search(r"<title>(.*?)</title>", text, re.S)
            heading = html.unescape(tm.group(1)).split(" · ")[0].split(" | ")[0].strip() if tm else None
        bm = re.search(r"<body\b[^>]*>", text)
        if heading and bm:
            tag = (f'\n{H1_MARK}\n<h1 style="{VH_CSS}">{html.escape(heading)}</h1>\n')
            text = text[:bm.end()] + tag + text[bm.end():]
            notes.append("main heading")
    return text, notes


def main():
    files = sorted(glob.glob("Ch[0-9][0-9]_*.html"))
    if not files:
        sys.exit("No Ch##_*.html files here. Run this from your site folder (where index.html is).")
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"chapter_backup_{stamp}"
    changed = 0
    for f in files:
        with open(f, encoding="utf-8") as fh:
            old = fh.read()
        new, notes = fix(old, f)
        if new == old:
            print(f"  {f}: already fixed")
            continue
        os.makedirs(backup, exist_ok=True)
        shutil.copy2(f, os.path.join(backup, f))
        with open(f, "w", encoding="utf-8", newline="") as fh:
            fh.write(new)
        changed += 1
        print(f"  {f}: " + ", ".join(notes))
    print(f"\nDone. {changed} of {len(files)} chapters changed.")
    if changed:
        print(f"Originals saved in {backup}/ (delete it once you're happy).")


if __name__ == "__main__":
    main()
