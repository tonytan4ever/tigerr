import kivy
kivy.require('1.9.2')
# Uses RecycleView, new in 1.9.2, replacing ListView (deprecated)

from random import sample
from string import ascii_lowercase
import webbrowser  # TODO: click on review row to open in browser

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.settings import SettingsWithSidebar

from settings import settings_json


class Tigerr(BoxLayout):

    def populate(self):
        # TODO: get from gerrit (ssh u@d.com -p 123 gerrit query)       
        self.rv.data = [{'value': ''.join(sample(ascii_lowercase, 6))}
                        for x in range(50)]

    def sort(self):
        self.rv.data = sorted(self.rv.data, key=lambda x: x['value'])

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
                '': True})

    def build_settings(self, settings):
        settings.add_json_panel('Tigerr',
                                self.config,
                                data=settings_json)

    def on_config_change(self, config, section, key, value):
        print((config, section, key, value))

if __name__ == '__main__':
    TigerrApp().run()
