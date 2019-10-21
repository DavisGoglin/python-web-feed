from flask import Flask, request, abort, make_response
import yaml
from feedgen.feed import FeedGenerator
from feed import Feed
import pytz
from os import environ

_generator = {
    'generator': 'python-web-feed',
    'version':   '0.1',
    'uri':       'https://github.com/DavisGoglin/python-web-feed',
}

app = Flask(__name__)

config_file = environ.get('PY_WEB_FEED_CONFIG', 'example.yaml')
with open(config_file, 'r') as f:
    config = yaml.load(f, Loader=yaml.BaseLoader)

timezone = pytz.timezone(config['timezone'])


def _round_date(dt, rounding):
    if rounding == 'day':
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif rounding == 'hour':
        return dt.replace(minute=0, second=0, microsecond=0)
    elif rounding == 'none' or rounding is None:
        return dt
    else:
        raise Exception


@app.route('/')
def hello():
    return 'Hello, World!'


@app.route('/<feed_name>')
def display_feed(feed_name):
    if feed_name not in config['feeds']:
        abort(404)

    f = Feed(config['feeds'][feed_name])
    f.load()
    f.parse()

    fg = FeedGenerator()

    fg.generator(**_generator)
    fg.id(
        request.base_url
    )
    fg.link(
        href=request.base_url,
        rel='self',
    )
    fg.title(
        f.properties.get('title', feed_name)
    )
    fg.author(
        name=f.properties.get('author', '')
    )
    fg.updated(
        timezone.localize(
            _round_date(
                max(
                    [e['updated'] for e in f.entries]
                ), config.get('date_rounding', None)
            )
        )
    )

    for entry in f.entries:
        fe = fg.add_entry()
        fe.id(entry['url'])
        fe.title(entry['title'])
        fe.link(href=entry['url'])
        fe.updated(
            timezone.localize(
                _round_date(
                    entry['updated'], config.get('date_rounding', None)
                )
            )
        )
        fe.content(entry['content'])
    atomfeed = fg.atom_str()

    resp = make_response(atomfeed)
    resp.headers['content-type'] = 'application/xml'
    return resp
