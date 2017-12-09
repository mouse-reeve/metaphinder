''' let's learn about birds '''
from datetime import datetime
import json
import random
import re
import settings
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import blacklist
from TwitterAPI import TwitterAPI

API = TwitterAPI(settings.API_KEY, settings.API_SECRET,
                 settings.ACCESS_TOKEN, settings.ACCESS_SECRET)

def build_metaphor(adjective):
    ''' create a comparison sentence based on tweets '''
    # pick an adjective around which to build the comparison
    verbs = ['is', 'was', 'are']
    prompt = ' OR '.join('"%s %s"' % (v, adjective) for v in verbs)

    nouns = []
    # find structurally compatible tweets that use the adjective
    tweets = API.request('search/tweets', {
        'q': prompt,
        'count': 100,
        'lang': 'en',
        'result_type': 'recent',
    })

    articles = r'\b|\b'.join(['my', 'his', 'her', 'a', 'an', 'the'])
    verbs = r'\b|\b'.join(verbs)
    regex = re.compile(
        r'(\b%s\b) (((?!\bwho\b|\bthat\b).){1,15}) (\b%s\b) %s' % \
                (articles, verbs, adjective),
        re.I)
    used_nouns = []
    for tweet in tweets:
        if not 'text' in tweet:
            continue

        text = tweet['text']

        if blacklist.check_blacklist(text):
            continue

        # detect a "my/the __ is/are green" pattern
        match = re.search(regex, text)
        if match:
            groups = match.groups()
            if len(match.groups()) < 4 or groups[1] in used_nouns:
                continue
            nouns.append({
                'the': groups[0],
                'noun': groups[1],
                'is': groups[3],
            })
            used_nouns.append(groups[1])

            # deduplicate entries to avoid super common things like
            # "my heart is broken" over and over
        if len(nouns) == 2:
            break

    # build the sentence
    sentences = ['{the1} {noun1} {is1} as {adj} as {the2} {noun2}'] * 5 + \
        ['{the1} {noun1} {is1} like {the2} {noun2} -- {adj}'] * 5 + \
        ['{the1} {noun1} {is1} like {the2} {noun2}: {adj}'] * 5 + \
        ['{the1} {noun1} {is1} {adj} like {the2} {noun2}'] * 3 + \
        ['{the1} {noun1} {is1} {the2} {noun2}, {the2} %s{adj} {noun2}' % \
            random.choice(['eternally ', 'ever-', 'always-'])]

    if len(nouns) >= 2:
        # prioritize definite articles
        if nouns[0]['the'] in ['a', 'an'] or \
                nouns[1]['the'] in ['my', 'his', 'her']:
            nouns = nouns[::-1]

        result = random.choice(sentences).format(
            the1=nouns[0]['the'],
            noun1=nouns[0]['noun'],
            is1=nouns[0]['is'],
            the2=nouns[1]['the'].lower(),
            noun2=nouns[1]['noun'],
            is2=nouns[1]['is'],
            adj=adjective)
        return result
    return False


def get_adjectives():
    ''' get a random adjective from wordnik '''
    data = {
        'hasDictionaryDef': True,
        'includePartOfSpeech': 'adjective',
        'minCorpusCount': 10,
        'maxCorpusCount': -1,
        'minDictionaryCount': 1,
        'maxDictionaryCount': -1,
        'minLength': 4,
        'maxLength': -1,
        'limit': 20,
        'api_key': settings.WORDNIK_KEY
    }

    params = urlencode(data)
    response = urlopen(Request(
        'http://api.wordnik.com:80/v4/words.json/randomWords?' + params))
    response = json.loads(response.read().decode("utf-8"))
    adjectives = [r['word'] for r in response]
    return adjectives


def post_tweet():
    ''' load the text and post to twitter '''
    print('------- creating metaphor -------')
    print(datetime.today().isoformat())

    text = False
    adjectives = get_adjectives()
    for adjective in adjectives:
        print('attempting to use adjective: ' + adjective)
        text = build_metaphor(adjective)
        if text:
            break

    if text:
        print(text)
        print('--------- posting tweet ---------')
        r = API.request('statuses/update', {'status': text})
        print(r.response)
        print('---------------------------------')


if __name__ == '__main__':
    post_tweet()
