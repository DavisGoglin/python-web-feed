from selector import Selector
import requests
import lxml
import logging

logging.basicConfig(level=logging.DEBUG)

class Feed:

    _selector_properties = [
        'updated',
        'title',
        'author',
    ]

    _entry_selector_properties = [
        'title',
        'updated',
        'url',
    ]

    _dates = [
        'updated'
    ]

    def __init__(self, config):
        self.config = config

        self.url = None
        if 'url' in config:
            self.url = config['url']

        self.properties = {}

        self.entries = []

    def load(self, url=None):
        logging.info("Loading data from {}".format(url))
        url = url or self.url
        request = requests.get(url)
        request.raise_for_status()
        self._raw = request.text

    def parse(self, html=None):
        html = html or self._raw

        parsed = lxml.html.fromstring(html)
        self.properties = self._parse_properties(parsed)
        self.entries = self._parse_entries(parsed)

    def _parse_entries(self, htmltree):
        _entries = []
        logging.info("Working on entries")
        config_entries = self.config['entries']

        entries_selector = Selector(config_entries, multiple=True)

        logging.info("Using selector \"{}\" with selector type {}".format(
            entries_selector.selector,
            entries_selector.SelectorType.__class__.__name__,
        ))

        result_entries = entries_selector.result(htmltree)
        logging.info('Got {} entries'.format(
            len(result_entries)
        ))

        for entry in result_entries:
            logging.info('Working on entry {}'.format(entry))
            tmp_entry = {}

            for property in self._entry_selector_properties:
                if property not in config_entries:
                    logging.info("No config found for {}".format(property))
                    continue
                logging.info('Working on prop {}'.format(property))

                args = {
                    'selector': config_entries[property],
                }
                if property in self._dates:
                    args['is_date'] = True
                selector = Selector(**args)

                logging.info(
                    "Using selector \"{}\" with selector type {}".format(
                        selector.selector,
                        selector.SelectorType.__class__.__name__,
                    )
                )

                tmp_entry[property] = selector.result(entry)

            _entries.append(tmp_entry)
        return _entries

    def _parse_properties(self, htmltree):
        # Populate properties from selectors
        _properties = {}
        config_props = self.config['properties']
        # Search for each property option
        for property in self._selector_properties:
            if property not in config_props:
                logging.info("No config found for {}".format(property))
                continue

            logging.info('Working on {}'.format(property))

            args = {
                'selector': config_props[property],
            }
            if property in self._dates:
                args['is_date'] = True
            selector = Selector(**args)

            logging.info("Using selector \"{}\" with selector type {}".format(
                selector.selector,
                selector.SelectorType.__class__.__name__,
            ))

            result_text = selector.result(htmltree)
            logging.info('Found prop value {}'.format(result_text))

            _properties[property] = result_text

        return _properties


if __name__ == '__main__':
    import yaml
    import pprint

    logging.basicConfig(level=logging.DEBUG)

    with open('example.yaml', 'r') as f:
        config = yaml.load(f, Loader=yaml.BaseLoader)
    with open('example.html', 'r') as f:
        html = f.read()

    feed = Feed(config['feeds']['example'])

    feed.parse(html)

    print("Properties")
    pp = pprint.PrettyPrinter()
    pp.pprint(feed.properties)
    print("Entries")
    pp.pprint(feed.entries)
