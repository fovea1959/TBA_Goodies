from math import *
import json


def matrices(teams, matches):
    print(teams)
    opr_A = [[0]*len(teams) for _ in range(len(teams))]

    opr_b = [0]*len(teams)
    dpr_b = [0]*len(teams)

    for match in matches:
        print(match)
        r1 = teams.index(match['alliances']['red']['team_keys'][0])
        r2 = teams.index(match['alliances']['red']['team_keys'][1])
        r3 = teams.index(match['alliances']['red']['team_keys'][2])
        b1 = teams.index(match['alliances']['blue']['team_keys'][0])
        b2 = teams.index(match['alliances']['blue']['team_keys'][1])
        b3 = teams.index(match['alliances']['blue']['team_keys'][2])

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

        rs = match['score_breakdown']['red']['totalPoints']
        bs = match['score_breakdown']['blue']['totalPoints']
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

    return getL(opr_A), opr_b, dpr_b


def totals(ranks):
    return list(zip(*ranks[1:]))[3:8]


def getL(m):
    final = [[0.0]*len(m) for _ in range(len(m))]
    for i in range(len(m)):
        for j in range(i+1):
            final[i][j] = m[i][j] - sum(final[i][k] * final[j][k] for k in range(j))
            if i == j:
                final[i][j] = sqrt(final[i][j])
            else:
                final[i][j] /= final[j][j]
    return final


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


def cholesky(L,b):
    y = forwardSubstitute(L, b)
    return backSubstitute(transpose(L), y)



def calc (teams, matches):
    team_keys = list(team['key'] for team in teams)

    opr_L, opr_b, dpr_b = matrices(team_keys, matches)

    opr_x = cholesky(opr_L, opr_b)

    dpr_x = cholesky(opr_L, dpr_b)

    for team_key, opr, dpr in zip(team_keys, opr_x, dpr_x):
        print (team_key, opr, dpr)


def main():
    with open('2023misjo/teams.json', 'r') as f:
        teams = json.load(f)
    with open('2023misjo/matches.json', 'r') as f:
        all_matches = json.load(f)
    matches = [match for match in all_matches if match['comp_level'] == 'qm']

    calc(teams, matches)


if __name__ == '__main__':
    main()
