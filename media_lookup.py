import os
import json
import urllib.parse
import urllib.request

from dotenv import load_dotenv

load_dotenv()


TMDB_TOKEN = os.getenv("TMDB_TOKEN")


BASE_URL = "https://api.themoviedb.org/3"


def tmdb_get(path, params=None):
    params = params or {}

    url = BASE_URL + path

    if params:
        url += "?" + urllib.parse.urlencode(params)

    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {TMDB_TOKEN}",
            "Accept": "application/json"
        }
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def search_title(title, media_type=None):
    """
    Returns the best TMDB match for a movie or TV show.
    """

    if media_type == "Movie":
        endpoint = "/search/movie"

    elif media_type == "TV":
        endpoint = "/search/tv"

    else:
        endpoint = "/search/multi"

    data = tmdb_get(
        endpoint,
        {
            "query": title,
            "language": "en-US",
            "include_adult": "false"
        }
    )

    results = data.get("results", [])

    # Keep only movie / TV results in multi-search
    results = [
        item
        for item in results
        if item.get("media_type") in ("movie", "tv")
        or media_type in ("Movie", "TV")
    ]

    if not results:
        return None

    return results[0]


def get_watch_providers(tmdb_id, media_type, country="US"):
    """
    Returns streaming, rental, and purchase providers.
    """

    if media_type == "Movie":
        path = f"/movie/{tmdb_id}/watch/providers"

    else:
        path = f"/tv/{tmdb_id}/watch/providers"

    data = tmdb_get(path)

    country_data = (
        data.get("results", {})
        .get(country, {})
    )

    def provider_names(key):
        return [
            item["provider_name"]
            for item in country_data.get(key, [])
        ]

    return {
        "stream": provider_names("flatrate"),
        "free": provider_names("free"),
        "ads": provider_names("ads"),
        "rent": provider_names("rent"),
        "buy": provider_names("buy"),
        "link": country_data.get("link")
    }


def lookup_availability(title, media_type, country="US"):
    match = search_title(title, media_type)

    if not match:
        return None

    tmdb_id = match["id"]

    providers = get_watch_providers(
        tmdb_id,
        media_type,
        country
    )

    display_title = (
        match.get("title")
        or match.get("name")
        or title
    )

    release_date = (
        match.get("release_date")
        or match.get("first_air_date")
        or ""
    )

    return {
        "title": display_title,
        "tmdb_id": tmdb_id,
        "release_date": release_date,
        "overview": match.get("overview", ""),
        "providers": providers
    }