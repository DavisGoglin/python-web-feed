import re
import dateparser
from pyquery import PyQuery


class SelectorType:
    def __init__(self, selector):
        self.selector = selector

    def result(self, target):
        return None

    def result_text(self, target):
        return None


class PyQuerySelectorType(SelectorType):
    def result(self, target):
        d = PyQuery(target)
        return d(self.selector)

    def result_text(self, target):
        result = self.result(target)
        return None if not result else result.text()


class XpathSelectorType(SelectorType):
    def result(self, target):
        return target.xpath(self.selector)

    def result_text(self, target):
        result = self.result(target)
        if not result:
            return None
        try:
            # Do your best
            return result.text
        except AttributeError:
            return result[0]


_selector_types = {
    'jquery': PyQuerySelectorType,
    'xpath': XpathSelectorType,
    'default': PyQuerySelectorType,
}


class Selector:
    _optional = [
        'regex',
        'date_format',
    ]

    def __init__(self, selector, multiple=False, is_date=False):
        self.options = {}

        if isinstance(selector, str):
            self.selector = selector
            self.SelectorType = _selector_types['default'](self.selector)
        else:
            self.selector = selector['selector']

            for option in self._optional:
                if option in selector:
                    self.options[option] = selector[option]

            if 'selector_type' in selector:
                self.SelectorType = _selector_types[
                    selector['selector_type']
                ](self.selector)
            else:
                self.SelectorType = _selector_types[
                    'default'
                ](self.selector)

        self.multiple = multiple
        self.is_date = is_date

    def result(self, target):
        if self.multiple:
            return self.SelectorType.result(target)

        result_text = self.SelectorType.result_text(target)

        if 'regex' in self.options:
            match = re.search(
                self.options['regex'],
                result_text,
            )
            if match:
                result_text = match.groups('')[0]

        if not self.is_date:
            return result_text

        args = {
            'date_string': result_text,
            'languages': ['en'],
        }
        if 'date_format' in self.options:
            args['date_formats'] = [
                self.options['date_format'],
            ]
        result_text = dateparser.parse(**args)
        return result_text
