"""
upload.py — Upload a video to YouTube via the Data API v3.

Usage:
  python infra/pipeline/upload.py videos/bfs_final.mp4
  python infra/pipeline/upload.py videos/lc994_final.mp4 --privacy public

First run will open a browser for OAuth. Token is cached in infra/pipeline/.token.json.

Requires:
  infra/pipeline/client_secrets.json  (download from GCP console)
"""

import argparse
import json
import os
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

HERE    = Path(__file__).resolve().parent
ROOT    = HERE.parents[1]
SECRETS = HERE / "client_secrets.json"
TOKEN   = HERE / ".token.json"
SCOPES  = ["https://www.googleapis.com/auth/youtube.upload"]

# Per-video metadata — key = stem of the final MP4 filename
METADATA = {
    "lc102_final": {
        "title":       "LC 102 · Binary Tree Level Order Traversal | BFS Visualized",
        "description": (
            "Visual walkthrough of LC 102 — Binary Tree Level Order Traversal.\n"
            "We process nodes level by level using a queue (BFS).\n\n"
            "Part of the BFS series: LC 102 → LC 200 → LC 994.\n\n"
            "github.com/algoviz1000/Viz"
        ),
        "tags": ["leetcode", "bfs", "binary tree", "level order", "algorithm", "visualization", "vizalgo"],
        "category": "27",  # Education
    },
    "lc200_final": {
        "title":       "LC 200 · Number of Islands | BFS Grid Visualized",
        "description": (
            "Visual walkthrough of LC 200 — Number of Islands.\n"
            "We use BFS to flood-fill each island and count them.\n\n"
            "Part of the BFS series: LC 102 → LC 200 → LC 994.\n\n"
            "github.com/algoviz1000/Viz"
        ),
        "tags": ["leetcode", "bfs", "grid", "islands", "algorithm", "visualization", "vizalgo"],
        "category": "27",
    },
    "lc994_final": {
        "title":       "LC 994 · Rotting Oranges | Multi-source BFS Visualized",
        "description": (
            "Visual walkthrough of LC 994 — Rotting Oranges.\n"
            "Multi-source BFS: all rotten oranges spread simultaneously wave by wave.\n\n"
            "Part of the BFS series: LC 102 → LC 200 → LC 994.\n\n"
            "github.com/algoviz1000/Viz"
        ),
        "tags": ["leetcode", "bfs", "rotting oranges", "multi-source", "algorithm", "visualization", "vizalgo"],
        "category": "27",
    },
    "bfs_final": {
        "title":       "Breadth-First Search | LC 102 → LC 200 → LC 994 Visualized",
        "description": (
            "Full BFS series in one video.\n"
            "LC 102 (Binary Tree) → LC 200 (Islands) → LC 994 (Rotting Oranges).\n"
            "Each problem builds on the same BFS pattern, visualized frame by frame.\n\n"
            "github.com/algoviz1000/Viz"
        ),
        "tags": ["leetcode", "bfs", "breadth first search", "algorithm", "visualization", "vizalgo", "series"],
        "category": "27",
    },
}

DEFAULT_METADATA = {
    "title":       "Algorithm Visualization | vizalgo",
    "description": "Algorithm visualization.\n\ngithub.com/algoviz1000/Viz",
    "tags":        ["algorithm", "visualization", "vizalgo"],
    "category":    "27",
}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def get_credentials():
    creds = None

    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not SECRETS.exists():
                print(f"Error: client_secrets.json not found at {SECRETS}")
                print("Download it from: console.cloud.google.com/apis/credentials?project=vizalgo-490301")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(SECRETS), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN.write_text(creds.to_json())

    return creds


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

def upload(video_path: str, privacy: str = "private"):
    path = Path(video_path)
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    stem = path.stem
    meta = METADATA.get(stem, DEFAULT_METADATA)

    print(f"Authenticating...")
    creds   = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title":       meta["title"],
            "description": meta["description"],
            "tags":        meta["tags"],
            "categoryId":  meta["category"],
        },
        "status": {
            "privacyStatus": privacy,
        },
    }

    print(f"Uploading: {path.name}")
    print(f"  Title:   {meta['title']}")
    print(f"  Privacy: {privacy}")

    media = MediaFileUpload(str(path), chunksize=-1, resumable=True,
                            mimetype="video/mp4")

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"  Uploading... {pct}%", end="\r")

    video_id = response["id"]
    print(f"\nDone: https://youtu.be/{video_id}")
    return video_id


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(prog="upload")
    parser.add_argument("video", help="Path to the MP4 file")
    parser.add_argument("--privacy", choices=["private", "unlisted", "public"],
                        default="private",
                        help="Privacy setting (default: private)")
    ns = parser.parse_args()
    upload(ns.video, privacy=ns.privacy)

if __name__ == "__main__":
    main()
