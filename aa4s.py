"""
Anime Adapter for Sonarr (aa4s)
"""

import datetime
import pprint
import logging
import pickle
from difflib import SequenceMatcher
import tvdb_api
import requests
from slugify import slugify


from kitsu import Kitsu

#logging.basicConfig(level=logging.DEBUG)

TVDB_API = tvdb_api.Tvdb()

KITSU = Kitsu("dd031b32d2f56c990b1425efe6c42ad847e7fe3ab46bf1299f05ecd856bdb7dd", "54d7307928f63414defd96399fc31ba847961ceaecef3a5fd93144e960c0e151")

WANTED_KITSU_ROLES = [
    KITSU.Role.PARENT_STORY,
    KITSU.Role.SEQUEL,
    KITSU.Role.PREQUEL,
    KITSU.Role.SIDE_STORY,
    # KITSU.Role.ADAPTATION
]

PP = pprint.PrettyPrinter(indent=2)

# Testing variables
__tvdb_id = 81831
__anilist_id = 3455
__anidb_id = 5625
__kitsu_id = 3021


def fetch_kitsu_seasons(kitsu_id):
    """ Fetch all the shows on kitsu that are related """
    all_animes = []

    def __id_in_all(needle):
        for anime in all_animes:
            if anime['id'] == needle:
                return True
        return False

    episodes = KITSU.get_anime_episodes(kitsu_id)
    all_animes.append({'id': kitsu_id, 'episodes': episodes})
    i = 0
    while i < len(all_animes):
        current_relations = KITSU.get_anime_relationship_ids(all_animes[i]['id'], roles=WANTED_KITSU_ROLES)
        for kid in current_relations:
            if not __id_in_all(kid):
                all_animes.append({
                    'id': kid,
                    'episodes': KITSU.get_anime_episodes(kid)
                })
        i += 1
    return all_animes


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
    # print("{} has {} seasons".format(tvdb_id, len(seasons)))
    return clean_tvdb_seasons(seasons)


def get_ids_in_set(set_var):
    """Return the ids for all of the elements in a given array."""
    ids = []
    for element in set_var:
        ids.append(element['id'])
    return ids


def dates_within_n_days(date1, date2, n):
    """ Are the dates within n days of each other """
    if abs((date1 - date2).days) < n + 1:
        return True
    return False


def map_tvdb_to_kitsu(tvdb_seasons, kitsu_seasons, current_map):
    """ Map TVDB episodes to kitsu episodes """
    mapped_episodes = dict() if current_map is None else current_map

    def __is_mapped(season, episode):
        for i, mapped in mapped_episodes.items():
            for m in mapped:
                if [season, episode] in m:
                    return True
        return False

    def __is_mapped_to_season(kitsu_id, season, episode):
        for m in mapped_episodes[kitsu_id]:
            if [season, episode] in m:
                return True
        return False

    def __is_kitsu_mapped(kitsu_id, episode):
        for m in mapped_episodes[kitsu_id]:
            if episode in m:
                return True
        return False

    stored_kitsu = None
    for season in kitsu_seasons:
        kitsu_id = int(season['id'])
        if kitsu_id not in mapped_episodes.keys():
            mapped_episodes.update({kitsu_id: []})

        for episode in season['episodes']:
            kitsu_episode = episode['attributes']['number']
            print("--------------------{}/{}--------------------".format(kitsu_id, kitsu_episode))
            if __is_kitsu_mapped(kitsu_id, kitsu_episode):
                stored_kitsu = episode
                continue
            solved = False
            kitsu_episode = episode['attributes']['number']
            # print("{}-{}".format(kitsu_id, kitsu_episode), episode['attributes']['seasonNumber'])
            airdate = datetime.datetime.strptime("1970-1-1", "%Y-%m-%d")
            try:
                airdate = datetime.datetime.strptime(episode['attributes']['airdate'], "%Y-%m-%d")
            except TypeError:
                " "
                # print("Kitsu episode {}-{} doesn't have an airdate. We'll try to compare the episode names instead.".format(season['id'], episode['attributes']['number']))
            episode_name = ""
            episode_names = []
            try:
                episode_name = slugify(episode['attributes']['canonicalTitle'])
                episode_names = [slugify(x.strip()) for x in episode['attributes']['canonicalTitle'].split("/")]
            except: # todo: add exception type
                " "
                # print("no episode name")
            for season_index, tvdb_season in tvdb_seasons.items():
                for episode_index, tvdb_episode in tvdb_season.items():
                    if __is_mapped(season_index, episode_index):
                        continue
                    tvdb_airdate = datetime.datetime.strptime("1970-1-1", "%Y-%m-%d")
                    try:
                        tvdb_airdate = datetime.datetime.strptime(tvdb_episode['airDate'], "%Y-%m-%d")
                    except: # todo: add exception type
                        " "
                    tvdb_name = slugify(tvdb_episode['episodeName'])
                    tvdb_names = [slugify(x.strip()) for x in tvdb_episode['episodeName'].split("/")]
                    ratio = SequenceMatcher(None, episode_name, tvdb_name).ratio()
                    ratios = []
                    big_index = len(episode_names) if len(episode_names) < len(tvdb_names) else len(tvdb_names)
                    o = 0
                    while o < big_index:
                        ratios.append(str(SequenceMatcher(None, episode_names[o], tvdb_names[o]).ratio()) + "," + episode_names[o] + "," + tvdb_names[o])
                        o += 1
                    average = 0.0
                    if len(ratios) > 1:
                        for ro in ratios:
                            average += float(ro.split(",")[0])
                    try:
                        average = average / len(ratios)
                    except: # todo: add exception type
                        average = 0
                    if dates_within_n_days(airdate, tvdb_airdate, 1) or episode_name == tvdb_name:
                        print("PASS ({}): {} == {}".format(ratio, episode_name, tvdb_name))
                        mapped_episodes[kitsu_id].append([[season_index, episode_index], episode['attributes']['number']])
                        solved = True
                        break
                    else:
                        # print("Matching failed. Details here:")
                        if ratio >= 0:
                            print("FAIL ({}): {} != {}".format(ratio, episode_name, tvdb_name))
                            if len(ratios) > 1:
                                print("EXTRA: AVG {}".format(average))
                                print("EXTRA: {}".format(ratios))
                        # print("K-{}-{}: {} aired on {}".format(kitsu_id, kitsu_episode, episode_name, airdate))
                        # print("T-{}-{}: {} aired on {}".format(season_index, episode_index, slugify(tvdb_episode['episodeName']), tvdb_date))
                    if __is_mapped_to_season(kitsu_id, season_index, episode_index - 1):
                        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                        print("LAST EPISODE FOR THIS SEASON IS IN THE KITSU SEASON!")
                        print("{}-{} might match to kitsu {}-{}".format(season_index, episode_index, kitsu_id, kitsu_episode))
                        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                if solved:
                    break
            stored_kitsu = episode
    return mapped_episodes


# __tvdb_id = 102261
# __kitsu_id = KITSU.get_from_kitsu_map(KITSU.Mapping.TVDB_SERIES, __tvdb_id)[0]
the_map = None
try:
    the_map = pickle.load(open(str(__tvdb_id) + ".pkl", 'rb'))
except:
    print("Map not found for id, starting over")
the_map = map_tvdb_to_kitsu(
    fetch_tvdb_seasons(__tvdb_id),
    fetch_kitsu_seasons(__kitsu_id),
    the_map
)
pickle.dump(the_map, open(str(__tvdb_id) + ".pkl", 'wb'))
