''' post a tweet from the queued file '''
from bot import settings
import json
from TwitterAPI import TwitterAPI

try:
    API = TwitterAPI(settings.TWITTER_API_KEY,
                     settings.TWITTER_API_SECRET,
                     settings.TWITTER_ACCESS_TOKEN,
                     settings.TWITTER_ACCESS_SECRET)
except:
    API = None

queue = json.load(open('%s/queue.json' % settings.FILEPATH))

text = queue[0]

if text:
    if API:
        r = API.request('statuses/update', {'status': text})

        if r.status_code != 200:
            print(r.response)
    else:
        print('----- API unavailable -----')
        print(text)

json.dump(queue[1:], open('%s/queue.json' % settings.FILEPATH, 'w'))
