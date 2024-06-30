import requests
import json
import math
from time import strftime, localtime
import time
import gspread
import functools
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get MP API Key from .env file
MPKEY = os.getenv('MPKEY')


def Reconnect():
    global scope
    global gc
    global sh
    global main
    global msh
    global botbulk
    global unfiltered
    global ids
    print('reconnecting')
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        gc = gspread.service_account(filename='service_account.json')

        #Name of the sheet that contains all other worksheets
        #Can also use gc.open_by_url(URL) if you have multiple
        # of the same name and don't want to change for whatever reason
        sh = gc.open('Master Spreadsheet')
        #Main worksheet name, uses name change if needed
        main = sh.worksheet("TF2")
        #Similarly but for max heads
        msh = sh.worksheet("MSH")
        #Similarly but for bot bulk
        botbulk = sh.worksheet("Bot Bulk")
        #Move all unfound items here
        unfiltered = sh.worksheet("Unrecorded Sales")
        #list of all ids
        ids = sh.worksheet("IDs")
    except Exception as e:
        print('Reconnection failed! Trying again...')
        print(e)
        time.sleep(10)
        return Reconnect()
    return scope, gc, sh, main, msh, botbulk, unfiltered, ids


def rate_limit(max_calls, timespan):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            if not hasattr(wrapper, 'call_times'):
                wrapper.call_times = []

            wrapper.call_times = [t for t in wrapper.call_times if current_time - t <= timespan]

            if len(wrapper.call_times) < max_calls:
                wrapper.call_times.append(current_time)
                return func(*args, **kwargs)
            else:
                time_to_wait = max(wrapper.call_times) + timespan - current_time
                if time_to_wait > 0:
                    time.sleep(time_to_wait)
                return wrapper(*args, **kwargs)

        return wrapper
    return decorator


@rate_limit(max_calls=50, timespan=60)  # 50 per minute just to be safe since sheets forces a full logout on 429
def limiter(function):
    return function

def mpconvert(credit):
    if credit < 10:
        return math.floor(credit * 0.9)*0.01
    else:
        return int(round(credit * 0.9, 0))*0.01


def dateconvert(time):
    return strftime('%Y-%m-%d', localtime(time))


def namefix(name, skulist):
    #Strange filter exception:
    if 'Uncraftable Strange Filter:' in name:
        name = name.split('Uncraftable')[1]
        name = 'Non-Craftable' + name
        return name
    
    # We match marketplace naming scheme to follow spreadsheet for easier matching.
    # KILLSTREAK x QUALITY HANDLING, should be compatible with ks hats afaik
    qlt = skulist.split(';')[1]
    sku = skulist.split(';')[0]

    # Remove killstreaker in the end of item name
    if 'Professional ' in name or 'Specialized ' in name:
        temp = name.rfind('(')
        name = name[:temp].strip()

    qualities = ['Vintage ', 'Genuine ', "Collector's ", "Normal ", 'Strange ']  # Think about strange double qualities later
    effects = ['Isotope ', 'Hot ', 'Energy Orb ', 'Cool ']
    aussieslots = ['primary', 'secondary', 'melee', 'warpaint']
    # Test example : 'Professional Australium Black Box'
    if 'Professional ' in name:
        temp = name.split('Professional ')  # '' + 'Australium BLack Box'
        name = temp[0] + 'Professional Killstreak ' + temp[1]  # Professional Killstreak Australium Black Box
    elif 'Specialized ' in name:
        temp = name.split('Specialized ')
        name = temp[0] + 'Specialized Killstreak ' + temp[1]
    elif 'Basic Killstreak ' in name:
        temp = name.split('Basic ')
        name = temp[0] + temp[1]  # Killstreak [ITEM NAME]

    if 'Australium ' in name and skema[sku]['item_slot'] in aussieslots:
        name = 'Strange ' + name

    if skema[sku]['item_slot'] in aussieslots and sku != '1181':  # hot hand exception
        for effect in effects:
            if effect in name:
                temp = name.split(effect)
                name = effect + temp[0] + temp[1]
        if '★' in name:
            temp = name.split('★')
            name = temp[0] + temp[1]

        if 'Festivized ' in name:
            temp = name.split('Festivized ')
            name = temp[0] + temp[1]

    for quality in qualities:
        if quality == 'Vintage ' and ('Vintage Tyrolean' in name or 'Vintage Merryweather' in name):
            continue
        if quality in name:
            temp = name.split(quality)
            name = quality + temp[0] + temp[1]  # 'Strange' + 'Professional' + 'Kritzkrieg'

    # Effect handling
    if 'Peace Sign' in name or 'TF Logo' in name:
        if 'Strange' in name:
            name = 'Strange Circling ' + name.split('Strange ')[1]
        else:
            name = 'Circling ' + name

    if 'Uncraftable' in name:
        temp = name.split('Uncraftable ')
        name = 'Non-Craftable ' + temp[0] + temp[1]

    if 'Paint: ' in name:
        temp = name.split('Paint: ')
        name = temp[0] + temp[1]

    if 'Unusualifier' in name:
        name = 'Non-Craftable Unusual ' + name

    if skema[sku]['item_slot'] == 'tool':
        if 'Kit' in name and 'Fabricator' not in name:
            name = 'Non-Craftable ' + name

    if 'Strange ' in name and qlt == '6': # Strange Unique
        name = 'Strange Unique ' + name.split('Strange ')[1]

    if skulist == f"{sku};6":
        name = skema[sku]['name']

    if name[0] == "'":
        name = name[:]

    if name == "Horseless Headless Horsemann's Headtaker":
        name = "Unusual Horseless Headless Horsemann's Headtaker"

    return name


def requestMpData(before, num):
    try:
        r = requests.get('https://marketplace.tf/api/Seller/GetSales/v2', params={'key': {MPKEY}, 'start_before': before, 'num': 100}, headers={'User-Agent': 'User-Agent'})
        if r.status_code == 200:
            result = json.loads(r.text)
            if result['success'] is True:
                return json.loads(r.text)
            else:
                return requestMpData(before, num)
        else:
            print('MP Data fail!')
            print(r)
            time.sleep(10)  # something went wrong. wait a bit
            return requestMpData(before, num)
    except Exception as e:
        print('MP Data fail 2!')
        print(e)
        time.sleep(1)
        return requestMpData(before, num)


def qualityFinder(item):  # use item section of the sale as input
    qualitydict = {'6': 'Unique',
                   '5': 'Unusual',
                   '11': 'Strange',
                   '14': "Collector's",
                   '13': "Haunted",
                   '3': "Vintage",
                   "1": "Genuine",
                   "9": "Self-Made",
                   "0": "Normal",
                   "15": "Decorated Weapon"}
    sku = item['sku'].split(';')[1]
    quality = qualitydict[sku]
    if '(Battle Scarred)' in item['name'] or '(Well-Worn)' in item['name'] or '(Field-Tested)' in item['name'] or '(Minimal Wear)' in item['name'] or '(Factory New)' in item['name']:
        if '★' in item['name']:
            quality = 'Unusual Decorated Weapon'
        else:
            quality = 'Decorated Weapon'

    if 'strange' in item['sku']:  # elevated qualities marked with ;strange
        quality = 'Strange ' + quality

    elif sku == '11' and quality != 'Strange':  # in theory should only apply to skins
        quality = 'Strange ' + quality

    return quality


skema = json.loads(open('itemschema.json', encoding="utf8").read())

Reconnect()
unsold = {}
finalsaletime = 0
lastsearch = os.getenv('LASTSEARCH')

try:
    while True:
        looptime = time.time()
        totalupdates = 0
        unfilteredBatchUpdate = []
        maxBatchUpdate = []
        fullBucket = []

        while True:
            try:
                maxLast = len(limiter(msh.col_values(6)))  # Get last filled max item
                break
            except Exception as e:
                if isinstance(e, gspread.exceptions.APIError):
                    if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                        time.sleep(5)
                        Reconnect()
                    else:
                        raise(e)
                else:
                    raise(e)

        lastcheck = int(time.time())
        incomplete = 1
        mpdata = {'sales': []}
        firstloop = 1
        while incomplete == 1:
            temp = limiter(requestMpData(lastcheck, 100))
            for sale in temp['sales']:
                if sale['id'] == lastsearch or sale['time'] < finalsaletime:
                    mpdata['sales'].append(sale)
                    incomplete = 0
                    break
                if firstloop == 0:
                    firstloop = 1
                    continue  # skip this one as it is the same as before
                mpdata['sales'].append(sale)

            if incomplete == 1:
                lastcheck = mpdata['sales'][-1]['time']  # setup next loop in case more than 100 sales happen in 1 hour
                firstloop = 0

        mpdata['sales'].reverse()

        for sale in mpdata['sales']:

            if sale['paid'] is False:  # Just in case it was already sold
                unsold[sale['id']] = sale
                print(f"Marking {sale['id']} as pending!")
                continue

            while True:
                try:
                    temp = limiter(ids.find(sale['id']))
                    break
                except Exception as e:
                    if isinstance(e, gspread.exceptions.APIError):
                        if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                            time.sleep(5)
                            Reconnect()
                        else:
                            raise(e)
                    else:
                        raise(e)

            if temp is not None:
                continue  # sale was already listed. just a sanity check in case the above initial doesn't cover

            if sale['id'] in unsold and sale['paid'] is True:
                print(f"Marking {sale['id']} as no longer pending!")
                del unsold[sale['id']]  # Mark it as sold aka don't need to check it again later

            print(f"Processing Sale ID: {sale['id']}")

            for item in sale['items']:
                gametest = item['sku'].split(';')[0]
                if gametest == 'd2' or gametest == 'steam':
                    continue

                totalupdates = totalupdates + 1

                if item['sku'].split(';')[0] == '-100':
                    sku = skema['263']
                    item['sku'] = '263;6'
                elif item['sku'].split(';')[0] in skema:
                    sku = skema[item['sku'].split(';')[0]]
                else:
                    sku = {"name": "UNKNOWN!", "defindex": "UNKNOWN!", "item_slot": "UNKNOWN!", "class": "UNKNOWN!"}
                name = namefix(item['name'], item['sku'])
                if ('(Battle Scarred)' in name or '(Well-Worn)' in name or '(Field-Tested)' in name or '(Minimal Wear)' in name or '(Factory New)' in name) and ' War Paint' not in name:
                    slot = 'Skin'  # dumb easy fix for skins
                else:
                    slot = sku['item_slot']
                quality = qualityFinder(item)
                print(f'Updating Item: {name}')
                if name != "Max's Severed Head":
                    found = 0
                    while True:
                        try:
                            search = limiter(main.findall(name))
                            break
                        except Exception as e:
                            if isinstance(e, gspread.exceptions.APIError):
                                if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                                    time.sleep(5)
                                    Reconnect()
                                else:
                                    raise(e)
                            else:
                                raise(e)

                    for entry in search:
                        while True:
                            try:
                                data = limiter(main.get(f"G{entry.row}"))  # check date sold cell
                                break
                            except Exception as e:
                                if isinstance(e, gspread.exceptions.APIError):
                                    if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                                        time.sleep(5)
                                        Reconnect()
                                    else:
                                        raise(e)
                                else:
                                    raise(e)
                        if data == [[]]:  # empty cell aka unsold and we can mark as sold
                            found = main
                            row = entry.row
                            break
                        else:  # item was already sold, move onto next
                            continue

                    if found == 0:  # no valid items, check the botbulk sheet
                        while True:
                            try:
                                search = limiter(botbulk.findall(name))
                                break
                            except Exception as e:
                                if isinstance(e, gspread.exceptions.APIError):
                                    if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                                        time.sleep(5)
                                        Reconnect()
                                    else:
                                        raise(e)
                                else:
                                    raise(e)
                        for entry in search:
                            while True:
                                try:
                                    data = limiter(botbulk.get(f"G{entry.row}"))
                                    break
                                except Exception as e:
                                    if isinstance(e, gspread.exceptions.APIError):
                                        if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                                            time.sleep(5)
                                            Reconnect()
                                        else:
                                            raise(e)
                                    else:
                                        raise(e)
                            if data == [[]]:
                                found = main
                                row = entry.row
                                break
                            else:
                                continue

                    if found != 0:
                        batchUpdate = []
                        batchUpdate.append({'range': f"A{row}:C{row}", "values": [[slot, sku['class'], quality]]})
                        batchUpdate.append({'range': f"G{row}:K{row}", "values": [[dateconvert(sale['time']), mpconvert(item['price']), f"=G{row}-E{row}", f"=H{row}-F{row}", f"=J{row}/F{row}"]]})
                        batchUpdate.append({'range': f"L{row}", "values": [[sale['id']]]})
                        while True:
                            try:
                                limiter(found.batch_update(batchUpdate, value_input_option='USER_ENTERED'))
                                break
                            except Exception as e:
                                if isinstance(e, gspread.exceptions.APIError):
                                    if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                                        time.sleep(5)
                                        Reconnect()
                                    else:
                                        raise(e)
                                else:
                                    raise(e)
                    else:
                        # Item not found so we move it to the unfiltered row
                        unfilteredBatchUpdate.append([slot, sku['class'], quality, name, dateconvert(sale['time']), mpconvert(item['price']), sale['id']])
                        fullBucket.append([slot, sku['class'], quality, name, dateconvert(sale['time']), mpconvert(item['price']), sale['id']])
                else:  # Max's head
                    maxLast = maxLast + 1
                    maxBatchUpdate = []
                    maxBatchUpdate.append({'range': f"C{maxLast}:G{maxLast}", "values": [[dateconvert(sale['time']), mpconvert(item['price']), f"=C{maxLast}-A{maxLast}", f"=D{maxLast}-B{maxLast}", f"=F{maxLast}/B{maxLast}"]]})
                    maxBatchUpdate.append({'range': f"H{maxLast}", "values": [[sale['id']]]})
                    while True:
                        try:
                            limiter(msh.batch_update(maxBatchUpdate, value_input_option='USER_ENTERED'))
                            break
                        except Exception as e:
                            if isinstance(e, gspread.exceptions.APIError):
                                if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                                    time.sleep(5)
                                    Reconnect()
                                else:
                                    raise(e)
                            else:
                                raise(e)

            while True:
                try:
                    limiter(ids.append_row([sale['id']]))  # Mark id as sold
                    break
                except Exception as e:
                    if isinstance(e, gspread.exceptions.APIError):
                        if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                            time.sleep(5)
                            Reconnect()
                        else:
                            raise(e)
                    else:
                        raise(e)

            # if initial == 1:
                # break  # no need to search any more
            # else:

        if len(unsold) > 0:
            delgroup = []
            for ID in unsold:
                mpdata = requestMpData(int(unsold[ID]['time']), 10)
                undelete = 1
                for sale in mpdata['sales']:
                    if sale['id'] == ID and sale['paid'] is True:
                        print(f"Updating Pending ID: {sale['id']}")
                        for item in sale['items']:
                            gametest = item['sku'].split(';')[0]
                            if gametest == 'd2' or gametest == 'steam':
                                continue
                            
                            if item['sku'].split(';')[0] == '-100':
                                sku = skema['263']
                                item['sku'] = '263;6'
                            elif item['sku'].split(';')[0] in skema:
                                sku = skema[item['sku'].split(';')[0]]
                            else:
                                sku = {"name": "UNKNOWN!", "defindex": "UNKNOWN!", "item_slot": "UNKNOWN!", "class": "UNKNOWN!"}
                            name = namefix(item['name'], item['sku'])
                            if ('(Battle Scarred)' in name or '(Well-Worn)' in name or '(Field-Tested)' in name or '(Minimal Wear)' in name or '(Factory New)' in name) and ' War Paint' not in name:
                                slot = 'Skin'  # dumb easy fix for skins
                            else:
                                slot = sku['item_slot']
                            quality = qualityFinder(item)
                            print(f'Updating Pending Item: {name}')
                            if name != "Max's Severed Head":
                                found = 0
                                while True:
                                    try:
                                        search = limiter(main.findall(name))
                                        break
                                    except Exception as e:
                                        if isinstance(e, gspread.exceptions.APIError):
                                            if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                                                time.sleep(5)
                                                Reconnect()
                                            else:
                                                raise(e)
                                        else:
                                            raise(e)

                                for entry in search:
                                    while True:
                                        try:
                                            data = limiter(main.get(f"G{entry.row}"))  # check date sold cell
                                            break
                                        except Exception as e:
                                            if isinstance(e, gspread.exceptions.APIError):
                                                if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                                                    time.sleep(5)
                                                    Reconnect()
                                                else:
                                                    raise(e)
                                            else:
                                                raise(e)

                                    if data == [[]]:  # empty cell aka unsold and we can mark as sold
                                        found = main
                                        row = entry.row
                                        break
                                    else:  # item was already sold, move onto next
                                        continue

                                if found == 0:  # no valid items, check the botbulk sheet
                                    while True:
                                        try:
                                            search = limiter(botbulk.findall(name))
                                            break
                                        except Exception as e:
                                            if isinstance(e, gspread.exceptions.APIError):
                                                if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                                                    time.sleep(5)
                                                    Reconnect()
                                                else:
                                                    raise(e)
                                            else:
                                                raise(e)

                                    for entry in search:
                                        while True:
                                            try:
                                                data = limiter(botbulk.get(f"G{entry.row}"))
                                                break
                                            except Exception as e:
                                                if isinstance(e, gspread.exceptions.APIError):
                                                    if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                                                        time.sleep(5)
                                                        Reconnect()
                                                    else:
                                                        raise(e)
                                                else:
                                                    raise(e)

                                        if data == [[]]:
                                            found = main
                                            row = entry.row
                                            break
                                        else:
                                            continue

                                if found != 0:
                                    batchUpdate = []
                                    batchUpdate.append({'range': f"A{row}:C{row}", "values": [[slot, sku['class'], quality]]})
                                    batchUpdate.append({'range': f"G{row}:K{row}", "values": [[dateconvert(sale['time']), mpconvert(item['price']), f"=G{row}-E{row}", f"=H{row}-F{row}", f"=J{row}/F{row}"]]})
                                    batchUpdate.append({'range': f"L{row}", "values": [[sale['id']]]})
                                    while True:
                                        try:
                                            limiter(found.batch_update(batchUpdate, value_input_option='USER_ENTERED'))
                                            break
                                        except Exception as e:
                                            if isinstance(e, gspread.exceptions.APIError):
                                                if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                                                    time.sleep(5)
                                                    Reconnect()
                                                else:
                                                    raise(e)
                                            else:
                                                raise(e)
                                else:
                                    # Item not found so we move it to the unfiltered row
                                    unfilteredBatchUpdate.append([slot, sku['class'], quality, name, dateconvert(sale['time']), mpconvert(item['price']), sale['id']])
                                    fullBucket.append([slot, sku['class'], quality, name, dateconvert(sale['time']), mpconvert(item['price']), sale['id']])
                            else:  # Max's head
                                maxLast = maxLast + 1
                                maxBatchUpdate = []
                                maxBatchUpdate.append({'range': f"C{maxLast}:G{maxLast}", "values": [[dateconvert(sale['time']), mpconvert(item['price']), f"=C{maxLast}-A{maxLast}", f"=D{maxLast}-B{maxLast}", f"=F{maxLast}/B{maxLast}"]]})
                                maxBatchUpdate.append({'range': f"H{maxLast}", "values": [[sale['id']]]})
                                while True:
                                    try:
                                        limiter(msh.batch_update(maxBatchUpdate, value_input_option='USER_ENTERED'))
                                        break
                                    except Exception as e:
                                        if isinstance(e, gspread.exceptions.APIError):
                                            if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                                                time.sleep(5)
                                                Reconnect()
                                            else:
                                                raise(e)
                                        else:
                                            raise(e)

                        while True:
                            try:
                                limiter(ids.append_row([sale['id']]))  # Mark id as sold
                                break
                            except Exception as e:
                                if isinstance(e, gspread.exceptions.APIError):
                                    if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                                        time.sleep(5)
                                        Reconnect()
                                    else:
                                        raise(e)
                                else:
                                    raise(e)
                        break
                    elif sale['id'] == ID and sale['paid'] is False:
                        undelete = 0
                        break
                if undelete == 1:
                    delgroup.append(ID)
            for i in delgroup:
                totalupdates = totalupdates + 1
                print(f"Marking {i} as no longer pending!")
                del unsold[i]  # Mark as sold

        if len(unfilteredBatchUpdate) > 0:
            while True:
                try:
                    print(f'Attempting to update {len(unfilteredBatchUpdate)} unfiltered items')
                    limiter(unfiltered.append_rows(unfilteredBatchUpdate, value_input_option='USER_ENTERED'))
                    break
                except Exception as e:
                    if isinstance(e, gspread.exceptions.APIError):
                        if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                            time.sleep(5)
                            Reconnect()
                        else:
                            raise(e)
                    else:
                        raise(e)

        if len(maxBatchUpdate) > 0:
            while True:
                try:
                    print(f'Attempting to update {len(maxBatchUpdate)} Max Heads')
                    limiter(msh.batch_update(maxBatchUpdate, value_input_option='USER_ENTERED'))
                    break
                except Exception as e:
                    if isinstance(e, gspread.exceptions.APIError):
                        if e.args[0]['code'] >= 500 or e.args[0]['code'] == 429:
                            time.sleep(5)
                            Reconnect()
                        else:
                            raise(e)
                    else:
                        raise(e)

        lastsearch = mpdata['sales'][-1]['id']
        finalsaletime = mpdata['sales'][-1]['time']

        print('Updated this many items:', totalupdates)
        print('Process completed in:', time.time() - looptime)
        print()

        if time.time() - looptime < 60*60:  # loop every 60 minutes
            print(f"Waiting {round(time.time() - looptime, 0)} until next sales fetch")
            time.sleep(60*60 - (time.time() - looptime))

except Exception as e:
    fail = str(e)
    errors = {'failpoint': e, 'sales': mpdata, 'unfilteredBatch': unfilteredBatchUpdate, 'maxBatchUpdate': maxBatchUpdate}
    with open('error.json', 'w', encoding ='utf8') as json_file:
        json.dump(errors, json_file, ensure_ascii=False)

    print(fail)
    print("Error happened!")
    input("Press enter to exit")

print("Something wrong happened, you shouldn't be seeing this!")