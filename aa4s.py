"""
Anime Adapter for Sonarr (aa4s)
"""

import os
import sys
import xml.etree.ElementTree as ET
import re

import requests
from Pymoe import Kitsu


XEM_URL =\
    "http://thexem.de/map/all?id={origin_id}&origin={origin_name}&destination={destination_name}"
__TVDB_ID = 81831
EPISODE_NUMBERING = r"S(\d*)E(\d*)"

KITSU = Kitsu("dd031b32d2f56c990b1425efe6c42ad847e7fe3ab46bf1299f05ecd856bdb7dd",
              "54d7307928f63414defd96399fc31ba847961ceaecef3a5fd93144e960c0e151")


class ShowNotMappedException(Exception):
    """ Raised when the requested show is not found on XEM """
    def __init__(self, origin, showid):
        super().__init__("XEM does not have the mapping for {} id {}".format(origin, showid))


class EpisodeNotMappedException(Exception):
    """ Raised when the requested episode has not been mapped on XEM """
    def __init__(self, season, episode):
        super().__init__("Season {}, Episode {} is not mapped on XEM!".format(season, episode))


def get_all_names_from_xem(origin="tvdb", season=1):
    xem_names = requests.get("http://thexem.de/map/allNames?origin={}&season={}".format(origin, season))
    if xem_names.status_code != 200:
        raise Exception("Status code is not 200! Something is wrong!")
    json = xem_names.json()
    if json['result'] == "success":
        return json['data']
    raise Exception("I don't know what happened!")


def get_romaji_name_from_tvdb(tvdbid):
    kitsu_req = requests.get("https://kitsu.io/api/edge/mappings?filter[externalSite]=thetvdb/series&filter[externalId]={}".format(tvdbid))
    if kitsu_req.status_code != 200:
        raise Exception("Status code is not 200! Something is wrong!")
    item_link = "https://kitsu.io/api/edge/mappings/{}/item".format(kitsu_req.json()['data'][0]['id'])
    print(item_link)


def get_xem_map(origin_name, origin_id, destination_name):
    request = requests.get(
        XEM_URL.format(
            origin_name=origin_name, origin_id=origin_id, destination_name=destination_name))
    if request.status_code != 200:
        raise Exception("Status code is not 200! Something is wrong!")
    json = request.json()
    if json['result'] == "success":
        return json['data']
    raise ShowNotMappedException(origin_name, origin_id)


def find_mapped_episde(xemmap, source, destination, season, episode):
    for mapped_episode in xemmap:
        if season == mapped_episode[source]["season"]\
                and episode == mapped_episode[source]["episode"]:
            return [mapped_episode[destination]["season"],
                    mapped_episode[destination]["episode"]]
    raise EpisodeNotMappedException(season, episode)


def get_anime_folders(anime_library):
    xem_map = None
    tvdbid = None
    # anidbid = None  # todo: use this for finding specials, maybe?
    for root, dirs, files in os.walk(anime_library):
        path = root.split(os.sep)
        if "tvshow.nfo" in files:
            tree = ET.parse(os.path.join(root, "tvshow.nfo"))
            eroot = tree.getroot()
            try:
                tvdbid = eroot.find("tvdbid").text
                xem_map = get_xem_map("tvdb", tvdbid, "anidb")
            except ShowNotMappedException as snm:
                print(snm)
            except AttributeError:
                print("{} does not have a TVDB id!".format(path[len(path) - 1]))
        elif len(files) > 1 and "season.nfo" in files:
            for file in files:
                if file.endswith("mkv") or file.endswith("mp4"):
                    matches = re.search(EPISODE_NUMBERING, file)
                    if len(matches.groups()) >= 2:
                        episode = None
                        try:
                            episode = find_mapped_episde(xem_map, "tvdb", "anidb",
                                                         int(matches[1]), int(matches[2]))
                        except EpisodeNotMappedException as enm:
                            print(enm)
                        break


print(sys.argv[1])
# print(sys.argv[2])
#get_romaji_name_from_tvdb(__TVDB_ID)
get_anime_folders(str(sys.argv[1]))
