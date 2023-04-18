import argparse
import json
import logging
import sys

import XLights


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", help="event key", required=True)
    args = parser.parse_args(argv)

    with open(args.event + '_xlights.json', 'r') as file:
        o = json.load(file)
        teams = o['teams']
        matches = o['matches']

        for match in matches:
            color = match['color']
            number = match['match']
            members = match['alliance']
            color_palette = XLights.Palette('#ff0000' if color == "red" else '#0000ff')

            sequence = XLights.Sequence(layers=2)

            logo = XLights.PicturesEffect(Pictures_Filename="FIRSTicon_RGB_withTM-resized.png")
            sequence.add_effect(0, logo, 0, 3.0, palette=color_palette)


            for team_key in members:
                t0 = sequence.length

                team = teams[team_key]

                e0 = XLights.TextEffect(Text=str(team['team_number']), Text_YStart=16)
                e1 = XLights.TextEffect(
                    Text=team['nickname'],
                    Text_YStart=-16,
                    FONTPICKER_Text_Font='bold arial 12 windows-1252',
                    Text_Dir='left'
                )

                sequence.add_effect(layer_index=0, effect=e0, start=t0, end=t0 + 3, palette=color_palette)
                sequence.add_effect(layer_index=1, effect=e1, start=t0, end=t0 + 3, palette=color_palette)

            x = sequence.xml()
            # ET.dump(x)
            break


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main(sys.argv[1:])
