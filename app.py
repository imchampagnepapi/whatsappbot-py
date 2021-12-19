import os
import sys
import re
import string
import random
import urllib
import requests
import json
import urllib.request
import urllib.parse
import giphy_client
from giphy_client.rest import ApiException
from random import randint

from profanityfilter import ProfanityFilter
pf = ProfanityFilter()

from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from twilio.twiml.voice_response import Record, VoiceResponse

from song import Song

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
headers = { 'User-Agent': USER_AGENT }

JIO_SAAVN_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1;' +
        ' WOW64; rv:39.0) Gecko/20100101 Firefox/75.0',
}

account_sid = 'AC3c600310d1da548ea07a9cc421f9cd00'
auth_token = 'e389a2d283a6d008aafa02bd7e5221fe'
client = Client(account_sid, auth_token)

api_instance = giphy_client.DefaultApi()
giphy_token =  'fgEpTwmDIoWWfCkgYSbTC4zDJdKHNC8T'

from_whatsapp_number = 'whatsapp:+14155238886'
to_whatsapp_number = 'whatsapp:+917016048948'

app = Flask(__name__)

@app.route("/")
def hello():
	return "Hello World"


@app.route("/sms", methods=['POST','GET'])
def sms_reply():
    msg = request.form.get('Body')

    if(msg.startswith("!img ")):
            resp = MessagingResponse()
            query_key = msg[5:]

            urllist = []
            url = 'https://www.bing.com/images/async?q={}&first=0&adlt=off'.format(query_key.replace(" ", "+"))
            request2 = urllib.request.Request(url, None, headers = headers)
            response = urllib.request.urlopen(request2)
            html = response.read().decode('utf8')

            links = re.findall('murl&quot;:&quot;(.*?)&quot;',html)
            print(links)

            if len(links) == 0:
                msg = resp.message("No Image Found!")
                pass
            else:
                url = links[random.randrange(len(links))]
                msg = resp.message()
                msg.media(url)

            return str(resp)

    
    elif msg.startswith("!jio "):
        resp = MessagingResponse()
        song_url_list = jio_query(str(msg[5:]))
        if len(song_url_list) > 0:
            msg = resp.message()
            msg.media(url)
        else:
            msg = resp.message(f"No song found for {msg[5:]}")
        return str(resp)
    
    elif(msg.startswith("!ud ")):
            query = msg[4:]
            resp = MessagingResponse()
            quoted_query = urllib.request.quote(query).replace("%20","")
            url = 'http://api.urbandictionary.com/v0/define?term=%s' % quoted_query
            response = urllib.request.urlopen(url)
            data = json.loads(response.read())

            if len(data['list'])==0:
                    msg = resp.message(f"No result found for {query}")
                    pass

            else:
                    definition = data['list'][0]['definition']
                    urls = data['list'][0]['permalink']
                    s = str(definition)
                    if("[" in s or "]" in s):
                            s2 = str(s).replace("[" ,"").replace("]","")
                            msg = resp.message("Word: "+quoted_query + "\r\n" +"Definition: " +s2 +"\r\n\r\n"+ ">> " + urls)
                    else:
                            msg = resp.message("Word: "+quoted_query + "\r\n" +"Definition: " +s +"\r\n\r\n"+ ">> " + urls)

            return str(resp)

    elif(msg.startswith("!gif ")):
            gif_search = msg[5:]
            resp = MessagingResponse()


            search = str(gif_search).replace("!@#$%^&*()[]{};:,./<>?\|`~-=_", "")
            search = str(search).replace(" ","+")
            pattern = re.compile("[A-Za-z0-9\+\s]")
            s1 = pattern.match(search)
            if s1:
                print("valid")
                try:
                    if(pf.is_clean(search)):
                        response = api_instance.gifs_search_get(giphy_token, search, rating='pg-13', limit=25,offset=randint(1,10), fmt='gif')
                        lst = list(response.data)

                        if len(lst) == 0:
                            msg = resp.message("No Gif Found!")
                            pass
                        else:
                            gif_id = random.choices(lst)
                            url_gif = gif_id[0].images.downsized.url
                            str1 = str(url_gif)

                            msg = resp.message(str1[:str1.find('?')])
                    else:
                        msg = resp.message("bad word")
                except ApiException as e:
                        msg = resp.message("not found")
                        print("Exception when calling DefaultApi->gifs_search_get: %s\n" % e)
                        pass
            else:
                sg = resp.message("Invalid!")

            return str(resp)


def jio_query(query_text, max_results=5):
    """Fetch songs from query."""
    req = requests.get(
        headers=JIO_SAAVN_HEADERS,
        url=f"https://www.jiosaavn.com/api.php?p=1&q={query_text.replace(' ', '+')}\
            &_format=json&_marker=0&api_version=4&ctx=wap6dot0\
            &n={max_results}&__call=search.getResults")
    return parse_query(req.json())

if __name__ == "__main__":
    app.run(debug=True)