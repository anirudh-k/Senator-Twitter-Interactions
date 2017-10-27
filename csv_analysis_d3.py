import csv
import json
from sets import Set
import sys

tag_endings = [' ', ':', ',', '.', '!', '?', ';', '\'']


def find_index(string, substring, start_index):
    try:
        index = string.index(substring, start_index)
        return index
    except:
        return sys.maxint


def find_between(s, first, endings):
    s_copy = str(s)
    substrings = Set()
    while True:
        try:
            start = s_copy.index(first) + len(first)
            end = min(
                map(lambda ending: find_index(s_copy, ending, start), endings))
            substrings.add(s_copy[start:end])
            s_copy = s_copy[:start - 1] + s_copy[end:]
        except ValueError:
            break
    if 'realDonaldTrump' in s_copy:
        print('FAILED')
        sys.exit()
    return substrings


def remove_non_ascii(s):
    string_list = [x for x in s]
    idx = 0
    for x in string_list:
        if ord(x) > 128:
            break
        else:
            idx += 1
    return ''.join(string_list[:idx])


def build_mentions(tweets, accounts, mentions):
    for tweet in tweets:
        tweet_contents = tweet['text']
        tweet_author = tweet['user']

        tagged_users = map(lambda x: remove_non_ascii(x),
                           find_between(tweet_contents, '@', tag_endings))

        for tagged_user in tagged_users:
            if tagged_user in accounts:
                if tweet_author in mentions:
                    if tagged_user in mentions[tweet_author]:
                        mentions[tweet_author][tagged_user] += 1
                    else:
                        mentions[tweet_author][tagged_user] = 1
                else:
                    mentions[tweet_author] = {}
                    mentions[tweet_author][tagged_user] = 1
    return mentions


def build_nodes(accounts):
    nodes = []
    for account in accounts:
        group = 1 if account['party'] == 'D' else 2
        if account['id'] == 'realDonaldTrump':
            group = 3
        if account['id'] == 'BarackObama':
            group = 4
        nodes.append({'id': account['id'], 'group': group})
    return nodes


def build_links(mentions):
    links = []
    for source in mentions:
        for target in mentions[source]:
            if any(((edge['source'] == source and edge['target'] == target) or
                    (edge['source'] == target and edge['target'] == source))
                   for edge in links):
                for edge in [
                        edge for edge in links
                        if
                    ((edge['source'] == source and edge['target'] == target) or
                     (edge['source'] == target and edge['target'] == source))
                ]:
                    edge['value'] += mentions[source][target]
            else:
                links.append({
                    'source': source,
                    'target': target,
                    'value': mentions[source][target]
                })
    return links


def build_graph_json(nodes, links):
    return json.dumps({'nodes': nodes, 'links': links}, indent=2)


with open('realDonaldTrump - fivethirtyeight.csv') as trump, open(
        'BarackObama - fivethirtyeight.csv') as obama, open(
            'senators - fivethirtyeight.csv') as senators:
    trump_tweets = csv.DictReader(trump)
    obama_tweets = csv.DictReader(obama)
    senator_tweets = csv.DictReader(senators)

    accounts = Set()
    accounts_with_party = []

    # produce list of politicians' twitter handles
    for tweet in senator_tweets:
        set_length = len(accounts)
        accounts.add(tweet['user'])
        if len(accounts) > set_length:
            accounts_with_party.append({
                'id': tweet['user'],
                'party': tweet['party']
            })
    senators.seek(0)
    accounts.add('realDonaldTrump')
    accounts_with_party.append({'id': 'realDonaldTrump', 'party': 'R'})
    accounts.add('BarackObama')
    accounts_with_party.append({'id': 'BarackObama', 'party': 'D'})

    mentions = {}
    mentions = build_mentions(senator_tweets, accounts, mentions)
    mentions = build_mentions(trump_tweets, accounts, mentions)
    mentions = build_mentions(obama_tweets, accounts, mentions)

    nodes = build_nodes(accounts_with_party)
    links = build_links(mentions)
    graph_json = build_graph_json(nodes, links)

    log = open("f830985c60d7d78c1ebdf2c3c4b50046/politicians.json", "w")
