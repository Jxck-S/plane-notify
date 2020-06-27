# plane-notify
Still WIP Should not use yet. Notify If a Selected Plane has taken off or landed using Python with OpenSky API, outputs location of takeoff location of landing and takeoff by revese lookup of cordinates.

## Required PIP packages
- OpenSky API https://github.com/openskynetwork/opensky-api
- geopy https://github.com/geopy/geopy
- colorama https://github.com/tartley/colorama

### Install OpenSky API
```bash
apt install git 
git clone https://github.com/openskynetwork/opensky-api.git
pip install -e ~/opensky-api/python
```
### Install Colorama and geopy
```bash
pip install colorama
pip install geopy
```
### Install Pushbullet and Tweepy optional output methods already implemented in code
```bash
pip install tweepy
pip install pushbullet.py
```
### Install Screen to run in background
apt install screen
