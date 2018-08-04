"""
Anime Adapter for Sonarr (aa4s)
"""

import tvdb_api
from Pymoe import Anilist
import requests

TVDB_API = tvdb_api.Tvdb()
ANILIST_API = Anilist()
ANILIST_URL = "https://graphql.anilist.co"
ANILIST_HEADER = {
    "Content-Type": "application/json",
    "User-Agent": "aa4s",
    "Accept": "application/json"
}
ANILIST_RELATIONS = [
    "PREQUEL",
    "SEQUEL",
    "SIDE_STORY",
    "SUMMARY"
]

# Testing variables
__tvdb_id = 281251
__anilist_id = 5081

def fetch_tvdb_seasons(tvdb_id):
    """Return all seasons of the given show."""
    seasons = dict()
    for key in TVDB_API[tvdb_id].keys():
        seasons.update({key: TVDB_API[tvdb_id][key]})
    return seasons

def fetch_anilist_show(anilist_id):
    """Return the given anime, and ids of all related anime."""
    query_string = """\
        query($id: Int) {
            Media(id: $id, type: ANIME) {
                id
                title {
                    romaji
                }
                startDate {
                    year
                    month
                    day
                }
                endDate {
                    year
                    month
                    day
                }
                episodes
                relations {
                    edges {
                        relationType
                    }
                    nodes {
                        id
                    }
                }
            }
        }
    """
    vars = {"id": anilist_id}
    request = requests.post(ANILIST_URL, headers=ANILIST_HEADER, json={"query": query_string, "variables": vars})
    json = {}
    try:
        json = request.json()
    except:
        print("ERROR!")
        return None
    return json

def get_ids_in_set(set_var):
    """Return the ids for all of the elements in a given array."""
    ids = []
    for element in set_var:
        ids.append(element['id'])
    return ids

def fetch_anilist_seasons(anilist_id):
    """Return all anime related to the given anime."""
    anime = []
    anime.append(fetch_anilist_show(anilist_id)['data']['Media'])
    for show in anime:
        for index, value in enumerate(show['relations']['nodes']):
            if show['relations']['edges'][index]['relationType'] in ANILIST_RELATIONS and value['id'] not in get_ids_in_set(anime):
                anime.append(fetch_anilist_show(value['id'])['data']['Media'])
    return anime

# fetch_tvdb_seasons(281251)
print(fetch_anilist_seasons(__anilist_id))
