import os

from serpapi import GoogleSearch


def web_search(search_query: str):
    params = {
        "engine": "google",
        "q": search_query,
        "api_key": os.getenv("SERP_API_KEY")
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    if "organic_results" in results:
        return results["organic_results"][0]["snippet"]

    return "No relevant results found."
