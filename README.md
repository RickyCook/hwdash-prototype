hwdash-prototype
================

Prototype for getting hwinfo data into D3

This should be pretty easy to get running on Linux (and only Linux I think). You should install `hwinfo` (debian is `apt-get install hwinfo`) and Python 2.7. Other than that, no special requirements...

Just run `./main.py` and hit http://localhost:8000 in a web browser.

You can easily make queries against the JSON API: `/api/all.json` and you can also filter by hardware type: `/api/network.json`, `/api/disk.json`. To filter like this in the HTML interface, simply do the same but with `.htm` extension. For example, `/disk.htm`

Link love for http://mbostock.github.io/d3/talk/20111018/tree.html because I pretty much entirely lifted the D3 code from there (for now).
