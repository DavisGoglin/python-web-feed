import requests
import lxml
import re
import dateparser
from pyquery import PyQuery


class Selector:
    def __init__(self, selector):
        self.selector = selector

    def results(self, target):
        return None

    def results_text(self, target):
        return None


class PyQuerySelector(Selector):
    def results(self, target):
        d = PyQuery(target)
        return d(self.selector)

    def result_text(self, target):
        result = self.results(target)
        return None if not result else result.text()


class XpathSelector(Selector):
    def results(self, target):
        return target.xpath(self.selector)

    def result_text(self, target):
        result = self.results(target)
        # Do your best
        if not result:
            return None
        try:
            return result.text
        except AttributeError:
            return result[0]


class Feed:

    _selectors = {
        'jquery': PyQuerySelector,
        'xpath': XpathSelector,
        'default': PyQuerySelector,
    }

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
        url = url or self.url
        self._raw = requests.get(url)
        self._raw.raise_for_status()

    def parse(self, html=None):
        html = html or self._raw

        parsed = lxml.html.fromstring(html)
        self.properties = self._parse_properties(parsed)
        self.entries = self._parse_entries(parsed)

    def _choose_selector(self, selector_prop):
        # If it's a string, assume default parser
        if isinstance(selector_prop, str):
            # And pass the string as the selector
            return self._selectors['default'](selector_prop)
        else:
            # If it's not, use specified parser and pass 'selector' as the
            # parser
            return self._selectors[
                selector_prop['selector_type']
            ](selector_prop['selector'])

    def _attempt_regex(self, selector_prop, selector_text):
        if isinstance(selector_prop, str):
            return selector_text

        if 'regex' in selector_prop:
            match = re.search(
                selector_prop['regex'],
                selector_text,
            )
            if match:
                selector_text = match.groups('')[0]
        return selector_text

    def _parse_entries(self, htmltree):
        _entries = []
        print("Working on entries")
        config_entries = self.config['entries']

        selectorParser = self._choose_selector(config_entries)

        print("Using selector \"{}\" with selector type {}".format(
            selectorParser.selector,
            selectorParser.__class__.__name__,
        ))

        result_entries = selectorParser.results(htmltree)
        print('Got {} entries'.format(
            len(result_entries)
        ))
        for entry in result_entries:
            print('Working on entry {}'.format(entry))
            tmp_entry = {}
            for property in self._entry_selector_properties:
                if property not in config_entries:
                    continue
                print('Working on prop {}'.format(property))

                selectorParser = self._choose_selector(
                    config_entries[property]
                )
                result_text = selectorParser.result_text(entry)
                result_text = self._attempt_regex(
                    config_entries[property],
                    result_text,
                )
                if property in self._dates:
                    args = {
                        'date_string': result_text,
                        'languages': ['en'],
                    }
                    if 'date_format' in config_entries[property]:
                        args['date_formats'] = [
                            config_entries[property]['date_format'],
                        ]
                    result_text = dateparser.parse(**args)
                tmp_entry[property] = result_text
            _entries.append(tmp_entry)
        return _entries

    def _parse_properties(self, htmltree):
        # Populate properties from selectors
        _properties = {}
        config_props = self.config['properties']
        # Search for each property option
        for property in self._selector_properties:
            if property not in config_props:
                continue

            print('Working on {}'.format(property))

            selectorParser = self._choose_selector(config_props[property])

            print("Using selector \"{}\" with selector type {}".format(
                selectorParser.selector,
                selectorParser.__class__.__name__,
            ))

            result_text = selectorParser.result_text(htmltree)
            print('Found prop value {}'.format(result_text))

            result_text = self._attempt_regex(
                config_props[property],
                result_text,
            )
            if property in self._dates:
                args = {
                    'date_string': result_text,
                    'languages': ['en'],
                }
                if 'date_format' in config_props[property]:
                    args['date_formats'] = [
                        config_props[property]['date_format'],
                    ]
                result_text = dateparser.parse(**args)
            _properties[property] = result_text

        return _properties


if __name__ == '__main__':
    import yaml
    import pprint

    with open('example.yaml', 'r') as f:
        config = yaml.load(f, Loader=yaml.BaseLoader)

    feed = Feed(config['feeds']['example'])

    with open('example.html', 'r') as f:
        html = f.read()

    pp = pprint.PrettyPrinter()
    feed.parse(html)
    print("Properties")
    pp.pprint(feed.properties)
    print("Entries")
    pp.pprint(feed.entries)
