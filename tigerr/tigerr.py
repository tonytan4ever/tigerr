import kivy
kivy.require('1.9.2')
# Uses RecycleView, new in 1.9.2, replacing ListView (deprecated)

from kivy.config import Config
# Comment out this line to develop touch features on a non-touch device
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

Config.set('graphics', 'minimum_width', '500')
Config.set('graphics', 'minimum_height', '400')

import copy
from datetime import datetime as dt
from os.path import join as pjoin
from os.path import expanduser as xpusr
import pickle
from pprint import pprint as pp
import subprocess
import time
import json
from uuid import uuid4
import webbrowser

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ListProperty
from kivy.properties import NumericProperty
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.settings import SettingsWithSidebar

from settings import settings_json

_VERSION = 'beta 0.5'
_T = '%Y-%b-%d %I:%M:%S %p'  # TODO: make configurable
_Q_PATH = '.queries.p'
_PS_PATH = '.patchsets.p'


def _dt_ts(timestamp, strft):
    return dt.fromtimestamp(timestamp).strftime(strft)


def _default_query_cache():
    '''Only needs to be called once on first start'''
    default_queries = [{'qid': str(uuid4()),  # query <-> patchset association
                        'title': 'My Starred',
                        'query': 'is:starred',
                        'alerts': 0
                       },
                       {'qid': str(uuid4()),
                        'title': 'My Watched',
                        'query': 'status:open is:watched',
                        'alerts': 0},
                       {'qid': str(uuid4()),
                        'title': 'My Drafts',
                        'query': 'owner:self is:draft',
                        'alerts': 0
                       }]
    return default_queries


def gerrit_query(port, user, host, keyfile, query, limit=100):
    _sq = query
    if ' limit:' in query:
        # query is already limited, don't set limit: twice
        _limit = ''
    else:
        # IFF no ' limit:' in query, use the 'limit' named arg
        _limit = ' limit:{}'.format(limit)
    # build the query string
    _query = str('gerrit query --all-approvals '
                 '--format=JSON {subquery}{lim}'.format(subquery=_sq,
                                                         lim=_limit))
    proc = subprocess.Popen(['/usr/bin/ssh', '-i', keyfile, '-p', port,
                             '{}@{}'.format(user, host),
                             _query],
                            stdout=subprocess.PIPE)

    # execute the query over ssh (weird, I know)
    x, e = proc.communicate()
    
    results = []
    stats = []

    # build the result dict
    for rr in x.split('\n'):
        if rr:
            _r = json.loads(rr)
            if 'type' in _r:
                if _r['type'] == 'stats':
                    stats = _r
            else:
                if 'id' in _r.keys():
                    _r['gerrit_id'] = _r['id']
                    del _r['id']
                _r['createdOnStr'] = _dt_ts(_r['createdOn'], _T)
                _r['lastUpdatedStr'] = _dt_ts(_r['lastUpdated'], _T)
                _r['owned_by'] = _r['owner']['name']
                try:
                    _r['owner_email'] = _r['owner']['email']
                except KeyError:
                    _r['owner_email'] = ''
                _r['owner_username'] = _r['owner']['username']
                results.append(_r)
    return results, stats


class Tigerr(BoxLayout):
    def __init__(self, **kwargs):
        super(Tigerr, self).__init__(**kwargs)
        self.cache_dir = xpusr(App._running_app.config.get('tigerr',
                                                           'cache_dir'))
        self.unpickle_cache()
        print('Cache restored, got queries: {}'.format(self.q_cache))

    def sort(self):
        # TODO: sorted by time waiting for a review since being verified+1
        self.rv.data = sorted(self.rv.data, key=lambda x: x['createdOn'])

    def pickle_cache(self):
        q = []
        for i in self.queries.data:
            # TODO: elegantly pickle a weakref list(dict())
            q.append(i)
        self._pickle(q, _Q_PATH)
        print('Queries pickled.')
        p = []
        for o in self.patchsets.data:
            p.append(o)
        self._pickle(p, _PS_PATH)
        print('Patchsets pickled.')

    def _pickle(self, the_dict, the_filename):
        pickle.dump(the_dict, open(pjoin(self.cache_dir, the_filename), 'wb'))

    def unpickle_cache(self):
        self.q_cache = self._unpickle(_Q_PATH)
        self.ps_cache = self._unpickle(_PS_PATH)
        self.queries.data = self.q_cache
        self.patchsets.data = self.ps_cache

    def _unpickle(self, the_filename):
        try:
            f = pjoin(self.cache_dir, the_filename)
            print('Loading {}'.format(f))
            return pickle.load(open(f, 'rb'))
        except IOError:
            print('...Unable to load cache, using defaults')
            return _default_query_cache()


class TigerrApp(App):
    # shown in the app titlebar
    title = 'Tigerr - {}'.format(_VERSION)
    
    # weakref to the child object that holds the RecycleViews
    tigerr = ObjectProperty()

    query_queue = ListProperty([])

    banner_message = StringProperty()

    def build(self):
        # Icon file format/size requirements vary from platform to platform.
        # Bug: no app icon ubuntu 16: https://github.com/kivy/kivy/issues/2202
        self.icon = 'icon.png'

        self.settings_cls = SettingsWithSidebar
        # Comment out this line to show kivy settings in the settings panel:
        self.use_kivy_settings = False

        # hold a weakref to the Tigerr instance to manipulate from this class
        self.tigerr = Tigerr()
        self.banner_message = 'Cache restored, Tigerr ready.'

        # initialize the query queue
        for query in self.tigerr.queries.data:
            self.query_queue.append(query)

        # initialize the patchset data structure
        # {{'qid': <qid>, {'gerrit_id': data, ...}}, ...}
        self.ps_data = {}

        # TODO: make query schedule configurable rather than just every 15 sec
        Clock.schedule_interval(self.run_next_query, 15.0)
        return self.tigerr

    def build_config(self, config):
        config.setdefaults('tigerr', {
                'host': 'review.openstack.org',
                'port': 29418,
                'user': 'Jdoe',
                'keyf': xpusr('~/.ssh/id_rsa.pub'),
                'cache_dir': '.'})

    def build_settings(self, settings):
        settings.add_json_panel('tigerr',
                                self.config,
                                data=settings_json)

    def on_config_change(self, config, section, key, value):
        self.banner_message = 'Changed {} to {}'.format(key, value)

    def show_add_query(self, *kwargs):
        p = AddQuery()
        p.open()

    def add_query(self, title, query):
        for q in self.tigerr.queries.data:
            # TODO: handle duplicate queries before submission 
            if query in q.get('query'):
                if title in q.get('title'):
                    m = 'This query is a duplicate of {}'.format(
                        q.get('title'))
                    self.banner_message = m
                    return
                m = 'This query already exists and is titled "{}"'.format(
                    q.get('title'))
                self.banner_message = m
                return
            if title in q.get('title') and not query in q.get('query'):
                m = 'A query with the title "{}" already exists'.format(
                        q.get('title'))
                self.banner_message = m
                return
        u = str(uuid4())
        self.tigerr.queries.data.append({'title': title,
                                         'query': query,
                                         'qid': u})
        self.tigerr.pickle_cache()
        self.banner_message = 'Added query "{}"'.format(title)

    def run_next_query(self, dt):
        # dt is delta time between scheduling and calling
        if len(self.query_queue) == 0:
            print('No queries to run, returning')
            return
        this_query = self.query_queue.pop(0)
        print('Running scheduled query {}'.format(this_query))
        self.banner_message = 'Running query "{}"...'.format(
                this_query['title'])
        q_dat, stats = gerrit_query(self.config.get('tigerr', 'port'),
                                    self.config.get('tigerr', 'user'),
                                    self.config.get('tigerr', 'host'),
                                    self.config.get('tigerr', 'keyf'),
                                    this_query['query'])
        m = 'Query complete, {} rows in {}ms.'.format(
                stats['rowCount'], stats['runTimeMilliseconds'])
        self.banner_message = m
        print(stats)
        self.query_queue.append(this_query)
        print('Updating patchsets with new data...')
        self.update_patchsets(this_query['qid'], q_dat)
        self.tigerr.pickle_cache()

    def update_patchsets(self, qid, new_data):
        # XXX TODO XXX resume here ... 
        for data in new_data:
            self.tigerr.patchsets.data.append(data)

class AddQuery(Popup):
    pass


class QueryError(Popup):
    pass  # TODO


class QueryTest(Popup):
    pass  # TODO show a few sample results from the new query


if __name__ == '__main__':
    TigerrApp().run()
