''' Create the bot's content '''
from bot import settings
from bot.blacklist import check_blacklist

from datetime import datetime
import json
import random
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from TwitterAPI import TwitterAPI

API = TwitterAPI(settings.TWITTER_API_KEY, settings.TWITTER_API_SECRET,
                 settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_ACCESS_SECRET)

def get_tweet(adjective):
    ''' create a comparison sentence based on tweets '''

    # load noun parts from twitter search
    nouns = get_nouns(adjective)

    if len(nouns) < 2:
        return False

    # build the sentences based on the nouns
    sentences = [
        '{the1}{noun1} {is1} like {the2}{noun2} -- {adj}',
        '{the1}{noun1} {is1} like {the2}{noun2}: {adj}',
        '{the1}{noun1} {is1} as {adj} as {the2}{noun2}',
        '{the1}{noun1} {is1} {adj} like {the2}{noun2}',
        '{the1}{noun1}, like {the2}{noun2}, {is1} {adj}',
        'like {the2}{noun2}, {the1}{noun1} {is1} {adj}',
    ]

    # prioritize definite articles
    if nouns[0]['the'].lower() in ['a', 'an'] or \
            nouns[1]['the'].lower() in ['my', 'his', 'her']:
        nouns = nouns[::-1]

    # drop "the" for plurals
    for i in range(0, 2):
        if nouns[i]['the'].lower() == 'the' and nouns[i]['noun'][-1] == 's':
            nouns[i]['the'] = ''
        else:
            nouns[i]['the'] = format_article(nouns[i]['the'])

    result = random.choice(sentences).format(
        the1=nouns[0]['the'],
        noun1=nouns[0]['noun'],
        is1=nouns[0]['is'],
        the2=nouns[1]['the'],
        noun2=nouns[1]['noun'],
        is2=nouns[1]['is'],
        adj=adjective)
    return result


def format_article(word):
    ''' tidy up pronoun/article capitalization '''
    if word != 'I':
        word = word.lower()
    return word + ' '


def get_nouns(adjective):
    ''' search twitter for sentences using the given adjective '''
    verbs = ['is', 'was', 'are', 'were', 'will be']
    articles = [
        'my', 'your',
        'his', 'her',
        'a', 'an',
        'the', 'this'
    ]
    prompt = ' OR '.join('"%s %s"' % (v, adjective) for v in verbs)
    prompt += ' OR ' + ' OR '.join('%s %s' % (a, adjective) for a in articles)

    # find structurally compatible tweets that use the adjective
    tweets = API.request('search/tweets', {
        'q': prompt,
        'count': 100,
        'lang': 'en',
        'result_type': 'recent',
    })

    articles = r'\b|\b'.join(articles)
    verbs = r'\b|\b'.join(verbs)
    exclude = r'\b|\b'.join(
        ['who', 'that', 'which', 'but', 'it', 'whether', 'if',
         'we', 'she', 'he', 'they', 'I', 'you', 'name'])

    # matches "the dog is cute"
    regex = re.compile(
        r'(\b%s\b) (((?!\b%s\b)[a-z\s-]){1,15}) (\b%s\b) %s' % \
                (articles, exclude, verbs, adjective),
        re.I)

    # matches "the cute dog"
    secondary_regex = re.compile(
        r'(\b%s\b) %s (((?!\b%s\b|\bone\b)[a-z]){1,15}) ' % \
                (articles, adjective, exclude), re.I)

    nouns = []
    secondary_nouns = [] # separate since these often suck
    used_nouns = []
    for tweet in tweets:
        if not 'text' in tweet:
            continue

        text = tweet['text']

        if check_blacklist(text):
            continue

        # detect a "my/the __ is/are green" pattern
        match = re.search(regex, text)
        if match:
            groups = match.groups()

            # detect duplicate entries to avoid super common things like
            # "my heart is broken" over and over
            if len(match.groups()) < 4 or groups[1].lower() in used_nouns:
                continue
            nouns.append({
                'the': groups[0],
                'noun': groups[1],
                'is': groups[3],
            })
            used_nouns.append(groups[1].lower())
        elif re.search(secondary_regex, text):
            # we don't get a verb with this pattern, so it's not ideal
            match = re.search(secondary_regex, text)
            groups = match.groups()
            if groups[1].lower() in used_nouns:
                continue

            # kinda crude plural detection
            verb = 'are' if groups[1][-1] == 's' else 'is'
            # fix a/an matching
            if groups[0] == 'a' and groups[1][0] in 'aeiou':
                groups[0] = 'an'
            elif groups[0] == 'an' and groups[1][0] not in 'aeiou':
                groups[0] = 'a'
            secondary_nouns.append({
                'the': groups[0],
                'noun': groups[1],
                'is': verb,
            })
            used_nouns.append(groups[1].lower())

        if len(nouns) == 2:
            break
    nouns += secondary_nouns
    return nouns


def get_adjectives():
    ''' get a random adjective from wordnik '''
    data = {
        'hasDictionaryDef': True,
        'includePartOfSpeech': 'adjective',
        'minCorpusCount': settings.WORDNIK_CORPUS_COUNT,
        'maxCorpusCount': -1,
        'minDictionaryCount': 2,
        'maxDictionaryCount': -1,
        'minLength': 4,
        'maxLength': -1,
        'limit': settings.QUEUE_COUNT,
        'api_key': settings.WORDNIK_KEY
    }

    params = urlencode(data)
    response = urlopen(Request(
        'http://api.wordnik.com:80/v4/words.json/randomWords?' + params))
    response = json.loads(response.read().decode("utf-8"))
    adjectives = [r['word'] for r in response if r['word'][-2:] != 'er']
    return adjectives


def fill_queue():
    ''' populate a json file with things to post the future '''
    try:
        queue = json.load(open('%s/queue.json' % settings.FILEPATH))
    except OSError:
        queue = []

    print('------- creating metaphor -------')
    print(datetime.today().isoformat())

    adjectives = get_adjectives()
    for adjective in adjectives:
        print('attempting to use adjective: ' + adjective)
        text = get_tweet(adjective)
        if text:
            print(text)
            queue.append(text)
        time.sleep(1)

    json.dump(queue, open('%s/queue.json' % settings.FILEPATH, 'w'))
    print('---------------------------------')


if __name__ == '__main__':
    fill_queue()
