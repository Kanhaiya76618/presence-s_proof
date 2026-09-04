import os
import json
import requests
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional

SOCIAL_DOMAINS = [
    "linkedin.com",
    "instagram.com",
    "x.com",
    "twitter.com",
    "facebook.com",
    "tiktok.com",
    "reddit.com",
    "youtube.com"
]

def upload_image_for_search(local_path: str) -> str:
    """
    Upload local image to get a publicly accessible URL for Google Lens.
    Tries multiple reliable ephemeral uploaders with failover.
    """
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Local file not found: {local_path}")

    # Strategy 1: tmpfiles.org
    try:
        with open(local_path, "rb") as f:
            resp = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files={"file": f},
                timeout=30
            )
        if resp.status_code == 200:
            data = resp.json()
            url = data.get("data", {}).get("url", "")
            if url:
                # tmpfiles returns https://tmpfiles.org/12345/image.png
                # Direct download link is https://tmpfiles.org/dl/12345/image.png
                return url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    except Exception as e:
        pass

    # Strategy 2: 0x0.st fallback
    try:
        with open(local_path, "rb") as f:
            resp = requests.post(
                "https://0x0.st",
                files={"file": f},
                headers={"User-Agent": "facechain-client/1.0"},
                timeout=30
            )
        if resp.status_code == 200 and resp.text.strip().startswith("http"):
            return resp.text.strip()
    except Exception:
        pass

    raise RuntimeError(
        "Could not auto-upload image to get public URL for Google Lens. "
        "Please provide --image-url <public-url> directly."
    )

def google_lens_search(
    image_url: str,
    api_key: str,
    cache_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query SerpAPI Google Lens engine.
    If cache_path exists and is valid, loads from cache to preserve API quota.
    """
    if cache_path and os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    if not api_key:
        raise ValueError("SERPAPI_KEY is not set in environment or passed to CLI.")

    params = {
        "engine": "google_lens",
        "url": image_url,
        "api_key": api_key,
        "hl": "en"
    }

    response = requests.get("https://serpapi.com/search.json", params=params, timeout=90)
    response.raise_for_status()
    data = response.json()

    if cache_path:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    return data

def filter_social_matches(lens_results: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Filters Google Lens visual matches for social media platforms.
    """
    visual_matches = lens_results.get("visual_matches", [])
    matches = []
    seen_urls = set()

    for item in visual_matches:
        link = item.get("link", "")
        if not link or link in seen_urls:
            continue

        host = urlparse(link).netloc.lower()
        matched_platform = None
        for domain in SOCIAL_DOMAINS:
            if domain in host:
                matched_platform = domain.split(".")[0]
                break

        if matched_platform:
            seen_urls.add(link)
            matches.append({
                "platform": matched_platform,
                "url": link,
                "title": item.get("title", ""),
                "source": item.get("source", host),
                "thumbnail": item.get("thumbnail", ""),
                "position": item.get("position", len(matches) + 1)
            })
            if len(matches) >= limit:
                break

    return matches

def download_candidate_image(thumbnail_url: str, output_path: str) -> Optional[str]:
    """Download candidate thumbnail or image to a local file for face comparison."""
    if not thumbnail_url:
        return None

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        resp = requests.get(thumbnail_url, timeout=6)
        if resp.status_code == 200 and len(resp.content) > 500:

            with open(output_path, "wb") as f:
                f.write(resp.content)
            return output_path
    except Exception:
        pass
    return None
