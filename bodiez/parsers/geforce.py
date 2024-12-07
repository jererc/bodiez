import requests

from bodiez.parsers.base import BaseParser


class GeforceDriverVersionParser(BaseParser):
    id = 'geforce_driver_version'

    def can_parse(self):
        return self.url_item.url == 'geforce-driver-version'

    def parse(self):
        url = 'https://gfwsl.geforce.com/services_toolkit/services/com/nvidia/services/AjaxDriverService.php?func=DriverManualLookup&psid=120&pfid=942&osID=57&languageCode=1033&beta=0&isWHQL=1&dltype=-1&dch=1&upCRD=0&qnf=0&ctk=null&sort1=1&numberOfResults=1'
        res = requests.get(url)
        if res.status_code != 200:
            raise Exception(f'error {res.status_code}')
        yield res.json()['IDS'][0]['downloadInfo']['Version']
