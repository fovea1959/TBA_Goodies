import argparse
import logging
import sys

import tba_cache


def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    parser = argparse.ArgumentParser()
    parser.add_argument("--district", help="district key", required=True)
    parser.add_argument("--offline", action='store_true', help="don't go to internet")
    parser.add_argument("--lazy", action='store_true', help="only go to internet if not in cache")
    args = parser.parse_args(argv)

    with tba_cache.TBACache(offline=args.offline, lazy=args.lazy) as tba:
        teams = tba.get_district_rankings(args.district)

        total_district_points = 0
        total_district_competitions = 0

        got_another = []
        for team in teams:
            competed_so_far = len(team.get('event_points', []))
            point_total = team['point_total']
            if point_total > 0:
                total_district_points = total_district_points + point_total
                total_district_competitions = total_district_competitions + competed_so_far
            if competed_so_far == 1:
                print(team['team_key'], point_total, competed_so_far)
                got_another.append(team['team_key'])

        for team in got_another:
            pass




        print ('Average', total_district_points / total_district_competitions)



if __name__ == '__main__':
    main(sys.argv[1:])
