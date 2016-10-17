#!/usr/bin/env python3


import json

settings_json = json.dumps([
    {'type': 'title',
     'title': 'Gerrit settings'},

    {'type': 'string',
     'title': 'Gerrit hostname',
     'desc': 'ex: review.openstack.org',
     'section': 'gerrit',
     'key': 'host'},

    {'type': 'numeric',
     'title': 'Gerrit port',
     'desc': 'ex: 29418',
     'section': 'gerrit',
     'key': 'port'},

    {'type': 'string',
     'title': 'Gerrit username',
     'desc': 'Your Gerrit ssh username, ex: Jdoe',
     'section': 'gerrit',
     'key': 'user'}])
