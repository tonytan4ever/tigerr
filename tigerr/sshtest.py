#!/usr/bin/env python3

import subprocess
from pprint import pprint as pp
import json

q = '''ssh -p 29418 JPerkins@review.openstack.org \
gerrit query --format=JSON status:open project:openstack/neutron limit:2'''

proc = subprocess.Popen(q.split(),
                        stdout=subprocess.PIPE,
                        )
x, e = proc.communicate()
results = []
stats = None
for rr in x.split('\n'):
    if rr:
        _r = json.loads(rr)
        if 'type' in _r:
            if _r['type'] == 'stats':
                stats = _r
        else:
            results.append(_r)
pp(results)
pp(stats)
