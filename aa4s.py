"""
Anime Adapter for Sonarr (aa4s)
"""

import tvdb_api
from Pymoe import Anilist
import requests
import pprint

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
__tvdb_id = 81831
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
                format
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
    anilist_data = {"id": anilist_id}
    request = requests.post(
        ANILIST_URL,
        headers=ANILIST_HEADER,
        json={"query": query_string, "variables": anilist_data})
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
        relations = show['relations']
        for index, value in enumerate(relations['nodes']):
            if relations['edges'][index]['relationType'] in ANILIST_RELATIONS:
                if value['id'] not in get_ids_in_set(anime):
                    anime.append(fetch_anilist_show(value['id'])['data']['Media'])
    return anime

def clean_anilist_seasons(anilist_seasons):
    """Strip any unneeded data from what was fetched from anilist."""
    clean_seasons = []
    for title in anilist_seasons:
        start = title['startDate']
        end = title['endDate']
        clean_seasons.append({
            "id": title['id'],
            "title": title['title']['romaji'],
            "dates": {
                "start": "{}-{}-{}".format(start['year'], start['month'], start['day']),
                "end": "{}-{}-{}".format(end['year'], end['month'], end['day'])
            },
            "type": title['format'],
            "episodes": title['episodes']
        })
    return clean_seasons

def map_tvdb_to_anilist(tvdb_seasons, anilist_seasons):
    """Attempt to map episodes from tvdb to anilist."""
    return None

#pp = pprint.PrettyPrinter(indent=2)
#pp.pprint(fetch_tvdb_seasons(__tvdb_id)[2][12]['firstAired'])
#print(fetch_anilist_seasons(__anilist_id))
#clean_anilist_seasons(fetch_anilist_seasons(__anilist_id))
