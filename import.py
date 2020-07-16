#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib, json, csv
import requests
import sys
import os.path

#
# import from scarfage json the latest scarf data.
# save data in CSV format to stdout.
#
# Usage: ./import.py {-n NUM} >> scarfDB.csv
# retrieves NUM latest (default 3000) scarves frolm scarfage.com
#
NUM = '4000' #set to 3000 to get everything. Query requests most recent NUM entries
if len(sys.argv) > 1 and sys.argv[1] == '-n':
    NUM = sys.argv[2]

# format json for print
def get_pretty_print(json_object):
    return json.dumps(json_object, sort_keys=True, indent=4, separators=(',', ': '))

# format image url
def image_url(image_id):
    # print "image_url for "+str(image_id)
    return "https://www.scarfage.com/image/"+str(image_id)+"/full"
    # return "https://d2tx6l6dxpjuj3.cloudfront.net/resize/1900x400/"+str(image_id)

# retrieve scarf image, and save in local folder named 'testimgs'
# skip duplicates...
def save_image_locally(image_id, con):
    filepath='./testimgs/'+str(image_id)+'.jpg'
    if not os.path.isfile(filepath):
        img_data = requests.get(image_url(image_id), verify=False).content
        with open(filepath, 'wb') as handler:
            handler.write(img_data)

# get the scarfage json
scarfjson_url = "/item/search?type=items&page=&limit="+NUM+"&query=&sort=added"
headers = {"Accept": "application/json"}

conn = httplib.HTTPSConnection("www.scarfage.com")
conn.request("GET", scarfjson_url, '', headers)
response = conn.getresponse()
data = json.loads(response.read())['results']
# print get_pretty_print(data)

output = csv.writer(sys.stdout)
output.writerow([ 'Name', 'Description', 'Tags', 'Added', 'Image0', 'Image1', 'ID' ]) # header row

for scarf in data:
    # get single scarf record (with description)
    scarfjson_url = "/item/" + str(scarf['uid'])
    conn.request("GET", scarfjson_url, '', headers)
    response = conn.getresponse()
    scarfdata = json.loads(response.read())

    scarfdata['image1'] = ""
    scarfdata['image0'] = ""
    for i in range(len(scarfdata['images'])):
        # uncomment next line to pull EVERY new image to your local folder
        # print "retrieving image: "+str(scarf['images'][i])
        save_image_locally(scarf['images'][i], conn)
        scarfdata['image'+str(i)] = image_url(scarfdata['images'][i])

    # print get_pretty_print(scarfdata)
    output.writerow([
        scarfdata['name'].encode('utf-8'),
        scarfdata['body'].encode('utf-8'),
        scarfdata['tags'],
        scarfdata['added'],
        scarfdata['image0'],
        scarfdata['image1'],
        scarfdata['uid']
    ])

conn.close()
