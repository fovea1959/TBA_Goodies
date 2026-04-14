import xml.etree.ElementTree as ET

from string import Template

def xml(template_file='template_robocart.xsq', model='Half Screens'):
    tree = ET.parse(template_file)
    doc = tree.getroot()

    ET.dump(doc)

    sub_values = {
        'p1': 1111,
        'p2': 2222,
        'alliance': 'RED',
    }

    effectDb = []
    effectDbNodes = doc.find("./EffectDB")
    for effectDbNode in list(effectDbNodes):
        ET.dump(effectDbNode)
        effect_text = effectDbNode.text
        template = Template(effect_text)
        effect_text = template.substitute(sub_values)
        values = {}
        for nvpair in effect_text.split(","):
            k, v = nvpair.split('=', 1)
            values[k] = v
        effectDbNode.text = effect_text
        print(values)
    #ET.indent(doc, ' ', 0)
    # ET.dump(doc)
    #tree = ET.ElementTree(doc)
    return tree

if __name__ == '__main__':
    xml('Test Template.xsq')
