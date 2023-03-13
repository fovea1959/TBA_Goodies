import json
import logging
import sys

import creds

import requests


class TBACache:

    def __init__(self, offline=False, lazy=False, cache_file_name='tba_cache.json'):
        self.logger = logging.getLogger(__name__)
        self.cache_file_name = cache_file_name
        self.offline = offline
        self.lazy = lazy
        self.cache = dict()
        self.cache_is_dirty = False
        self.fetched = set()

        input_file_exists = False
        try:
            with open(cache_file_name, 'r') as file:
                self.cache = json.load(file)
            input_file_exists = True
        except Exception as err:
            self.logger.warning("enable to read cache %s, error = %s", cache_file_name, err)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.done()
        return False

    def fetch(self, url=None):
        cache_entry = self.cache.get(url, None)

        if url in self.fetched:
            # already fetched this session
            self.logger.info("already fetched %s", url)
            return cache_entry['data']

        etag = None
        if cache_entry is not None:
            if self.offline or self.lazy:
                return cache_entry['data']
            etag = cache_entry['etag']
        else:
            if self.offline:
                # offline and missing
                self.logger.warning("%s not in cache", url)
                return None

        # need to fetch
        headers = {
            'X-TBA-Auth-Key': creds.tba_auth_key,
            'accept': 'application/json',
        }
        if etag is not None:
            headers['If-None-Match'] = etag

        response = requests.get('https://www.thebluealliance.com' + url, headers=headers)

        # throw exception for a 4xx or 5xx
        response.raise_for_status()

        if response.status_code == 304:
            self.fetched.add(url)
            self.logger.info("got a 304 for %s", url)
            return cache_entry['data']

        # check other codes here

        self.fetched.add(url)

        data = response.json()
        self.cache_is_dirty = True

        self.cache[url] = {
            'data': data,
            'etag': response.headers['etag']
        }

        return response.json()

    def done(self):
        if self.cache_is_dirty:
            logging.info("writing cache")
            # TODO need to move the existing file first
            with open (self.cache_file_name, 'w') as file:
                json.dump(self.cache, file, indent=1)
        else:
            logging.info("don't need to write cache")

    def get_teams_at_event(self, event_key=None):
        return self.fetch(f"/api/v3/event/{event_key}/teams/simple")

    def get_matches_for_event(self, event_key=None):
        return self.fetch(f"/api/v3/event/{event_key}/matches")

    def get_event_keys_for_team(self, team_key=None, year=None):
        if year is None:
            return self.fetch(f"/api/v3/team/{team_key}/events/keys")
        return self.fetch(f"/api/v3/team/{team_key}/events/{year}/keys")

    def get_events_for_team(self, team_key=None, year=None):
        if year is None:
            return self.fetch(f"/api/v3/team/{team_key}/events")
        return self.fetch(f"/api/v3/team/{team_key}/events/{year}")

    def get_event(self, event_key=None):
        return self.fetch(f"/api/v3/event/{event_key}")


def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    with TBACache() as cache:
        print(cache.fetch(url='/api/v3/event/2023misjo/teams/simple'))
        print(cache.get_event('2023misjo'))
        print(cache.get_teams_at_event('2023misjo'))
        print(cache.get_matches_for_event('2023misjo'))
        print(cache.get_event_keys_for_team('frc3620', 2023))
        print(cache.get_event_keys_for_team('frc3620'))


if __name__ == '__main__':
    main(sys.argv[1:])

