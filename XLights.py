import argparse
import copy
import json
import logging
import re
import sys

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element


class Palette:
    def __init__(self, *, xml_text=None, colors=[]):
        # zero based
        self.checked = set()
        self.colors = {}

        if xml_text is not None:
            for nvpair in xml_text.split(","):
                k, v = nvpair.split('=', 1)
                m = re.match(r'^C_BUTTON_Palette(\d+)$', k)
                if m:
                    self.colors[int(m.group(1))-1] = v
                    continue

                m = re.match(r'^C_CHECKBOX_Palette(\d+)$', k)
                if m:
                    if v == '1':
                        self.checked.add(int(m.group(1))-1)
                    elif v == '0':
                        pass
                    else:
                        logging.error("got funny value %s in '%s=%s'", v, k, v)
                    continue

                logging.error("don't recognize '%s=%s'", k, v)
        else:
            for i, c in enumerate(colors):
                self.colors[i] = c
                self.checked.add(i)

    def __repr__(self):
        # return super().__repr__() + f":{self.colors}"
        return str(vars(self))

    def xml(self):
        x = ET.Element('ColorPalette')
        t = []
        for k, v in self.colors.items():
            t.append(f"C_BUTTON_Palette{k+1}={v}")
        for i in self.checked:
            t.append(f"C_CHECKBOX_Palette{i+1}=1")
        x.text = ",".join(t)
        return x


class Effect:
    def __init__(self, *, xml_text=None, **kwargs):
        super().__setattr__('_initialized', False)
        self.defaults = self.get_defaults()
        self.attribute_names = list(self.defaults.keys())
        self.set_attr_enabled = True
        if xml_text is not None:
            self._make_props_dict_from_xml_text(xml_text)
        else:
            self._make_props_dict_from_kwargs(**kwargs)
        self._initialized = True

    def _make_props_dict_from_kwargs(self, **kwargs):
        self.props = self.defaults.copy()
        for k, v in kwargs.items():
            self.set_prop(key=k, value=v)

    def _make_props_dict_from_xml_text(self, xml_text):
        self.props = {}
        for nv_pair in xml_text.split(","):
            k, v = nv_pair.split('=', 1)
            v = v.replace('&comma;', ',')
            self.props[k] = v

    def __setattr__(self, key, value):
        if not getattr(self, '_initialized', False):
            super().__setattr__(key, value)
            return
        key1 = self._lookup_key(key)
        print(f"{key} -> {key1}")
        if key1 is None:
            super().__setattr__(key, value)
        else:
            self.set_prop(key=key1, value=value)

    def __getattr__(self, key):
        if not getattr(self, '_initialized', False):
            return super().__getattr__(key)
        key = self._lookup_key(key)
        return self.props.get(key)

    def _lookup_key(self, key):
        if key in self.attribute_names:
            return key
        if key in self.props.keys():
            return key
        u_key = key.upper()
        for k1 in self.attribute_names:
            if k1.upper().endswith(f"_{u_key}"):
                return k1
        for k1 in self.props.keys():
            if k1.upper().endswith(f"_{u_key}"):
                return k1
        logging.error("what is option %s", key)
        return None

    def set_prop(self, *, force=False, key=None, value=None):
        if force:
            self.props[key] = value
            return

        key = self._lookup_key(key)
        self.props[key] = value

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
        # x.text = "B_CHOICE_BufferStyle=Per Model Default," + ",".join(t)
        x.text = ",".join(t)
        return x


class TextEffect(Effect):
    defaults = {
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

    def get_defaults(self):
        return self.defaults


class MarqueeEffect(Effect):
    defaults = {
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

    def get_defaults(self):
        return self.defaults

class PicturesEffect(Effect):
    defaults = {
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

    def get_defaults(self):
        return self.defaults


class EffectReference:
    def __init__(self, *, sequence: 'Sequence' = None, xml_element: ET.Element = None, effect: Effect = None, name=None, start=None, end=None, palette: Palette = None):
        assert sequence is not None
        self.sequence = sequence
        if xml_element is None:
            self.xml_element = ET.Element('Effect')
            self.effect = effect
            self.name = name
            self.start = start
            self.end = end
            self.palette = palette
        else:
            # TODO need to handle id and selected
            self.xml_element = xml_element
            self.name = xml_element.attrib.get('name')
            effects_index = int(xml_element.attrib.get('ref'))
            effect_maybe = sequence.effects[effects_index]
            if type(effect_maybe) == str:
                if self.name == 'Text':
                    self.effect = TextEffect(xml_text=effect_maybe)
                elif self.name == 'Pictures':
                    self.effect = PicturesEffect(xml_text=effect_maybe)
                elif self.name == 'Marquee':
                    self.effect = MarqueeEffect(xml_text=effect_maybe)
                else:
                    self.effect = Effect(xml_text=effect_maybe)
                sequence.effects[effects_index] = self.effect
            else:
                self.effect = effect_maybe
            self.start = int(xml_element.attrib.get('startTime'))
            self.end = int(xml_element.attrib.get('endTime'))
            self.palette = sequence.palettes[int(xml_element.attrib.get('palette'))]

    def __repr__(self):
        # return super().__repr__() + f":{self.name}[{self.start}:{self.end}]"
        return str(vars(self))

    def xml(self):
        effect_index = self.sequence.effects.index(self.effect)
        palette_index = self.sequence.palettes.index(self.palette)
        self.xml_element.attrib.update({
            "ref": str(effect_index),
            "name": self.name,
            "startTime": str(int(self.start)),
            "endTime": str(int(self.end)),
            "palette": str(palette_index)
        })
        return self.xml_element


class Model:
    def __init__(self, *, sequence: 'Sequence' = None, xml_element: ET.Element = None, name: str = None):
        self.sequence = sequence
        self.layers = []
        self.name = name
        if xml_element is not None:
            self.xml_element = xml_element
            self.name = self.xml_element.attrib.get('name')

            effects_layers = self.xml_element.findall('./EffectLayer')
            logging.info("model %s has %d layers", self.name, len(effects_layers))
            to_remove = []
            for i, layer_xml in enumerate(effects_layers):
                logging.info("processing layer %d of model %s", i, self.name)
                ET.dump(layer_xml)
                layer = []
                self.layers.append(layer)
                for effect_ref_xml in layer_xml:
                    assert effect_ref_xml.tag == 'Effect'
                    effect_ref = EffectReference(sequence=self.sequence, xml_element=effect_ref_xml)
                    layer.append(effect_ref)
                to_remove.append(layer_xml)
            for layer_xml in to_remove:
                self.xml_element.remove(layer_xml)
        else:
            self.xml_element = Element('Element', { 'name': name, 'type': 'model'})

        assert self.xml_element.attrib.get("name") is not None
        assert self.xml_element.attrib.get("type") == "model"

    def xml(self):
        rv = copy.deepcopy(self.xml_element)
        print('**** start')
        print(json.dumps(self.layers, indent=1, default=lambda x: str(x)))
        ET.dump(rv)
        for i, layer in enumerate(self.layers):
            layer_xml_element = Element('EffectLayer')
            rv.append(layer_xml_element)
            for effectReference in layer:
                layer_xml_element.append(effectReference.xml())
            print(f"** after adding layer {i}")
            print(json.dumps(self.layers, indent=1, default=lambda x: str(x)))
            ET.dump(rv)
        print('**** end')
        print(json.dumps(self.layers, indent=1, default=lambda x: str(x)))
        ET.dump(rv)
        return rv


class DisplayElement:
    def __init__(self, *, xml_element = None, name = None):
        if xml_element is not None:
            self.xml_element = xml_element
        else:
            self.xml_element = ET.Element('Element', {
                'name': name,
                'type': 'model',
                'collapsed': '0',
                'visible': '1',
            })

    def xml(self):
        return self.xml_element

class Sequence:
    def __init__(self):
        self.palettes = []
        self.effects = []
        self.models = {}
        self.display_elements = {}

        self.xml_doc = None

        self.length = 0

    def load(self, *, file: str = None):
        tree = ET.parse(file)
        self.xml_doc = tree.getroot()

        self.palettes = []
        e = self.xml_doc.find("./ColorPalettes")
        for e1 in list(e):
            v = Palette(xml_text=e1.text)
            self.palettes.append(v)
            e.remove(e1)

        self.effects = []
        e = self.xml_doc.find("./EffectDB")
        for e1 in list(e):
            self.effects.append(e1.text)
            e.remove(e1)

        self.display_elements = {}
        e = self.xml_doc.find("./DisplayElements")
        for e1 in list(e):
            self.display_elements[e1.attrib.get('name')] = DisplayElement(xml_element=e1)
            e.remove(e1)

        self.models = {}
        e = self.xml_doc.find("./ElementEffects")
        for e1 in list(e):
            if e1.attrib.get('type') == 'model':
                model = Model(sequence=self, xml_element=e1)
                self.models[model.name] = model
                e.remove(e1)

        for i in range(len(self.effects)):
            if type(self.effects[i]) == str:
                self.effects[i] = Effect(xml_text=self.effects[i])


    def add_effect(self, *, model_name=None, layer_index=None, effect=None, start=None, end=None, palette=None):
        if effect not in self.effects:
            self.effects.append(effect)

        if palette not in self.palettes:
            self.palettes.append(palette)

        name = type(effect).__name__
        if name[-6:] == "Effect":
            name = name[:-6]

        model = self.models.get(model_name)
        if model is None:
            model = Model(sequence=self, name=model_name)
            self.models[model_name] = model

        # layer_index is one based!
        while len(model.layers) < layer_index:
            model.layers.append([])      # get enough layers
        layer = model.layers[layer_index-1]

        layer.append(
            EffectReference(sequence=self, effect=effect, name=name, start=start, end=end, palette=palette)
        )

        display_element = self.display_elements.get(model_name)
        if display_element is None:
            display_element = DisplayElement(name=model_name)
            self.display_elements[model_name] = display_element


    def xml_tree(self) -> ET.ElementTree:
        rv = copy.deepcopy(self.xml_doc)

        # update the sequence length
        e = rv.find("./head/sequenceDuration")
        e.text = str(self.length)

        # add the color palettes
        e = rv.find("./ColorPalettes")
        for p in self.palettes:
            e.append(p.xml())

        # add the effects into the document
        e = rv.find("./EffectDB")
        for f in self.effects:
            e.append(f.xml())

        # add the display elements into the document
        e = rv.find("./DisplayElements")
        for f in self.display_elements.values():
            e.append(f.xml())

        # add the models back into the document
        e = rv.find("./ElementEffects")
        for f in self.models.values():
            e.append(f.xml())

        ET.indent(rv, ' ', 0)
        tree = ET.ElementTree(rv)
        return tree


def main(argv):
    sequence = Sequence()
    sequence.load(file="py_template.xsq")

    effect = TextEffect(Text='3620')
    palette = Palette(colors=('#FF0000', '#00FF00'))
    print(f'effect.text = {effect.text}')
    print(f'effect.xxx = {effect.xxx}')
    effect.text = 'xxxxx'
    print(f'effect.text = {effect.text}')
    sequence.add_effect(model_name="Matrix", layer_index=1, effect=effect, palette=palette, start=1000, end=9000)

    sequence.add_effect(model_name="surprise", layer_index=1, effect=effect, palette=palette, start=1000, end=9000)

    sequence.length = 10.0
    xml_tree = sequence.xml_tree()
    ET.dump(xml_tree)
    # xml_tree.write('xlights_test.xsq')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main(sys.argv[1:])