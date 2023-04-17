import argparse
import json
import logging
import sys

import xml.etree.ElementTree as ET


class Effect:
    def __init__(self, **kwargs):
        self.props = self.make_value_dict(**kwargs)

    def make_value_dict(self, **kwargs):
        d = self.get_defaults()
        rv = d.copy()
        for k, v in kwargs.items():
            logging.debug("looking to see what matches %s", k)
            ok = False
            for k1 in d.keys():
                if k1.endswith(f"_{k}"):
                    rv[k1] = v
                    ok = True
                    logging.debug("%s matches %s", k1, k)
                    break
            if not ok:
                logging.error("what is option %s", k)
        return rv

    def get_defaults(self):
        return {}

    def xml(self):
        x = ET.Element('Effect')
        t = []
        for k, v in self.props.items():
            if v is not None:
                if type(v) is str:
                    v = v.replace(',', '&comma;')
                t.append(f"{k}={v}")
        x.text = ",".join(t)
        return x


class TextEffect(Effect):
    def get_defaults(self):
        return {
            'E_CHECKBOX_TextToCenter': 0,
            'E_CHECKBOX_Text_PixelOffsets': 0,
            'E_CHOICE_Text_Count': 'none',
            'E_CHOICE_Text_Dir': 'none',
            'E_CHOICE_Text_Effect': 'normal',
            'E_CHOICE_Text_Font': 'Use OS Fonts',
            'E_FILEPICKERCTRL_Text_File': '',
            'E_FONTPICKER_Text_Font': 'bold arial 18 windows-1252',
            'E_SLIDER_Text_XEnd': 0,
            'E_SLIDER_Text_XStart': 0,
            'E_SLIDER_Text_YEnd': 0,
            'E_SLIDER_Text_YStart': 0,
            'E_TEXTCTRL_Text': None,
            'E_TEXTCTRL_Text_Speed': 28,
            'T_TEXTCTRL_Fadein': 1.00,
            'T_TEXTCTRL_Fadeout': 1.00
        }


class MarqueeEffect(Effect):
    def get_defaults(self):
        return {
            'E_CHECKBOX_Marquee_PixelOffsets': 0,
            'E_CHECKBOX_Marquee_Reverse': 0,
            'E_CHECKBOX_Marquee_WrapX': 0,
            'E_CHECKBOX_Marquee_WrapY': 0,
            'E_NOTEBOOK_Marquee': 'Settings',
            'E_SLIDER_MarqueeXC': 0,
            'E_SLIDER_MarqueeYC': 0,
            'E_SLIDER_Marquee_Band_Size': 4,
            'E_SLIDER_Marquee_ScaleX': 100,
            'E_SLIDER_Marquee_ScaleY': 100,
            'E_SLIDER_Marquee_Skip_Size': 2,
            'E_SLIDER_Marquee_Speed': 3,
            'E_SLIDER_Marquee_Stagger': 0,
            'E_SLIDER_Marquee_Start': 0,
            'E_SLIDER_Marquee_Thickness': 1,
            'T_TEXTCTRL_Fadein': 1.00,
            'T_TEXTCTRL_Fadeout': 1.00
        }


class PicturesEffect(Effect):
    def get_defaults(self):
        return {
            'E_CHECKBOX_Pictures_PixelOffsets': 0,
            'E_CHECKBOX_Pictures_Shimmer': 0,
            'E_CHECKBOX_Pictures_TransparentBlack': 0,
            'E_CHECKBOX_Pictures_WrapX': 0,
            'E_CHOICE_Pictures_Direction': 'none',
            'E_CHOICE_Scaling': 'No Scaling',
            'E_FILEPICKER_Pictures_Filename': None,
            'E_SLIDER_PicturesXC': 0,
            'E_SLIDER_PicturesYC': 0,
            'E_SLIDER_Pictures_EndScale': 100,
            'E_SLIDER_Pictures_StartScale': 100,
            'E_TEXTCTRL_Pictures_FrameRateAdj': 1.0,
            'E_TEXTCTRL_Pictures_Speed': 1.0,
            'E_TEXTCTRL_Pictures_TransparentBlack': 0,
            'T_TEXTCTRL_Fadein': 1.00,
            'T_TEXTCTRL_Fadeout': 1.00
        }


class Sequence:
    def __init__(self, layers=1):
        self.colors = []
        self.palettes = []
        self.effects = []
        self.layers = [[] for _d in range(layers)]
        self.length = 0

    def add_effect(self, layer_index=None, effect=None, start=None, end=None, palette=None):
        if effect not in self.effects:
            self.effects.append(effect)
        effect_index = self.effects.index(effect)

        if palette not in self.palettes:
            self.palettes.append(palette)
        palette_index = self.palettes.index(palette)

        name = type(effect).__name__
        if name[-6:] == "Effect":
            name = name[:-6]

        self.layers[layer_index].append(
            EffectReference(effect_index=effect_index, name=name, start=start, end=end, palette_index=palette_index)
        )

        self.length = max(self.length, end)

    def xml(self):
        tree = ET.parse('template.xsq')
        doc = tree.getroot()

        # ET.dump(doc)

        # update the sequence length
        e = doc.find("./head/sequenceDuration")
        e.text = str(self.length)

        # zap and replace the color palettes
        e = doc.find("./ColorPalettes")
        # https://stackoverflow.com/a/37336234/17887564
        for e_sub in list(e):
            e.remove(e_sub)
        for p in self.palettes:
            e.append(p.xml())

        # zap and replace the effects
        e = doc.find("./EffectDB")
        for e_sub in list(e):
            e.remove(e_sub)
        for f in self.effects:
            e.append(f.xml())

        # zap and replace the effect references
        e = doc.find("./ElementEffects/Element[@type='model']")
        for e_sub in list(e):
            e.remove(e_sub)
        for l in self.layers:
            x_l = ET.Element('EffectLayer')
            e.append(x_l)
            for i, er in enumerate(l):
                x_l.append(er.xml(i))

        ET.indent(doc, ' ', 0)
        ET.dump(doc)
        return doc


class EffectReference:
    def __init__(self, effect_index=None, name=None, start=None, end=None, palette_index=None):
        self.effect_index = effect_index
        self.name = name
        self.start = start
        self.end = end
        self.palette_index = palette_index

    def __repr__(self):
        # return super().__repr__() + f":{self.name}[{self.start}:{self.end}]"
        return str(vars(self))

    def xml(self, id=None):
        x = ET.Element('Effect')
        x.attrib = {
            "ref": str(self.effect_index),
            "name": self.name,
            "id": str(id),
            "startTime": str(int(self.start * 1000)),
            "endTime": str(int(self.end * 1000)),
            "palette": str(self.palette_index)
        }
        return x


class Palette:
    def __init__(self, *colors):
        self.colors = [ *colors ]

    def __repr__(self):
        # return super().__repr__() + f":{self.colors}"
        return str(vars(self))

    def xml(self):
        x = ET.Element('ColorPalette')
        t = []
        for i, c in enumerate(self.colors):
            t.append(f"C_BUTTON_Palette{i+1}={self.colors[i]}")
            t.append(f"C_CHECKBOX_Palette{i+1}=1")
        x.text = ",".join(t)
        return x


def test(argv):

    e = TextEffect(Text='Test Text')
    print(e.xml_text())

    s = Sequence(layers=2)

    blue = Palette("#0000ff")
    red = Palette('#ff0000')
    s.add_effect(0, e, 0, 1, blue)
    s.add_effect(0, e, 1, 2, red)
    print(s.layers)
    print(s.palettes)


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

            sequence = Sequence(layers=2)

            color_palette = Palette('#ff0000' if color == "red" else '#0000ff')

            for team_key in members:
                t0 = sequence.length

                team = teams[team_key]

                e0 = TextEffect(Text=str(team['team_number']), Text_YStart=16)
                e1 = TextEffect(Text=team['nickname'], Text_YStart=-16, FONTPICKER_Text_Font='bold arial 12 windows-1252')

                sequence.add_effect(layer_index=0, effect=e0, start=t0, end=t0 + 5, palette=color_palette)
                sequence.add_effect(layer_index=1, effect=e1, start=t0, end=t0 + 5, palette=color_palette)

            x = sequence.xml()
            # ET.dump(x)
            break


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main(sys.argv[1:])