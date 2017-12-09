''' let's learn about birds '''
from datetime import datetime
import json
import random
import re
import settings
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import blacklist
from TwitterAPI import TwitterAPI

API = TwitterAPI(settings.API_KEY, settings.API_SECRET,
                 settings.ACCESS_TOKEN, settings.ACCESS_SECRET)

def build_metaphor(adjective):
    ''' create a comparison sentence based on tweets '''
    # pick an adjective around which to build the comparison
    prompt = 'is %s' % adjective

    nouns = []
    # find structurally compatible tweets that use the adjective
    tweets = API.request('search/tweets', {
        'q': '"%s"' % prompt,
        'count': 100,
        'lang': 'en',
        'result_type': 'recent',
    })
    for tweet in tweets:
        if not 'text' in tweet:
            continue

        text = tweet['text']

        if blacklist.check_blacklist(text):
            continue

        # detect a "my/the __ is green" pattern
        articles = r'\b|\b'.join(['my', 'his', 'her', 'a', 'an', 'the'])
        regex = re.compile(r'(\b%s\b) ([a-z\s]{1,15}) %s' % (articles, prompt),
                           re.I)
        match = re.search(regex, text)
        if match and len(match.groups()) > 1:
            nouns.append(match.groups())

        # deduplicate entries to avoid super common things like
        # "my heart is broken" over and over
        nouns = list(set(nouns))
        if len(nouns) == 2:
            break

    # build the sentence
    sentences = [
        '{the1} {noun1} is as {adj} as {the2} {noun2}',
        '{the1} {noun1} is like {the2} {noun2} -- {adj}',
        '{the1} {noun1} is like {the2} {noun2}: {adj}',
        '{the1} {noun1} is {adj} like {the2} {noun2}',
        '{the1} {noun1} is {the2} {noun2}, {the2} %s{adj} {noun2}' % \
            random.choice(['eternally ', 'ever-', 'always-']),
    ]
    if len(nouns) >= 2:
        # prioritize definite articles
        if nouns[0][0] in ['a', 'an'] or nouns[1][0] in ['my', 'his', 'her']:
            nouns = nouns[::-1]

        result = random.choice(sentences).format(
            the1=nouns[0][0],
            noun1=nouns[0][1],
            the2=nouns[1][0].lower(),
            noun2=nouns[1][1],
            adj=adjective)
        return result

    return False


def get_adjective():
    ''' get a random adjective from wordnik '''
    data = {
        'hasDictionaryDef': True,
        'includePartOfSpeech': 'adjective',
        'minCorpusCount': 1500,
        'maxCorpusCount': -1,
        'minDictionaryCount': 1,
        'maxDictionaryCount': -1,
        'minLength': 4,
        'maxLength': -1,
        'api_key': settings.WORDNIK_KEY
    }

    params = urlencode(data)
    response = urlopen(Request(
        'http://api.wordnik.com:80/v4/words.json/randomWord?' + params))
    response = json.loads(response.read().decode("utf-8"))
    adjective = response['word']
    return adjective


def post_tweet():
    ''' load the text and post to twitter '''
    print('------- creating metaphor -------')
    print(datetime.today().isoformat())

    text = False
    while not text:
        adjective = get_adjective()
        print 'attempting to use adjective: ' + adjective
        text = build_metaphor(adjective)
        if not text:
            # poor man's rate limiting
            time.sleep(2)
    print(text)

    print('--------- posting tweet --------')
    r = API.request('statuses/update', {'status': text})
    print(r.response)
    print('--------------------------------')


if __name__ == '__main__':
    post_tweet()
