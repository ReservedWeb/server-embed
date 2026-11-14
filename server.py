"""
Discord Embedder - server
=========================
Tiny stateless Flask app. It serves a page with OpenGraph / Twitter-player
meta tags pointing at a raw video URL. Discord reads those tags and renders
an inline video player.

Deploy free on Render / PythonAnywhere / Fly.io / Railway etc.
Start command:  gunicorn server:app
"""
import re
from html import escape
from urllib.parse import urlparse

from flask import Flask, Response, request

app = Flask(__name__)

MIME = {".webm": "video/webm", ".mov": "video/quicktime", ".m4v": "video/mp4"}


def clean_url(u):
    p = urlparse(u or "")
    return u if p.scheme in ("http", "https") and p.netloc else None


def guess_mime(url):
    path = urlparse(url).path.lower()
    for ext, mime in MIME.items():
        if path.endswith(ext):
            return mime
    return "video/mp4"


def dim(name, default):
    v = request.args.get(name, "")
    return v if v.isdigit() and 16 <= int(v) <= 7680 else str(default)


@app.route("/")
def index():
    return Response(
        "<!doctype html><title>Discord Embedder</title>"
        "<body style='font-family:sans-serif;background:#1e1f22;color:#ddd;"
        "text-align:center;padding:4rem'>"
        "<h1>Discord Embedder</h1><p>Server is running. Use the desktop app "
        "to generate embed links.</p></body>",
        mimetype="text/html",
    )


@app.route("/healthz")
def health():
    return "ok"


@app.route("/e")
def embed():
    video = clean_url(request.args.get("v"))
    if not video:
        return Response("Missing or invalid ?v= video URL", status=400)

    title = request.args.get("t", "").strip()[:200]
    desc = request.args.get("d", "").strip()[:500]
    color = request.args.get("c", "5865F2")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", color):
        color = "5865F2"
    thumb = clean_url(request.args.get("img"))
    w, h = dim("w", 1280), dim("h", 720)
    mime = guess_mime(video)

    e = lambda s: escape(s, quote=True)  # noqa: E731
    tags = [
        f'<meta charset="utf-8">',
        f"<title>{e(title or 'Video')}</title>",
        f'<meta name="theme-color" content="#{color}">',
        '<meta property="og:type" content="video.other">',
        f'<meta property="og:url" content="{e(request.url)}">',
        f'<meta property="og:video" content="{e(video)}">',
        f'<meta property="og:video:url" content="{e(video)}">',
        f'<meta property="og:video:secure_url" content="{e(video)}">',
        f'<meta property="og:video:type" content="{mime}">',
        f'<meta property="og:video:width" content="{w}">',
        f'<meta property="og:video:height" content="{h}">',
        '<meta name="twitter:card" content="player">',
        f'<meta name="twitter:player" content="{e(video)}">',
        f'<meta name="twitter:player:stream" content="{e(video)}">',
        f'<meta name="twitter:player:stream:content_type" content="{mime}">',
        f'<meta name="twitter:player:width" content="{w}">',
        f'<meta name="twitter:player:height" content="{h}">',
    ]
    if title:
        tags += [
            f'<meta property="og:title" content="{e(title)}">',
            f'<meta name="twitter:title" content="{e(title)}">',
        ]
    if desc:
        tags += [
            f'<meta property="og:description" content="{e(desc)}">',
            f'<meta name="twitter:description" content="{e(desc)}">',
        ]
    if thumb:
        tags += [
            f'<meta property="og:image" content="{e(thumb)}">',
            f'<meta name="twitter:image" content="{e(thumb)}">',
        ]

    body = (
        "<body style='margin:0;background:#111;display:flex;align-items:center;"
        "justify-content:center;min-height:100vh'>"
        f"<video src='{e(video)}' controls autoplay loop playsinline "
        "style='max-width:100%;max-height:100vh'></video></body>"
    )
    page = "<!doctype html><html><head>" + "".join(tags) + "</head>" + body + "</html>"
    return Response(page, mimetype="text/html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
