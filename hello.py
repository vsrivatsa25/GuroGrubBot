import requests
import random
from bs4 import BeautifulSoup
import re
from langdetect import detect
import os
import json
from cloudant import Cloudant
from datetime import datetime,date
import time
import tweet


db_name = 'mydb'
client = None
db = None

if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    #print('Found VCAP_SERVICES')
    if 'cloudantNoSQLDB' in vcap:
        creds = vcap['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)
elif "CLOUDANT_URL" in os.environ:
    client = Cloudant(os.environ['CLOUDANT_USERNAME'], os.environ['CLOUDANT_PASSWORD'], url=os.environ['CLOUDANT_URL'], connect=True)
    db = client.create_database(db_name, throw_on_exists=False)
elif os.path.isfile('vcap-local.json'):
    with open('vcap-local.json') as f:
        vcap = json.load(f)
        #print('Found local VCAP_SERVICES')
        creds = vcap['services']['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)


def number_gen():
    return random.randint(1,10**7)

def recheck(lst):
    i=0
    while i<len(lst):
        if lst[i]=="" or re.match(".*verse \d: ",lst[i].lower()) or re.match(".+intro:.+",lst[i].lower()) or re.match(".+chorus.+",lst[i].lower()) or re.match(".+hook.+",lst[i].lower()) or re.match(".+solo.+",lst[i].lower())or re.match(".+bridge:.+",lst[i].lower()) or re.match(".*Lyrics for this song.+",lst[i].lower()):
            lst.remove(lst[i])
        else:
            temp = list(lst[i])
            if len(temp)>150 or len(temp)<10:
                lst.remove(lst[i])
            else:
                i+=1
    return lst

def song_title(ftitle):
    title = re.match("(.+) Lyrics | Genius Lyrics",ftitle)
    return title.groups()[0]

headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36"}
if __name__ == '__main__':
    var=0
    while True:
        if var==0:
            start=time.time()
        var=1
        number = number_gen()
        #url = "https://genius.com/songs/3524045"
        url = "https://genius.com/songs/"+str(number)
        #print(url)
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        lyrics = soup.find("div", {"class": "lyrics"})
        if lyrics:
            lyrics = lyrics.get_text()
            lyrics = lyrics.splitlines()
            lyrics = recheck(lyrics)
            if len(lyrics)>0:
                lyric = random.choice(lyrics)
                try:
                    if detect(lyric) == 'en':
                        ftitle = soup.title.get_text()
                        #print(lyric)
                        title = song_title(ftitle)
                        #print(title)
                        now = datetime.now()
                        current_time = now.strftime("%H:%M:%S")
                        #print("Current Time =", current_time)
                        today = date.today()
                        #print("Today's date:", today)

                        data = {'Song': title,
                                'Time': current_time,
                                'Date': str(today),
                                'Lyric': lyric}
                        tweet.tweetit(lyric+"\n"+title)
                        if client:
                            my_document = db.create_document(data)
                            data['_id'] = my_document['_id']
                        else:
                            pass
                            #print('No database')
                        var=0
                        elapsed = time.time() - start
                        time.sleep(10800-float(elapsed))
                except:
                    pass

