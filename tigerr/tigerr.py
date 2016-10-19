import kivy
kivy.require('1.9.2')
# Uses RecycleView, new in 1.9.2, replacing ListView (deprecated)

from datetime import datetime as dt
from pprint import pprint as pp
import subprocess
import json
import webbrowser

from kivy.app import App
from kivy.lang import Builder
from kivy.config import Config
from kivy.properties import NumericProperty
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.settings import SettingsWithSidebar

from settings import settings_json


def gerrit_query(port, user, host, keyfile, query,limit):
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
                _r['createdOnStr'] = dt.fromtimestamp(
                        _r['createdOn']).strftime('%Y-%b-%d %I:%M:%S %p')
                _r['lastUpdatedStr'] = dt.fromtimestamp(
                        _r['lastUpdated']).strftime('%Y-%b-%d %I:%M:%S %p')
                _r['owned_by'] = _r['owner']['name']
                _r['owner_email'] = _r['owner']['email']
                _r['owner_username'] = _r['owner']['username']
                results.append(_r)
    pp(results)
    return results, stats


class Tigerr(BoxLayout):
    def populate(self, q, l):
        print(q)
        print(l)
        config = App._running_app.config
        p = config.get('gerrit', 'port')
        u = config.get('gerrit', 'user')
        h = config.get('gerrit', 'host')
        k = config.get('gerrit', 'keyf')
        self.rv.data, stats = gerrit_query(p, u, h, k, q, l)
        print(stats)

    def sort(self):
        self.rv.data = sorted(self.rv.data, key=lambda x: x['createdOn'])

    def clear(self):
        self.rv.data = []

    def insert(self, value):
        self.rv.data.insert(0, {'value': value or 'default value'})

    def update(self, value):
        if self.rv.data:
            self.rv.data[0]['value'] = value or 'default new value'
            self.rv.refresh_from_data()

    def remove(self):
        if self.rv.data:
            self.rv.data.pop(0)


class TigerrApp(App):
    def build(self):
        self.settings_cls = SettingsWithSidebar
        self.use_kivy_settings = False
        return Tigerr()

    def build_config(self, config):
        config.setdefaults('gerrit', {
                'host': 'review.openstack.org',
                'port': 29418,
                'user': 'Jdoe',
                'keyf': '~/.ssh/id_rsa.pub'})

    def build_settings(self, settings):
        settings.add_json_panel('gerrit',
                                self.config,
                                data=settings_json)

    def on_config_change(self, config, section, key, value):
        print((config, section, key, value))


if __name__ == '__main__':
    TigerrApp().run()
