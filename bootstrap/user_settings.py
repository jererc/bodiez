import os

GOOGLE_CREDS = os.path.join(os.path.expanduser('~'), 'google_creds.json')

params_1337x = {
    'xpath': '//table/tbody/tr/td[1]/a[2]',
}
params_geforce_news = {
    'xpath': '//div[contains(@class, "article-title-text")]/a',
}
params_lexpress = {
    'main_xpath': '//div[contains(@class, "card-row")]',
    'text_xpaths': [
        './/div[contains(@class, "title-holder")]/h2',
        './/address',
        './/div[contains(@class, "card-foot-price")]/strong/a',
    ],
}

URLS = [
    {
        'url': 'https://1337x.to/cat/Games/1/',
        'id': 'games',
        'params': params_1337x,
    },
    {
        'url': 'https://1337x.to/cat/Anime/1/',
        'id': 'anime',
        'params': params_1337x,
    },
    {
        'url': 'https://www.nvidia.com/en-us/geforce/news/',
        'id': 'geforce-news',
        'params': params_geforce_news,
        'update_delta': 12 * 3600,
    },
    {
        'url': 'https://www.lexpressproperty.com/en/buy-mauritius/residential_land/riviere_noire-la_gaulette-la_preneuse-tamarin/?price_max=8%2C000%2C000&currency=MUR&filters%5Bland_unit%5D%5Beq%5D=m2',
        'id': 'land-west',
        'params': params_lexpress,
        'update_delta': 8 * 3600,
    },
]
