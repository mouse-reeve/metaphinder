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
    verbs = ['is', 'was', 'are', 'were', 'will be']
    prompt = ' OR '.join('"%s %s"' % (v, adjective) for v in verbs)

    nouns = []
    # find structurally compatible tweets that use the adjective
    tweets = API.request('search/tweets', {
        'q': prompt,
        'count': 100,
        'lang': 'en',
        'result_type': 'recent',
    })

    articles = r'\b|\b'.join(['my', 'his', 'your', 'her', 'a', 'an', 'the'])
    verbs = r'\b|\b'.join(verbs)
    exclude = r'\b|\b'.join(
        ['who', 'that', 'which', 'but',
         'we', 'she', 'he', 'they'])
    regex = re.compile(
        r'(\b%s\b) (((?!\b%s\b)[a-z\s-]){1,15}) (\b%s\b) %s' % \
                (articles, exclude, verbs, adjective),
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

            # detect duplicate entries to avoid super common things like
            # "my heart is broken" over and over
            if len(match.groups()) < 4 or groups[1] in used_nouns:
                continue
            nouns.append({
                'the': groups[0],
                'noun': groups[1],
                'is': groups[3],
            })
            used_nouns.append(groups[1])

        if len(nouns) == 2:
            break

    # build the sentence
    sentences = [
        '{the1} {noun1} {is1} like {the2} {noun2} -- {adj}',
        '{the1} {noun1} {is1} like {the2} {noun2}: {adj}',
        '{the1} {noun1} {is1} as {adj} as {the2} {noun2}',
        '{the1} {noun1} {is1} {adj} like {the2} {noun2}',
    ]

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
        'minCorpusCount': 1,
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
    adjectives = [r['word'] for r in response if r['word'][-2:] != 'er']
    return adjectives


def fill_queue():
    ''' load the text and post to twitter '''
    print('------- creating metaphor -------')
    print(datetime.today().isoformat())

    queue = json.load(open('queue.json'))
    text = False
    adjectives = get_adjectives()
    for adjective in adjectives:
        print('attempting to use adjective: ' + adjective)
        text = build_metaphor(adjective)
        if text:
            print(text)
            queue.append(text)
        time.sleep(1)

    json.dump(queue, open('queue.json', 'w'))
    print('---------------------------------')


if __name__ == '__main__':
    fill_queue()
