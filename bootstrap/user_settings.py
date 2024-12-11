xpath_1337x = '//table/tbody/tr/td[1]/a[2]'

URLS = [
    {
        'url': 'https://1337x.to/cat/Games/1/',
        'id': 'games',
        'xpath': xpath_1337x,
        'max_notif': 10,
    },
    {
        'url': 'https://1337x.to/cat/Anime/1/',
        'id': 'anime',
        'xpath': xpath_1337x,
        'active': False,
    },
    {
        'url': 'https://www.nvidia.com/en-us/geforce/news/',
        'id': 'geforce-news',
        'xpath': '//div[contains(@class, "article-title-text")]/a',
        'update_delta': 12 * 3600,
        'active': False,
    },
    {
        'url': 'https://www.lexpressproperty.com/en/buy-mauritius/residential_land/riviere_noire-la_gaulette-la_preneuse-tamarin/?price_max=8%2C000%2C000&currency=MUR&filters%5Bland_unit%5D%5Beq%5D=m2',
        'id': 'land-west',
        'parent_xpath': '//div[contains(@class, "card-row")]',
        'child_xpaths': [
            './/div[contains(@class, "title-holder")]/h2',
            './/address',
            './/div[contains(@class, "card-foot-price")]/strong/a',
        ],
        'update_delta': 8 * 3600,
        'active': False,
    },
    {
        'url': 'https://www.facebook.com/marketplace/108433389181024/propertyforsale',
        'id': 'facebook-marketplace',
        'scroll_xpath': '//img',
        'rel_xpath': '../../../../../../../../div/div/div',
        'scroll_group_attrs': ['width', 'height'],
        'update_delta': 16 * 3600,
        'active': False,
    },
    {
        'url': 'https://www.facebook.com/iqonmauritius',
        'id': 'facebook-timeline',
        'scroll_xpath': '//*[local-name()="image"]',
        'rel_xpath': '../../../../../../../../../../../../div[3]/div[1]',
        'update_delta': 16 * 3600,
        'active': False,
    },
]
