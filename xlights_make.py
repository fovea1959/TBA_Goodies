import argparse
import json
import logging
import os
import re
import sys

import XLights


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", help="event key", required=True)
    parser.add_argument("--field", help="field name", required=True)
    args = parser.parse_args(argv)

    year = re.sub(r'^.*(\d{4}).*$', r'\1', args.event)

    with open(args.event + '_xlights.json', 'r') as file:
        o = json.load(file)
        teams = o['teams']
        matches = o['matches']

        pane_length = 3.0;

        for match in matches:
            color = match['color']
            number = match['match']
            members = match['alliance']
            color_palette = XLights.Palette('#ff0000' if color == "red" else '#0000ff')

            sequence = XLights.Sequence(layers=2)

            sequence.add_effect(0,
                                XLights.PicturesEffect(Pictures_Filename="FIRSTicon_RGB_withTM-resized.png"),
                                sequence.length, sequence.length+pane_length, palette=color_palette)

            sequence.add_effect(0,
                                XLights.TextEffect(Text="Hey!"),
                                sequence.length, sequence.length+pane_length, palette=color_palette)

            t0 = sequence.length
            e0 = XLights.TextEffect(Text=args.field, Text_YStart=16)
            e1 = XLights.TextEffect(Text="Field!", Text_YStart=-16)
            sequence.add_effect(layer_index=0, effect=e0, start=t0, end=t0 + pane_length, palette=color_palette)
            sequence.add_effect(layer_index=1, effect=e1, start=t0, end=t0 + pane_length, palette=color_palette)

            t0 = sequence.length
            e0 = XLights.TextEffect(Text="It's", Text_YStart=16)
            e1 = XLights.TextEffect(Text="us...", Text_YStart=-16)
            sequence.add_effect(layer_index=0, effect=e0, start=t0, end=t0 + pane_length, palette=color_palette)
            sequence.add_effect(layer_index=1, effect=e1, start=t0, end=t0 + pane_length, palette=color_palette)

            t0 = sequence.length
            c = color.capitalize()
            e0 = XLights.TextEffect(Text=f"The {c}", Text_YStart=16, FONTPICKER_Text_Font='bold arial 12 windows-1252')
            e1 = XLights.TextEffect(Text="Alliance.", Text_YStart=-16, FONTPICKER_Text_Font='bold arial 12 windows-1252')
            sequence.add_effect(layer_index=0, effect=e0, start=t0, end=t0 + pane_length, palette=color_palette)
            sequence.add_effect(layer_index=1, effect=e1, start=t0, end=t0 + pane_length, palette=color_palette)

            for team_key in members:
                avatar_filename = f"avatars/avatar_{year}_{team_key}.png"
                if os.path.isfile(avatar_filename):
                    e0 = XLights.MarqueeEffect()
                    e1 = XLights.PicturesEffect(Pictures_Filename=avatar_filename)

                    t0 = sequence.length
                    sequence.add_effect(layer_index=0, effect=e0, start=t0, end=t0 + pane_length, palette=color_palette)
                    sequence.add_effect(layer_index=1, effect=e1, start=t0, end=t0 + pane_length, palette=color_palette)

                team = teams[team_key]

                e0 = XLights.TextEffect(Text=str(team['team_number']), Text_YStart=16)
                e1 = XLights.TextEffect(
                    Text=team['nickname'],
                    Text_YStart=-16,
                    FONTPICKER_Text_Font='bold arial 12 windows-1252',
                    Text_Dir='left'
                )

                t0 = sequence.length
                sequence.add_effect(layer_index=0, effect=e0, start=t0, end=t0 + pane_length, palette=color_palette)
                sequence.add_effect(layer_index=1, effect=e1, start=t0, end=t0 + pane_length, palette=color_palette)

            x = sequence.xml()
            # ET.dump(x)
            break


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main(sys.argv[1:])
