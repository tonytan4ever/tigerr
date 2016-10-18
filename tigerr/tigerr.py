import kivy
kivy.require('1.9.2')
# Uses RecycleView, new in 1.9.2, replacing ListView (deprecated)

from random import sample
from string import ascii_lowercase
import subprocess
import json
import webbrowser  # TODO: click on review row to open in browser

from kivy.app import App
from kivy.lang import Builder
from kivy.config import Config
from kivy.properties import NumericProperty
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.settings import SettingsWithSidebar

from settings import settings_json


class Tigerr(BoxLayout):
    def populate(self):
        p = Config.get('gerrit', 'port')
        u = Config.get('gerrit', 'user')
        h = Config.get('gerrit', 'host')
        _l = 10 
        query = 'ssh -p {p} {u}@{h} gerrit query --format=JSON {q} limit:{l}'
        _sq = 'status:open project:openstack/neutron'
        proc = subprocess.Popen(query.format(p=p,u=u,h=h,q=_sq,_l=10).split(),
                                stdout=subprocess.PIPE)
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
                    results.append(_r)
        self.rv.data = results

    def sort(self):
        self.rv.data = sorted(self.rv.data, key=lambda x: x[''])

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
                'user': 'Jdoe'})

    def build_settings(self, settings):
        settings.add_json_panel('gerrit',
                                self.config,
                                data=settings_json)

    def on_config_change(self, config, section, key, value):
        print((config, section, key, value))


if __name__ == '__main__':
    TigerrApp().run()
