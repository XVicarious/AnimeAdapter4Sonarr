"""
Anime Adapter for Sonarr (aa4s)
"""

import tvdb_api
import requests
import pprint
import datetime

TVDB_API = tvdb_api.Tvdb()
ANILIST = {
    'url': 'https://graphql.anilist.co',
    'header': ''
}
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

PP = pprint.PrettyPrinter(indent=2)

# Testing variables
__tvdb_id = 81831
__anilist_id = 3455

def clean_tvdb_seasons(tvdb_seasons):
    """Clean up unneeded data on the seasons fetched from TVDB"""
    clean_seasons = dict()
    for index, season in tvdb_seasons.items(): 
        clean_episodes = dict()
        for episode_index, episode in season.items():
            clean_episodes.update({episode_index: {
                'episodeName': episode['episodeName'],
                'airDate': episode['firstAired']
            }})
        clean_seasons.update({index: clean_episodes})
    return clean_seasons

def fetch_tvdb_seasons(tvdb_id):
    """Return all seasons of the given show."""
    seasons = dict()
    for key in TVDB_API[tvdb_id].keys():
        seasons.update({key: TVDB_API[tvdb_id][key]})
    print("{} has {} seasons".format(tvdb_id, len(seasons)))
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
    return clean_anilist_seasons(anime)

def dates_within_n_days(date1, date2, n):
    if abs((date1 - date2).days) < n + 1:
        return True
    return False

def map_tvdb_to_anilist(tvdb_seasons, anilist_seasons):
    """Attempt to map episodes from tvdb to anilist."""
    mapped_episodes = dict()
    temp_tvdb = tvdb_seasons
    # Loop through each of the "seasons" (really shows) on anilist
    for season in anilist_seasons:
        # Initialize the season with type and entries for each episode
        mapped_episodes.update({
            season['id']: {
                'type': season['type'],
                'episodes': dict.fromkeys(list(range(1, season['episodes'])), [])
            }
        })
        # Get the start and dates in datetime format
        ani = {}
        ani['start'] = datetime.datetime.strptime(season['dates']['start'], "%Y-%m-%d")
        ani['end'] = datetime.datetime.strptime(season['dates']['end'], "%Y-%m-%d")
        # Loop through each episode in the anilist season
        for map_index, map_episode in enumerate(mapped_episodes[season['id']]['episodes']):
            # If we solved an episode, we should set this to true to not waste time going through the rest
            solved = False
            # Each TVDB season, anime specials and OVAs are all in season 0 regardless of what season they're associated with
            for index, tvdb_season in tvdb_seasons.items():
                # Each episode in the season
                for episode_index, tvdb_episode in tvdb_season.items():
                    # TVDB gives us nice information about when the episodes aired, unlike Anilist...
                    tvdb_date = datetime.datetime.strptime(tvdb_episode['airDate'], "%Y-%m-%d")
                    # If the episode is within a day of the start or end date or within the season range
                    if dates_within_n_days(tvdb_date, ani['start'], 1) or dates_within_n_days(tvdb_date, ani['end'], 1) or tvdb_date >= ani['start'] and tvdb_date <= ani['end']:
                        #print("Map Season: {}, Map Episode: {}, TVDB Season: {}, TVDB Episode: {}".format(
                        #    season['id'], map_episode, index, episode_index
                        #))
                        # Testing the first two conditions again, because I'm bad
                        if dates_within_n_days(tvdb_date, ani['start'], 1) or dates_within_n_days(tvdb_date, ani['end'], 1):
                            datey = ani['start']
                            if dates_within_n_days(tvdb_date, ani['end'], 1):
                                datey = ani['end']
                            print("Season {} Episode {} aired on {} and is equal to {}".format(
                                index, episode_index, tvdb_date, datey
                            ))
                            print("PERFECT MATCH: Anilist {}-{} maps to TVDB {}-{}".format(season['id'], map_episode, index, episode_index))
                        mapped_episodes[season['id']]['episodes'][map_episode].append([index, episode_index])
                    if solved:
                        break
                if solved:
                    break
        break
    return mapped_episodes

def map_anilist_show_to_tvdb_season(anilist_season, tvdb_seasons):
    """Attempt to map a show from anilist to tvdb seasons and episodes"""
    for episode in anilist_season:
        return None

#PP.pprint(
map_tvdb_to_anilist(clean_tvdb_seasons(fetch_tvdb_seasons(__tvdb_id)), fetch_anilist_seasons(__anilist_id))
#)
# PP.pprint(clean_tvdb_seasons(fetch_tvdb_seasons(__tvdb_id)))
## PP.pprint(fetch_tvdb_seasons(__tvdb_id))
# PP.pprint(fetch_anilist_show(__anilist_id))
# PP.pprint(fetch_anilist_seasons(__anilist_id))
# clean_anilist_seasons(fetch_anilist_seasons(__anilist_id))
