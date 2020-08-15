# plane-notify

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/c4e1d839eec3468cadfe351d64dc1ac4)](https://app.codacy.com/manual/Jxck-S/plane-notify?utm_source=github.com&utm_medium=referral&utm_content=Jxck-S/plane-notify&utm_campaign=Badge_Grade_Settings)
[![GPLv3 License](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://opensource.org/licenses/)

Notify If a Selected Plane has taken off or landed using Python with OpenSky or ADS-B Exchange Data, outputs location of takeoff location of landing and takeoff by reverse lookup of coordinates.

## Why I made it

Made it so I could track Elon Musk's Jet and share with others of his whereabouts on Twitter. [![Twitter Follow](https://img.shields.io/twitter/follow/ElonJet.svg?style=social)](https://twitter.com/ElonJet)

## How It works

-   Takes data about every 15 seconds from OpenSky Network or ADS-B Exchange and compares it to previous data with what I've defined as a landing or takeoff event.

-   A takeoff event is the plane is not on the ground, below 10k feet and ((previously no data and now getting data) or was previously on the ground).

-   A landing event is previously below 10k feet and (previously getting data, no longer getting data and previously not on the ground) or (now on the ground and previously not on the ground).

-   Given the coordinates of the aircraft the coordinates are reverse looked up for a location name. (GeoPY Nomination Geolocator)

-   At the time of takeoff a takeoff time is set, which is referenced in the landing event to calculate approximate total flight time.

-   A Static map image is created based off location name. (Google Static Maps API) or a screenshot of <https://global.adsbexchange.com/> is created using Selenium/ChromeDriver The selected plane is locked on in the screenshot.

-   If the landing event and takeoff events are true, It will output to any of the following built-in output methods. (Twitter, Pushbullet, and Discord all of which can be setup and enabled in config.ini). Outputs the location name, map image and takeoff time if landing. (Tweepy and "Pushbullet.py" and Discord_webhooks)

## Required PIP packages

-   OpenSky API <https://github.com/openskynetwork/opensky-api> (If using OpenSky, which is default and anybody can use)

-   geopy <https://github.com/geopy/geopy>

-   colorama <https://github.com/tartley/colorama>

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

### Install Pushbullet, Tweepy, and Discord optional output methods already implemented in code

```bash
pip install tweepy
pip install pushbullet.py
pip install discord_webhooks
```

Configure these methods of output in config.ini

### Install Screen to run in the background

```bash
apt install screen
```

### Make sure Python is installed

```bash
apt install python3
```

### Download / Clone

```bash
git clone https://github.com/Jxck-S/plane-notify.git
cd plane-notify
```

### Configure config file with keys and URLs (config.ini)

-   edit them with nano or vi on the running machine or on your pc and transfer the config to where you will be running the bot

### Enter and create new Screen Session

```bash
screen -R <name screen whatever you want>
```

### Start Program

```bash
python3 NotifyBot.py
```

### TODO

Move the lookup location of coordinates so that it only rungs when landing or takeoff occurs. So then Geopy/Nomination API is called less

Implement airport name, done by closest airport

#### Refrences

-   <https://opensky-network.org/apidoc/>
-   <https://geopy.readthedocs.io/en/stable/>
-   <https://www.geeksforgeeks.org/python-get-google-map-image-specified-location-using-google-static-maps-api/>
-   <https://realpython.com/twitter-bot-python-tweepy/>
-   <https://github.com/rbrcsk/pushbullet.py>
