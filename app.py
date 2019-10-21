from flask import Flask, escape, request, abort, make_response
import yaml
from feedgen.feed import FeedGenerator
from feed import Feed
import pytz

app = Flask(__name__)

with open('example.yaml', 'r') as f:
    config = yaml.load(f, Loader=yaml.BaseLoader)

timezone = pytz.timezone(config['timezone'])


def _round_date(dt, rounding):
    if rounding == 'day':
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif rounding == 'hour':
        return dt.replace(minute=0, second=0, microsecond=0)
    else:
        raise Exception


@app.route('/')
def hello():
    name = request.args.get("name", "World")
    return 'Hello, {}!'.format(escape(name))


@app.route('/<feed_name>')
def display_feed(feed_name):
    if feed_name not in config['feeds']:
        abort(404)

    f = Feed(config['feeds'][feed_name])
    f.load()
    f.parse()

    fg = FeedGenerator()

    fg.id(f.url)
    fg.title(
        f.properties.get('title', feed_name)
    )
    fg.author(
        f.properties.get('author', '')
    )
    fg.updated(
        timezone.localize(
            _round_date(
                max(
                    [e['updated'] for e in f.entries]
                ), config['date_rounding']
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
                    entry['updated'], config['date_rounding']
                )
            )
        )
    atomfeed = fg.atom_str()

    resp = make_response(atomfeed)
    resp.headers['content-type'] = 'application/xml'
    return resp
