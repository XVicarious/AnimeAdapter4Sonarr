"""
Kitsu API bindings, far from complete.
Uses typing library because it was neat and I wanted to try it out
That might become an issue
"""

from enum import Enum
from typing import NewType
from typing import List
from typing import Type
import requests

MapId = NewType("MapId", int)
AnimeId = NewType("AnimeId", int)


class Kitsu:
    """
    Random API shit for Kitsu, not complete.
    Would be nice to complete since PyMoe doesn't support everything
    There is 0 error handling here as of yet so... You'll (probably
    just me) will have to deal with it.
    """

    KITSU_PATH = "https://kitsu.io/api"
    API_PATH = KITSU_PATH + "/edge"
    OAUTH_PATH = KITSU_PATH + "/oauth"

    MAPPING_PATH = API_PATH + "/mappings"
    ANIME_PATH = API_PATH + "/anime"

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    class SubType(Enum):
        """ Different show types for Kitsu. """
        ONA,
        OVA,
        TV,
        movie,
        music,
        special

    class Mapping(Enum):
        """ The different types of mappings that Kitsu has,
            this is incomplete. """
        ANIDB = "anidb"
        ANILIST = "anilist"
        MAL_ANIME = "myanimelist/anime"
        MAL_MANGA = "myanimelist/manga"
        TVDB = "thetvdb"
        TVDB_SEASON = "thetvdb/season"
        TVDB_SERIES = "thetvdb/series"

    def get_from_kitsu_map(self,
                           map_type: Type[Mapping],
                           map_id) -> List[MapId]:
        """ Get a list of MapIds from a given map. """
        mapping_url = (self.MAPPING_PATH +
                       "?filter[externalSite]={}&filter[externalId]={}"
                       .format(
                           map_type.value, map_id
                       ))
        json = requests.get(mapping_url).json()
        mappings = []
        for entry in json['data']:
            if entry['id'] is not None:
                mappings.append(MapId(entry['id']))
        return mappings

    def get_map_by_id(self, map_id: MapId):
        """ Gets a specific map based on a MapId. """
        mapping_url = self.MAPPING_PATH + "/{}".format(map_id)
        return requests.get(mapping_url).json()['data']

    def get_item_from_map(self, map_id: MapId):
        """ Gets the item that maps to a specific MapId. """
        mapping_url = self.MAPPING_PATH + "/{}/item".format(map_id)
        return requests.get(mapping_url).json()['data']

    def get_anime_mappings(self, anime_id: AnimeId):
        """ Get all the mappings for a specific anime. """
        mappings_url = self.ANIME_PATH + "/{}/mappings".format(anime_id)
        return requests.get(mappings_url).json()['data']

    def get_anime_episodes(self, anime_id: AnimeId):
        """ Get all the episodes from an anime. """
        episodes_url = self.ANIME_PATH + "/{}/episodes".format(
            anime_id
        )
        return requests.get(episodes_url).json()['data']
