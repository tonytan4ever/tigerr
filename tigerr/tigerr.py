import kivy
kivy.require('1.9.2')
# Uses RecycleView, new in 1.9.2, replacing ListView (deprecated)

from kivy.config import Config
# Comment out this line to develop touch features on a non-touch device
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

Config.set('graphics', 'minimum_width', '400')
Config.set('graphics', 'minimum_height', '400')


from datetime import datetime as dt
from os.path import join as pjoin
from os.path import expanduser as xpusr
import pickle
from pprint import pprint as pp
import subprocess
import json
from uuid import uuid4
import webbrowser

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.settings import SettingsWithSidebar

from settings import settings_json

_VERSION = 'beta 0.4'
_T = '%Y-%b-%d %I:%M:%S %p'  # TODO: make configurable
_Q_PATH = '.tigerr_queries.p'
_PS_PATH = '.tigerr_patchsets.p'


def _dt_ts(timestamp, strft):
    return dt.fromtimestamp(timestamp).strftime(strft)


def _default_query_cache():
    '''Only needs to be called once on first start'''
    default_queries = [{'qpid': str(uuid4()),  # query <-> patchset association
                        'title': 'My Starred',
                        'query': 'is:starred',
                        'alerts': 0},
                       {'qpid': str(uuid4()),
                        'title': 'My Watched',
                        'query': 'status:open is:watched',
                        'alerts': 0},
                       {'qpid': str(uuid4()),
                        'title': 'My Drafts',
                        'query': 'owner:self is:draft',
                        'alerts': 0}]
    return default_queries


def gerrit_query(port, user, host, keyfile, query, limit):
    _sq = query
    _query = str('gerrit query --all-approvals '
                 '--format=JSON {subquery} limit:{lim}'.format(subquery=_sq,
                                                               lim=limit))
    proc = subprocess.Popen(['/usr/bin/ssh', '-i', keyfile, '-p', port,
                             '{}@{}'.format(user, host),
                             _query],
                            stdout=subprocess.PIPE,
                            )
    x, e = proc.communicate()
    results = []
    stats = []
    for rr in x.split('\n'):
        if rr:
            _r = json.loads(rr)
            if 'type' in _r:
                if _r['type'] == 'stats':
                    stats = _r
            else:
                _r['createdOnStr'] = _dt_ts(_r['createdOn'], _T)
                _r['lastUpdatedStr'] = _dt_ts(_r['lastUpdated'], _T)
                _r['owned_by'] = _r['owner']['name']
                _r['owner_email'] = _r['owner']['email']
                _r['owner_username'] = _r['owner']['username']
                results.append(_r)
    pp(results)
    return results, stats


class Tigerr(BoxLayout):
    def __init__(self, **kwargs):
        super(Tigerr, self).__init__(**kwargs)
        self.cache_dir = xpusr(App._running_app.config.get('tigerr',
                                                           'cache_dir'))
        self.unpickle_cache()
        print('Cache restored, got queries: {}'.format(self.q_cache))
        self.queries.data = self.q_cache

    def execute_query(self, query, limit):
        config = App._running_app.config
        port = config.get('tigerr', 'port')
        user = config.get('tigerr', 'user')
        host = config.get('tigerr', 'host')
        key = config.get('tigerr', 'keyf')
        q_dat, stats = gerrit_query(port, user, host, key, query, limit)
        self.patchsets.data = self.update_cache(ps_dat, self.ps_cache)
        print(stats)

    def update_cache(self, query_data, cache):
        for record in query_data:
            # record['id'] is the 'I57458722234...' string identifier in a PS
            if record['id'] in cache.keys():
                cache[record['id']] = record
            else:
                cache.update({record['id']: record})
        return cache

    def sort(self):
        self.rv.data = sorted(self.rv.data, key=lambda x: x['createdOn'])

    def insert(self, value):
        self.rv.data.insert(0, {'value': value or 'default value'})

    def update(self, value):
        if self.rv.data:
            self.rv.data[0]['value'] = value or 'default new value'
            self.rv.refresh_from_data()

    def remove(self):
        if self.rv.data:
            self.rv.data.pop(0)

    def pickle_cache(self):
        self._pickle(self.q_cache, _Q_PATH)
        self._pickle(self.ps_cache, _PS_PATH)

    def _pickle(self, the_dict, the_filename):
        pickle.dump(the_dict, open(pjoin(self.cache_dir, the_filename), 'wb'))

    def unpickle_cache(self):
        self.q_cache = self._unpickle(_Q_PATH)
        self.ps_cache = self._unpickle(_PS_PATH)

    def _unpickle(self, the_filename):
        try:
            return pickle.load(open(pjoin(self.cache_dir, the_filename), 'rb'))
        except IOError:
            return _default_query_cache()


class TigerrApp(App):
    title = 'Tiger - {}'.format(_VERSION)
    def build(self):
        # Icon file format/size requirements vary from platform to platform.
        # Bug: no app icon ubuntu 16: https://github.com/kivy/kivy/issues/2202
        self.icon = 'icon.png'
        self.settings_cls = SettingsWithSidebar
        self.use_kivy_settings = False
        return Tigerr()

    def build_config(self, config):
        config.setdefaults('tigerr', {
                'host': 'review.openstack.org',
                'port': 29418,
                'user': 'Jdoe',
                'keyf': '~/.ssh/id_rsa.pub',
                'cache_dir': '~/.tigerr'})

    def build_settings(self, settings):
        settings.add_json_panel('tigerr',
                                self.config,
                                data=settings_json)

    def on_config_change(self, config, section, key, value):
        print((config, section, key, value))


if __name__ == '__main__':
    TigerrApp().run()
