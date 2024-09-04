import json
import requests

r = requests.get('https://raw.githubusercontent.com/danocmx/node-tf2-static-schema/master/static/items.json')

schema = json.loads(r.text)

skema = {}
for i in schema:
    if i['item_type_name'] == 'CheatDetector':
        continue
    if 'item_slot' not in i:
        i['item_slot'] = i['item_class']
    if i['item_name'] == 'War Paint':
        i['item_slot'] = 'warpaint'
    elif i['item_name'] == 'Unusualifier':
        i['item_slot'] = 'unusualifier'
    if "used_by_classes" in i:
        if len(i['used_by_classes']) > 1:
            classes = 'Multi-Class'
        elif i['used_by_classes'] == []:
            classes = 'None'
        else:
            classes = i['used_by_classes'][0]
    else:
        if 'item_slot' in i:
            classes = 'All-Class'
        else:
            classes = None
    if i['proper_name'] == True:
        name = 'The ' + i['item_name']
    else:
        name = i['item_name']
    skema[str(i['defindex'])] = {'name': name, 'defindex': str(i['defindex']), 'item_slot': i['item_slot'], 'class': classes}

with open(f'itemschema.json', 'w', encoding ='utf8') as json_file:
    json.dump(skema, json_file, ensure_ascii=False)