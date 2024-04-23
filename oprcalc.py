import argparse
import copy
import logging
import sys

import tba_cache

from math import *


def matrices(team_keys, matches, metric_extractor=None):
    opr_A = [[0] * len(team_keys) for _ in range(len(team_keys))]

    opr_b = [0] * len(team_keys)
    dpr_b = [0] * len(team_keys)

    if metric_extractor is None:
        metric_extractor = score_metric_extractor

    for match in matches:
        rs = metric_extractor(match, 'red')
        bs = metric_extractor(match, 'blue')

        if rs is None or bs is None:
            continue

        r1 = team_keys.index(match['alliances']['red']['team_keys'][0])
        r2 = team_keys.index(match['alliances']['red']['team_keys'][1])
        r3 = team_keys.index(match['alliances']['red']['team_keys'][2])
        b1 = team_keys.index(match['alliances']['blue']['team_keys'][0])
        b2 = team_keys.index(match['alliances']['blue']['team_keys'][1])
        b3 = team_keys.index(match['alliances']['blue']['team_keys'][2])

        opr_A[r1][r1] += 1
        opr_A[r1][r2] += 1
        opr_A[r1][r3] += 1

        opr_A[r2][r1] += 1
        opr_A[r2][r2] += 1
        opr_A[r2][r3] += 1

        opr_A[r3][r1] += 1
        opr_A[r3][r2] += 1
        opr_A[r3][r3] += 1

        opr_A[b1][b1] += 1
        opr_A[b1][b2] += 1
        opr_A[b1][b3] += 1

        opr_A[b2][b1] += 1
        opr_A[b2][b2] += 1
        opr_A[b2][b3] += 1

        opr_A[b3][b1] += 1
        opr_A[b3][b2] += 1
        opr_A[b3][b3] += 1

        opr_b[r1] += rs
        opr_b[r2] += rs
        opr_b[r3] += rs
        opr_b[b1] += bs
        opr_b[b2] += bs
        opr_b[b3] += bs

        dpr_b[r1] += bs
        dpr_b[r2] += bs
        dpr_b[r3] += bs
        dpr_b[b1] += rs
        dpr_b[b2] += rs
        dpr_b[b3] += rs

    return opr_A, opr_b, dpr_b


def dumpMatrix(A, team_keys):
    for i, t in enumerate(team_keys):
        print("team", i, t)


    for i, row in enumerate(A):
        print(i,'{:8}'.format(team_keys[i]), ''.join(['{:4}'.format(item) for item in row]))


def getL1(m):
    final = [[0.0]*len(m) for _ in range(len(m))]
    for i in range(len(m)):
        for j in range(i+1):
            final[i][j] = m[i][j] - sum(final[i][k] * final[j][k] for k in range(j))
            if i == j:
                final[i][j] = sqrt(final[i][j])
            else:
                if final[j][j] == 0:
                    print("boom!", i, j, final)
                final[i][j] /= final[j][j]
    return final


def getL2(A):
    # https://rosettacode.org/wiki/Cholesky_decomposition#Python
    L = [[0.0] * len(A) for _ in range(len(A))]
    for i in range(len(A)):
        for j in range(i+1):
            s = sum(L[i][k] * L[j][k] for k in range(j))
            L[i][j] = sqrt(A[i][i] - s) if (i == j) else \
                      (1.0 / L[j][j] * (A[i][j] - s))
    return L


def forwardSubstitute(m,n):
    final = list(n)
    for i in range(len(m)):
        final[i] -= sum(m[i][j]*final[j] for j in range(i))
        final[i] /= m[i][i]
    return final


def backSubstitute(m,n):
    final = list(n)
    l = range(len(m)-1, -1, -1)
    for i in l:
        final[i] -= sum(m[i][j]*final[j] for j in range(i+1,len(m)))
        final[i] /= m[i][i]
    return final


def transpose(arr):
    return [[arr[y][x] for y in range(len(arr))] for x in range(len(arr[0]))]


def cholesky(L, b):
    y = forwardSubstitute(L, b)
    return backSubstitute(transpose(L), y)


def calc(teams, matches, offense_metric_name=None, defense_metric_name=None, metric_extractor=None):
    if len(matches) == 0:
        return

    team_dict = {team['key']: team for team in teams}
    team_keys = set()

    for match in matches:
        for i in range(3):
            team_keys.add(match['alliances']['red']['team_keys'][i])
            team_keys.add(match['alliances']['blue']['team_keys'][i])
    team_keys = list(team_keys)
    team_keys.sort()

    opr_A, opr_b, dpr_b = matrices(team_keys, matches, metric_extractor=metric_extractor)

    dumpMatrix(opr_A, team_keys)

    opr_L = getL2(opr_A)

    opr_x = cholesky(opr_L, opr_b)
    dpr_x = cholesky(opr_L, dpr_b)

    for team_key, opr, dpr in zip(team_keys, opr_x, dpr_x):
        team = team_dict[team_key]
        metrics = team['metrics']
        if offense_metric_name is not None:
            metrics[offense_metric_name] = opr
        if defense_metric_name is not None:
            metrics[defense_metric_name] = dpr


def score_metric_extractor(match, color):
    try:
        return match['score_breakdown'][color]['totalPoints']
    except TypeError as e:
        # probably not subscriptable
        return None


def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    parser = argparse.ArgumentParser()
    parser.add_argument("--event", help="event key", required=True)
    parser.add_argument("--offline", action='store_true', help="don't go to internet")
    parser.add_argument("--lazy", action='store_true', help="only go to internet if not in cache")
    args = parser.parse_args(argv)

    with tba_cache.TBACache(offline=args.offline, lazy=args.lazy) as tba:
        teams = copy.deepcopy(tba.get_teams_at_event(args.event))

        for team in teams:
            team['metrics'] = {}

        all_matches = tba.get_matches_for_event(args.event)
        matches = [match for match in all_matches if match['comp_level'] == 'qm']
        matches.sort(key=lambda match: match['match_number'])

        calc(teams, matches, offense_metric_name='opr', metric_extractor=score_metric_extractor)
        calc(teams, matches, defense_metric_name='dpr', metric_extractor=score_metric_extractor)
        calc(teams, matches, offense_metric_name='opr2', defense_metric_name='dpr2')

        for team in teams:
            print(team['team_number'], team['nickname'], team['metrics'])


if __name__ == '__main__':
    main(sys.argv[1:])
