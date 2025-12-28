import os
import subprocess
from instascrape import Reel, Post
import requests

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_with_parth_dl(url):
    """
    Attempt download using parth-dl (CLI)
    """
    try:
        result = subprocess.run(
            ["parth-dl", url, "-o", DOWNLOAD_DIR],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            files = os.listdir(DOWNLOAD_DIR)
            if files:
                return [os.path.join(DOWNLOAD_DIR, f) for f in files]

        raise Exception("parth-dl failed")

    except Exception as e:
        print("parth-dl error:", e)
        return None


def download_with_instascrape(url):
    """
    Fallback method using instascrape
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0"
    })

    files = []

    try:
        if "/reel/" in url:
            reel = Reel(url)
            reel.scrape(session=session)
            reel.download(fp=DOWNLOAD_DIR)
            files.append(os.path.join(DOWNLOAD_DIR, reel.filename))

        else:
            post = Post(url)
            post.scrape(session=session)

            if post.is_video:
                post.download(fp=DOWNLOAD_DIR)
                files.append(os.path.join(DOWNLOAD_DIR, post.video_filename))
            else:
                for media in post.get_medias():
                    media.download(fp=DOWNLOAD_DIR)
                    files.append(os.path.join(DOWNLOAD_DIR, media.filename))

        return files

    except Exception as e:
        print("instascrape error:", e)
        return None


def download_instagram(url):
    """
    Main handler (parth-dl -> instascrape fallback)
    """
    # clean folder
    for f in os.listdir(DOWNLOAD_DIR):
        os.remove(os.path.join(DOWNLOAD_DIR, f))

    files = download_with_parth_dl(url)

    if files:
        print("Downloaded using parth-dl")
        return files

    print("Switching to instascrape...")
    files = download_with_instascrape(url)

    if files:
        print("Downloaded using instascrape")
        return files

    raise Exception("All download methods failed")
