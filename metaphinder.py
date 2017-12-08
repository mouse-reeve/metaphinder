''' let's learn about birds '''
import blacklist
from datetime import datetime
import re
import settings
import sys
from TwitterAPI import TwitterAPI

API = TwitterAPI(settings.API_KEY, settings.API_SECRET,
                 settings.ACCESS_TOKEN, settings.ACCESS_SECRET)

def build_metaphor(adjective):
    ''' create a comparison sentence based on tweets '''
    # pick an adjective around which to build the comparison
    prompt = 'is %s' % adjective

    nouns = []
    # find structurally compatible tweets that use the adjective
    tweets = API.request('search/tweets', {'q': '"%s"' % prompt})
    for tweet in tweets:
        if not 'text' in tweet:
            continue

        text = tweet['text']

        if blacklist.check_blacklist(text):
            continue

        # detect a "my/the __ is green" pattern
        print(text)
        articles = '|'.join(['my', 'his', 'her', 'a', 'an', 'the', 'that'])
        match = re.search(r'(\b%s\b) (.{1,20}) %s' % \
                (articles, prompt), text.lower())
        if match and len(match.groups()) > 1:
            nouns.append(match.groups())

        if len(nouns) == 2:
            break
    print(nouns)

    # build the sentence
    if len(nouns) >= 2:
        result = '%s %s is as %s as %s %s' % \
            (nouns[0][0], nouns[0][1], adjective, nouns[1][0], nouns[1][1])
        print result
        return result

    return False


def post_tweet():
    ''' load the text and post to twitter '''
    print('--------- creating metaphor --------')
    print(datetime.today().isoformat())

    text = build_metaphor('green')
    print(text)

    print('--------- posting tweet --------')
    r = API.request('statuses/update', {'status': text})
    print(r.response)


if __name__ == '__main__':
    #post_tweet()
    try:
        input_adjective = sys.argv[1]
    except IndexError:
        input_adjective = 'green'
    build_metaphor(input_adjective)
