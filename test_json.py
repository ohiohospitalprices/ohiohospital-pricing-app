import requests
import json

url = 'https://www.ohiohealth.com/siteassets/patients-and-visitors/preparing-for-your-visit/out-of-pocket-estimates/384105653_berger-hospital_standardcharges.json'
resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
data = json.loads(resp.content.decode('utf-8-sig'))
sci = data.get('standard_charge_information', [])
print(f'standard_charge_information type: {type(sci)}')
if isinstance(sci, list):
    print(f'Length: {len(sci)}')
    if len(sci) > 0:
        print('First item type:', type(sci[0]))
        if isinstance(sci[0], dict):
            print('First item keys:', list(sci[0].keys())[:20])
