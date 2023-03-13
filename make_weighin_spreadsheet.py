import json
import os

import jsonpath_ng


jsonpath_cache = {}


def json_parse(json_expression_text):
    rv = jsonpath_cache.get(json_expression_text, None)
    if rv is None:
        jsonpath_cache[json_expression_text] = rv = jsonpath_ng.parse(json_expression_text)
    return rv


def main():
    dir = "2023misjo"
    with open(os.path.join(dir, 'teams.json'), 'r') as infile:
        team_array = json.load(infile)

        team_dict = {}
        for team in team_array:
            team_dict[team['key']] = team

    with open(os.path.join(dir, 'matches.json'), 'r') as infile:
        match_array = json.load(infile)

        for match in match_array:
            comp_level = match['comp_level']
            if comp_level != 'qm':
                continue

            json_find_results = (json_parse('*..team_keys').find(match))
            print(json_find_results)
            match_number = match['match_number']
            for json_find_result in json_find_results:
                for team_key in json_find_result.value:
                    team = team_dict[team_key]
                    team['last_match'] = max(team.get('last_match', -1), match_number)

    for team in team_dict.values():
        print(team['team_number'], team['nickname'], team['last_match'])



if __name__ == '__main__':
    main()

