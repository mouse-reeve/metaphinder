''' let's learn about birds '''
import blacklist
from datetime import datetime
import re
import settings
from TwitterAPI import TwitterAPI

API = TwitterAPI(settings.API_KEY, settings.API_SECRET,
                 settings.ACCESS_TOKEN, settings.ACCESS_SECRET)

def build_metaphor():
    ''' create a comparison sentence based on tweets '''
    # pick an adjective around which to build the comparison
    adjective = 'green'
    prompt = 'is %s' % adjective

    # find structurally compatible tweets that use the adjective
    tweets = API.request('search/tweets', {'q': '"%s"' % prompt})
    for tweet in tweets:
        if not 'text' in tweet:
            continue

        text = tweet['text']

        if blacklist.check_blacklist(text):
            continue

        # detect a "my/the __ is green" pattern
        if re.match(r'(my|the) ([.*]{1,20}) %s' % prompt, text):
            print text
            import pdb;pdb.set_trace()
        import pdb;pdb.set_trace()

    # build the sentence
    text = ''

    return text


def post_tweet():
    ''' load the text and post to twitter '''
    print('--------- creating metaphor --------')
    print(datetime.today().isoformat())

    text = build_metaphor()
    print(text)

    print('--------- posting tweet --------')
    r = API.request('statuses/update', {'status': text})
    print(r.response)


if __name__ == '__main__':
    post_tweet()
