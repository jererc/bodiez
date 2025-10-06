xpath_1337x = '//table/tbody/tr/td[1]/a[2]'
filter_xpath_1337x = '../../td[3]'
filter_callable_1337x = lambda x: int(x) > 50
next_page_xpath_1337x = '//a[contains(text(), ">>")]'

xpath_libgen = '//tr/td[1]/a[@title][1]'


def rate_key_generator(body, step):
    price = float(body.title.replace('$', '').replace(',', ''))
    return str(price - (price % step))


QUERIES = [
    {
        'url': 'https://1337x.to/user/FitGirl/',
        'id': 'FitGirl',
        'xpath': xpath_1337x,
        'filter_xpath': filter_xpath_1337x,
        'filter_callable': filter_callable_1337x,
        'next_page_xpath': next_page_xpath_1337x,
        'pages': 3,
        'block_external': True,
        'max_notif': 10,
    },
    {
        'url': 'https://1337x.to/user/DODI/',
        'id': 'DODI',
        'xpath': xpath_1337x,
        'filter_xpath': filter_xpath_1337x,
        'filter_callable': filter_callable_1337x,
        'next_page_xpath': next_page_xpath_1337x,
        'pages': 2,
        'block_external': True,
        'max_notif': 10,
    },
    {
        'url': 'https://www.techspot.com/drivers/manufacturer/nvidia_geforce/',
        'id': 'geforce-drivers',
        'xpath': '//div[contains(@class, "title")]/a',
        'block_external': True,
        'update_delta': 18 * 3600,
    },
    {
        'url': 'https://coinmarketcap.com/currencies/bitcoin/',
        'id': 'btc-usd',
        'xpath': '//span[@data-test="text-cdp-price-display"]',
        'block_external': True,
        'key_generator': lambda x: rate_key_generator(x, 2000),
        'history_size': 2,
        'update_delta': 4 * 3600,
    },
    {
        'url': 'https://coinmarketcap.com/currencies/xrp/',
        'id': 'xrp-usd',
        'xpath': '//span[@data-test="text-cdp-price-display"]',
        'block_external': True,
        'key_generator': lambda x: rate_key_generator(x, .02),
        'history_size': 2,
        'update_delta': 4 * 3600,
        'active': False,
    },
    {
        'url': 'https://libgen.gl/index.php?req=lenglet+maitre+lang%3Afre+ext%3Aepub&columns%5B%5D=t&columns%5B%5D=a&columns%5B%5D=s&columns%5B%5D=y&columns%5B%5D=p&columns%5B%5D=i&objects%5B%5D=f&objects%5B%5D=e&objects%5B%5D=s&objects%5B%5D=a&objects%5B%5D=p&objects%5B%5D=w&topics%5B%5D=l&topics%5B%5D=c&topics%5B%5D=f&topics%5B%5D=a&topics%5B%5D=m&topics%5B%5D=r&topics%5B%5D=s&res=100&gmode=on&filesuns=all',
        'id': 'libgen-lenglet-maitre',
        'xpath': xpath_libgen,
        'block_external': True,
        'allow_no_results': True,
        'update_delta': 18 * 3600,
    },
    {
        'url': 'https://rutracker.org/forum/tracker.php?f=557',
        'id': 'classical',
        'login_xpath': '//input[@name="login_username"]',
        'xpath': '//div[contains(@class, "t-title")]/a',
        'block_external': True,
        'update_delta': 6 * 3600,
        'active': False,
    },
    {
        'url': 'https://www.intel.com/content/www/us/en/support/articles/000005489/wireless.html',
        'id': 'intel-wireless-drivers',
        'xpath': '//table[contains(@class, "icstable")]/tbody/tr[not(contains(@class, "icstablehead"))]/td/*/a',
        'block_external': True,
        'update_delta': 18 * 3600,
        'active': False,
    },
    {
        'url': 'https://actualitte.com/thematique/35/chroniques',
        'id': 'livres',
        'xpath': '//a[contains(@class, "list-article_link") or contains(@class, "article-card_link")]/h2',
        'link_xpath': '..',
        'block_external': True,
        'update_delta': 6 * 3600,
        'active': False,
    },
    {
        'url': 'https://www.lexpressproperty.com/en/buy-mauritius/residential_land/riviere_noire-la_gaulette-la_preneuse-tamarin/?price_max=6%2C000%2C000&currency=MUR&filters%5Bland_unit%5D%5Beq%5D=m2',
        'id': 'land-west',
        'xpath': '//div[contains(@class, "card-row")]',
        'text_xpaths': [
            './/div[contains(@class, "title-holder")]/h2',
            './/address',
            './/div[contains(@class, "card-foot-price")]/strong/a',
        ],
        'link_xpath': './/a',
        'block_external': True,
        'update_delta': 4 * 3600,
        'active': False,
    },
    {
        'url': 'https://www.facebook.com/marketplace/108433389181024/propertyforsale',
        'id': 'fb-properties',
        'login_xpath': '//input[@name="email"]',
        'xpath': '//img',
        'group_xpath': '../../../../../../../div[2]/div',
        'group_attrs': ['width', 'height'],
        'link_xpath': '../../..',
        'pages': 3,
        'update_delta': 6 * 3600,
        'active': False,
    },
    {
        'url': 'https://www.facebook.com/iqonmauritius',
        'id': 'fb-iqon',
        'login_xpath': '//input[@name="email"]',
        'xpath': '//*[local-name()="svg"][@aria-label]',
        'group_xpath': '../../../../../../../../../div[3]/div[1]',
        'group_attrs': ['x'],
        'link_xpath': '../div[2]//a',
        'pages': 3,
        'update_delta': 4 * 3600,
        'active': False,
    },
]
