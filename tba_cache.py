import base64
import datetime
import logging
import sys

import requests

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

import creds
from tba_entities import TBAData


class TBACache:

    def __init__(self, offline=False, lazy=False, db_file_name='tba.db', echo=False):
        self.logger = logging.getLogger(__name__)
        self.db_file_name = db_file_name
        self.already_fetched : dict[str,TBAData] = {}
        self.offline = offline
        self.lazy = lazy
        self.engine = create_engine(f'sqlite:///{db_file_name}', echo=echo)
        self.session = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        return False

    def fetch(self, url=None):
        cache_entry = self.already_fetched.get(url, None)

        if cache_entry is not None:
            return cache_entry.data

        if self.session is None:
            self.session = sessionmaker(bind=self.engine)()

        existing_tba_data = self.session.get(TBAData, url)
        etag = None
        if existing_tba_data is not None:
            if self.offline or self.lazy:
                return existing_tba_data.data
            etag = existing_tba_data.etag
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

        self.logger.info("got a %d for %s", response.status_code, url)

        # throw exception for a 4xx or 5xx
        response.raise_for_status()

        # check for other catastrophic codes here

        # and we are good!

        if response.status_code == 304:
            return existing_tba_data.data

        tba_data = TBAData(
            url=url,
            etag=response.headers['etag'],
            date=datetime.datetime.now().astimezone(),
            data_json=response.content
        )
        self.already_fetched[url] = tba_data
        self.session.add(tba_data)
        self.session.commit()

        return tba_data.data

    def done(self):
        pass

    def get_teams_at_event(self, event_key=None):
        return self.fetch(f"/api/v3/event/{event_key}/teams")

    def get_team_statuses_at_event(self, event_key=None):
        return self.fetch(f"/api/v3/event/{event_key}/teams/statuses")

    def get_team_status_at_event(self, event_key=None, team_key=None):
        return self.fetch(f"/api/v3/team/{team_key}/event/{event_key}/status")

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

    def get_events_simple(self, year=None):
        return self.fetch(f"/api/v3/events/{year}/simple")

    def get_district_events(self, district_key=None):
        return self.fetch(f"/api/v3/district/{district_key}/events")

    def get_district_rankings(self, district_key=None):
        return self.fetch(f"/api/v3/district/{district_key}/rankings")

    def get_district_teams_simple(self, district_key=None):
        return self.fetch(f"/api/v3/district/{district_key}/teams/simple")

    def get_team_media(self, team_key=None, year=None):
        return self.fetch(f"/api/v3/team/{team_key}/media/{year}")

    def get_team_matches_at_event(self, team_key=None, event_key=None):
        return self.fetch(f"/api/v3/team/{team_key}/event/{event_key}/matches")

    def get_team_awards_at_event(self, team_key=None, event_key=None):
        return self.fetch(f"/api/v3/team/{team_key}/event/{event_key}/awards")

    def get_team_districts(self, team_key=None):
        return self.fetch(f"/api/v3/team/{team_key}/districts")

    def get_team_years_participated(self, team_key=None):
        return self.fetch(f"/api/v3/team/{team_key}/years_participated")

    def get_team_event_keys(self, team_key=None, year=None):
        if year is None:
            return self.fetch(f"/api/v3/team/{team_key}/events/keys")
        else:
            return self.fetch(f"/api/v3/team/{team_key}/events/{year}/keys")

    def get_team_events(self, team_key=None, year=None):
        if year is None:
            return self.fetch(f"/api/v3/team/{team_key}/events")
        else:
            return self.fetch(f"/api/v3/team/{team_key}/events/{year}")

    def make_avatar(self, team_key=None, year=None):
        media_list = self.get_team_media(team_key=team_key, year=year)
        if media_list is not None:
            for media in media_list:
                if media['type'] == 'avatar':
                    fk = media['foreign_key']
                    b64 = media.get('details', {}).get('base64Image', None)
                    if b64 is not None:
                        content = base64.b64decode(b64)
                        fn = f"avatars/{fk}.png"
                        with open(fn, "wb") as f:
                            f.write(content)


def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    with TBACache() as cache:
        # print(cache.fetch(url='/api/v3/event/2023misjo/teams/simple'))
        # print(cache.get_event('2025misjo'))
        # print(cache.get_teams_at_event('2023misjo'))
        # print(cache.get_matches_for_event('2023misjo'))

        event_keys = cache.get_event_keys_for_team('frc3620', 2025)
        for event_key in event_keys:
            matches = cache.get_matches_for_event(event_key)
            for match in matches:
                print(event_key, match)

        # print(cache.get_event_keys_for_team('frc3620'))


if __name__ == '__main__':
    main(sys.argv[1:])

