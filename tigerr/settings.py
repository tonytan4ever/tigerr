#!/usr/bin/env python3


import json

settings_json = json.dumps([
    {'type': 'title',
     'title': 'Gerrit Settings'},

    {'type': 'string',
     'title': 'Hostname',
     'desc': 'ex: review.openstack.org',
     'section': 'tigerr',
     'key': 'host'},

    {'type': 'numeric',
     'title': 'Port',
     'desc': 'ex: 29418',
     'section': 'tigerr',
     'key': 'port'},

    {'type': 'string',
     'title': 'User Name',
     'desc': 'Your Gerrit ssh user name, ex: Jdoe',
     'section': 'tigerr',
     'key': 'user'},
    
    {'type': 'path',
     'title': 'SSH keyfile',
     'desc': 'Your Gerrit ssh keyfile location, ex: ~/.ssh/id_rsa.pub',
     'section': 'tigerr',
     'key': 'keyf'},
    
    {'type': 'title',
     'title': 'Tigerr Settings'},

    {'type': 'path',
     'title': 'Cache directory',
     'desc': 'Directory for persisting data, ex: ~/.tigerr',
     'section': 'tigerr',
     'key': 'cache_dir'}

    ])
