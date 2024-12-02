import os

GOOGLE_CREDS = os.path.join(os.path.expanduser('~'), 'google_creds.json')

PARAMS = {
    '1337x': {
        'main_xpath': '//table/tbody/tr',
        'text_xpaths': [
            './/td[1]/a[2]',
        ],
    },
    'nvidia_geforce': {
        'main_xpath': '//div[contains(@class, "article-title-text")]',
        'text_xpaths': [
            './/a',
        ],
    },
    'lexpressproperty': {
        'main_xpath': '//div[contains(@class, "card-row")]',
        'text_xpaths': [
            './/div[contains(@class, "title-holder")]/h2',
            './/address',
            './/div[contains(@class, "card-foot-price")]/strong/a',
        ],
    },
}

URLS = [
    {
        'url': 'https://1337x.to/cat/Movies/1/',
        'id': 'movies',
        'params': PARAMS['1337x'],
    },
    {
        'url': 'https://www.nvidia.com/en-us/geforce/news/',
        'id': 'geforce news',
        'params': PARAMS['nvidia_geforce'],
        'update_delta': 12 * 3600,
    },
    {
        'url': 'https://www.lexpressproperty.com/en/buy-mauritius/residential_land/riviere_noire-la_gaulette-la_preneuse-tamarin/?price_max=8%2C000%2C000&currency=MUR&filters%5Bland_unit%5D%5Beq%5D=m2',
        'id': 'lexpressproperty land',
        'params': PARAMS['lexpressproperty'],
        'update_delta': 8 * 3600,
    },
]
