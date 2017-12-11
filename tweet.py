''' post a tweet from the queued file '''
import json
import settings
from TwitterAPI import TwitterAPI

API = TwitterAPI(settings.API_KEY, settings.API_SECRET,
                 settings.ACCESS_TOKEN, settings.ACCESS_SECRET)

queue = json.load(open('queue.json'))

text = queue[0]
r = API.request('statuses/update', {'status': text})
print(r.response)
json.dump(queue, open('queue.json', 'w'))
