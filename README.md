# plane-notify

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/c4e1d839eec3468cadfe351d64dc1ac4)](https://app.codacy.com/manual/Jxck-S/plane-notify?utm_source=github.com&utm_medium=referral&utm_content=Jxck-S/plane-notify&utm_campaign=Badge_Grade_Settings)
[![GPLv3 License](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://opensource.org/licenses/)

Notify if configured planes have taken off or landed using Python with OpenSky(free) or ADS-B Exchange Data(paid but much better), outputs location of takeoff location of landing and takeoff by a reverse lookup of coordinates.

### Discord Output Example

![Discord Output Example](./ExImages/DiscordEX.png?raw=true)

#### More examples are in  the ExImages folder

[ExImages](./ExImages)

### Background

I made this program so I could track Elon Musk's Jet and share with others of his whereabouts on Twitter. [![Twitter Follow](https://img.shields.io/twitter/follow/ElonJet.svg?style=social)](https://twitter.com/ElonJet) I have now Expanded and run multiple accounts for multiple planes, a list of the accounts here [plane-notify Twitter List](https://twitter.com/i/lists/1307414615316467715)

### Contributing

 I'm open to any help or suggestions, I realize theirs much better ways I'm sure to do a lot of my methods, I'm only a noob. I'll accept pull requests. If you'd like to discuss join <https://JacksTech.net/Discord>

### [Algorithm](PseudoCode.md)

## Setup / Install

### Make sure Python/PIP is installed

```bash
apt update
apt install python3
apt install python3-pip
```

### Install Pipenv and Dependencies

```bash
pip install pipenv
pipenv install
```

### Install Selenium / ChromeDriver or setup Google Static Maps

Selenium/ChromeDriver is used to take a screenshot of the plane on globe.adsbexchange.com. Or use Google Static Maps, which can cost money if overused(No tutorial use <https://developers.google.com/maps/documentation/maps-static/get-api-key> to get to a key).

#### Chromium

```bash
sudo apt-get install chromium
```
These output methods once installed can be configured in the planes config you create, using the example plane1.ini

### Install Screen to run in the background

```bash
apt install screen
```

### Download / Clone

```bash
apt install git
git clone -b multi --single-branch https://github.com/Jxck-S/plane-notify.git
cd plane-notify
```

### Configure main config file with keys and URLs (mainconf.ini) in the configs directory

-   edit them with nano or vi on the running machine or on your pc and transfer the config to where you will be running the bot
-   Pick between OpenSky and ADS-B Exchange
-   The OpenSky API is free for everyone but the data is not as good as ADS-B Exchange. The ADS-B Exchange API is not free and this program will not work for the Rapid API from ADS-B Exchange. It only works with the API that they give when you have a partnership with ADS-B Exchange. It is not cheap to get the ADS-B Exchange full API, Don't contact them unless you are ready to pay. 
-   If you'd like to add support for ADS-B Exchanges RapidAPI feel free to work on it and submit a merge request. 
-   If you've set up multiple planes and want to use ADSB Exchange as your source you must have /all endpoint access to their API or it won't work.
-   Pick the correct API version for ADS-B Exchange.
-   Proxy is if your running multiple programs that use the ADSB Exchange, setup the proxy from lemonodor so you don't abuse the ADSB Exchange API, otherwise leave enable false.
-   When using OpenSky there's more bugs because I mainly use ADS-B Exchange and work less on the OpenSky Implementation. 

### Configure individual planes

-   an example file is given (plane1.ini) plane config files should be in the configs directory, the program looks for any file in that folder with a .ini extension.
-   each plane should have its own config

### Enter and create a new Screen Session

```bash
screen -R <name screen whatever you want>
```

### Start Program

```bash
pipenv run python __main__
```

## Using with Docker

Install [docker from their website](https://docs.docker.com/get-docker/). Run the following command from the root of the project.

```bash
docker-compose up -d
```

After running this command, dut to the `-d` flag the container will be running in the background. To see the logs of the docker 

### TODO

-   General Cleanup
-   Restructure project to make it proper currently random files because I didn't know how to properly structure a project before. (in progress)
-   Add proper logging and service to run the program and remove excessive printing.
-   Better single config YAML, or DB maybe

### [More References/Documentation](Refrences.md)
