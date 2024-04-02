import argparse
import base64
import json
import logging
import re
import sys

import tba_cache


def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    parser = argparse.ArgumentParser()
    parser.add_argument("--event", help="event key", required=True)
    parser.add_argument("--home", help="team key for home team", default="frc3620")
    parser.add_argument("--offline", action='store_true', help="don't go to internet")
    parser.add_argument("--lazy", action='store_true', help="only go to internet if not in cache")
    args = parser.parse_args(argv)

    with tba_cache.TBACache(offline=args.offline, lazy=args.lazy) as tba:
        year = re.sub(r'^.*(\d{4}).*$', r'\1', args.event)

        match_array = tba.get_matches_for_team_at_event(team_key=args.home, event_key=args.event)

        partners = set()
        our_matches = []

        all_teams_at_event = tba.get_teams_at_event(event_key=args.event)
        team_dict = { t['key']: t for t in all_teams_at_event }

        for match in match_array:
            comp_level = match['comp_level']
            if comp_level != 'qm':
                continue

            for color, alliances in match.get('alliances', {}).items():
                team_keys = alliances.get('team_keys', [])
                if args.home in team_keys:
                    # we have our alliance
                    for team_key in team_keys:
                        partners.add(team_key)
                    our_matches.append ({'match': match['match_number'], 'alliance': team_keys, 'color': color})
                    break

        for team_key in partners:
            media_list = tba.get_team_media(team_key=team_key, year=year)
            # jsonpath_ng does not like "$..[?(@.type=='avatar')]"
            if media_list is not None:
                for media in media_list:
                    if media['type'] == 'avatar':
                        fk = media['foreign_key']
                        b64 = media.get('details', {}).get('base64Image', None)
                        if b64 is not None:
                            content = base64.b64decode(b64)
                            fn = f"avatars/{fk}.png"
                            team_dict[team_key]['avatar_fn'] = fn
                            with open(fn, "wb") as f:
                                f.write(content)

        with open(args.event + '_xlights.json', 'w') as file:
            o = {
                "teams": team_dict,
                "matches": our_matches
            }
            json.dump(o, file, indent=1)


if __name__ == '__main__':
    main(sys.argv[1:])
