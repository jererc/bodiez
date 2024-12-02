import os

GOOGLE_CREDS = os.path.join(os.path.expanduser('~'), 'creds.json')
URLS = [
    {
        'url': 'https://1337x.to/cat/Games/1/',
    },
    {
        'url': 'https://1337x.to/cat/Movies/1/',
        'id': 'movies',
        'update_delta': 8 * 3600,
    },
]
