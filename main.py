import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from TwitterSearch import *

with open("db.json") as dataFile:
    data = json.load(dataFile)


def TwitterAnalyse(temp):
    try:
        list = temp.split(' ')
        print('searched keywords: %s' % list[4:])
        tso = TwitterSearchOrder()
        tso.set_keywords(list[4:])
        tso.set_language('en')
        tso.remove_all_filters()
        ts = TwitterSearch(
            consumer_key=list[0],
            consumer_secret=list[1],
            access_token=list[2],
            access_token_secret=list[3],
        )

        def my_callback_closure(current_ts_instance):
            queries, tweets_seen = current_ts_instance.get_statistics()
            if queries > 0 and (queries % 5) == 0:
                time.sleep(10)
        data['tweets_count'] = 0
        data['tweets'] = []
        for tweet in ts.search_tweets_iterable(tso,callback=my_callback_closure):
            dict = {}
            dict['Main Information'] = (
                    'author %s with nickname @%s tweeted: %s' % (tweet['user']['name'], tweet['user']['screen_name'],
                                                                 tweet['text']))
            dict['Author_information'] = {'name': tweet['user']['name'], 'username': tweet['user']['screen_name'],
                                          'follower_count': tweet['user']['followers_count'],
                                          'following_count': tweet['user']['friends_count']}
            dict['Date'] = tweet['created_at']
            dict['Tweet_contents'] = {'Tweet': tweet['text'], 'Hastags': tweet['entities']['hashtags'],
                                      'urls': tweet['entities']['urls'],
                                      'Language': tweet['lang']}
            dict['Number_of_likes'] = tweet['favorite_count']
            dict['Number_of_retweets'] = tweet['retweet_count']
            dict['Number_of_discussions'] = len(tweet['entities']['user_mentions'])
            data['tweets'].append(dict)

        data['tweets'].sort(key=lambda x: (x['Number_of_retweets'], x['Number_of_likes'], x['Number_of_discussions']),
                            reverse=True)
        data['tweets_count'] = len(data['tweets'])
    except TwitterSearchException as e:
        print(e)


class tweetAnalyzer(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        len = int(self.headers['Content-Length'])
        stream = self.rfile.read(len)
        temp = stream.decode('utf8').strip('b\'')
        temp = temp.strip('"')
        temp = temp.replace(r'\n', '\n')
        self.end_headers()
        return temp

    def do_POST(self):
        temp = self._set_headers()
        TwitterAnalyse(temp)
        with open("db.json", 'w+') as data_file:
            json.dump(data, data_file)

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=3).encode("utf8"))


server = HTTPServer(('localhost', 8080), tweetAnalyzer)
server.serve_forever()
