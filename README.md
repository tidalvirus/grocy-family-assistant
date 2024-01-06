# grocy-family-assistant

Use NiceGUI, requests, and of course Grocy to try and create a slightly more family friendly view for tracking chores

Steps to use:
* Clone repo
* copy env.sample to .env
* edit .env
* python3 -m venv .venv
* source .venv/bin/activate
* pip3 install -r requirements.txt
* python3 chores_nicesgui.py

Current status: Works well enough for my use - which is for users that probably wouldn't use Grocy's own UI. And this works better on a shared tablet device, and is good enough to use on a phone too. Code isn't pretty, but it seems to work.

Example view of the app:

![Screenshot](/screenshot.png?raw=true "Screenshot")
