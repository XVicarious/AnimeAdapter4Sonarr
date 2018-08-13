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
    RELATIONSHIP_PATH = API_PATH + "/media-relationships"

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

    class Role(Enum):
        """ Roles for kitsu media relationships """
        ADAPTATION = 0
        ALTERNATIVE_SETTING = 1
        ALTERNATIVE_VERSION = 2
        CHARACTER = 3
        FULL_STORY = 4
        OTHER = 5
        PARENT_STORY = 6
        PREQUEL = 7
        SEQUEL = 8
        SIDE_STORY = 9
        SPINOFF = 10
        SUMMARY = 11
        def __get__(self, instance, owner):
            return self.name.lower()

    class SubType(Enum):
        """ Different show types for Kitsu. """
        ONA = 0
        OVA = 0
        TV = 0
        movie = 0
        music = 0
        special = 0
        def __get__(self, instance, owner):
            return self.name.lower()

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
        def __get__(self, instance, owner):
            return self.value

    def get_from_kitsu_map(self,
                           map_type: Type[Mapping],
                           map_id) -> List[MapId]:
        """ Get a list of MapIds from a given map. """
        mapping_url = (self.MAPPING_PATH +
                       "?filter[externalSite]={}&filter[externalId]={}"
                       .format(
                           map_type, map_id
                       ))
        json = requests.get(mapping_url).json()
        mappings = []
        for entry in json['data']:
            if entry['id'] is not None:
                mappings.append(MapId(entry['id']))
        return mappings

    def get_media(self, anime_id):
        """ Get a media item based on the given id """
        anime_url = self.ANIME_PATH + "/{}".format(anime_id)
        return requests.get(anime_url).json()['data']

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
        json = requests.get(episodes_url).json()
        episodes = json['data']
        current_link = json['links']['first']
        try:
            next_link = json['links']['next']
            last_link = json['links']['last']
        except KeyError:
            return episodes
        while True:
            # set.union(otherset)
            json = requests.get(next_link).json()
            episodes += json['data']
            current_link = next_link
            if current_link == last_link:
                break
            try:
                next_link = json['links']['next']
            except KeyError:
                next_link = last_link
        return episodes

    def get_media_relationships(self, media_id, roles=[]):
        """ Get all relationships of the given media, filter by roles if desired """
        relationship_url = self.RELATIONSHIP_PATH + "?filter[sourceId]={}&filter[role]={}".format(
            media_id, ",".join(roles)
        )
        return requests.get(relationship_url).json()['data']

    def get_item_by_relationship(self, relationship_id):
        relationship_url = self.RELATIONSHIP_PATH + "/{}".format(relationship_id)
        relation_item_id = requests.get(relationship_url).json()['data']['data']['id']
        return self.get_media(relation_item_id)

    def get_anime_relationships(self, anime_id: AnimeId, roles=[]):
        """ Get all relationships of the given anime, filter by roles if desired """
        return self.get_media_relationships(anime_id, roles=roles)

    def get_anime_relationship_ids(self, anime_id, roles=[]):
        raw_anime_relationships = self.get_anime_relationships(anime_id, roles=roles)
        id_relations = []
        for relation in raw_anime_relationships:
            if relation is not None:
                id_relations.append(
                    requests.get(relation['relationships']['destination']['links']['self']).json()['data']['id']
                )
        return id_relations

    def get_anime_relationships_nice(self, anime_id, roles=[]):
        raw_anime_relationships = self.get_anime_relationships(anime_id, roles=roles)
        nice_relations = []
        for relation in raw_anime_relationships:
            if relation is not None:
                rel = requests.get(relation['relationships']['destination']['links']['self']).json()['data']['id']
                nice_relations.append(self.get_media(rel))
        return nice_relations
