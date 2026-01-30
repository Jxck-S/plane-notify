> [!IMPORTANT]
> **Major Refactor and Cleanup**
> This commit marks the beginning of a major refactor and cleanup of the codebase.


# plane-notify

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/c4e1d839eec3468cadfe351d64dc1ac4)](https://app.codacy.com/manual/Jxck-S/plane-notify?utm_source=github.com&utm_medium=referral&utm_content=Jxck-S/plane-notify&utm_campaign=Badge_Grade_Settings)
[![GPLv3 License](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://opensource.org/licenses/)

Notify if configured planes have taken off or landed using Python with ADS-B data, outputs location of takeoff location of landing and takeoff by reverse lookup of coordinates.

### Discord Output Example

![Discord Output Example](./ExImages/DiscordEX2.png?raw=true)

#### More examples are in  the ExImages folder

[ExImages](./ExImages)

### Background

I made this program so I could track Elon Musk's Jet and share his whereabouts with others orginally on Twitter (but now suspended, but now also on other platforms). I have now expanded and run multiple accounts for multiple planes, a list of the accounts can be found here <https://grndcntrl.net/links>

### Contributing

I'm open to any help or suggestions, I realize there are many better ways to improve this program and better ways to get this program to work properly, I'm only a noob. I'll accept pull requests. If you'd like to discuss join <https://grndcntrl.net/discord>

### [Algorithm](PseudoCode.md)

## Setup / Install
- Install using the following steps or use Docker, scroll down to the Docker section.

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

Selenium/ChromeDriver is used to take a screenshot of the plane on globe.theairtraffic.com. Or use Google Static Maps, which can cost money if overused(No tutorial use <https://developers.google.com/maps/documentation/maps-static/get-api-key> to get to a key).

#### Chrome 
- This is assuming linux/debian
```bash
curl -sSL https://dl-ssl.google.com/linux/linux_signing_key.pub  | apt-key add 
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list
apt update
apt install google-chrome-stable
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

-   Copy `mainconf.ini.example` to `mainconf.ini` andCopy `plane1.ini.example` to `plane1.ini`. `plane1.ini` can change names as long as it ends with the ini extension
-   Edit them with nano or vi on the running machine or on your pc and transfer the config to where you will be running the bot



### Configure individual planes

-   An example file is given (plane1.ini) plane config files should be in the configs directory, the program looks for any file in that folder with a .ini extension.
-   Each plane should have its own config

### Enter and create a new Screen Session

```bash
screen -R <name screen whatever you want>
```

### Start Program

```bash
pipenv run python __main__.py
```

## Using with Docker

Install [docker from their website](https://docs.docker.com/get-docker/). Run the following command from the root of the project.

```bash
docker-compose up -d
```

After running this command, due to the `-d` flag the container will be running in the background. To see the logs of the docker container use `docker logs CONTAINER` (add `-f` to continue streaming the containers output)

### Telegram message feature - march/2022

Data obtained can be sent through Telegram to a chat (contact), channel or groups.

Creating a Telegram Bot
-   Start a conversation with [BotFather](https://t.me/BotFather);
-   Send it to the BotFather: /newbot
-   Choose a name for your bot;
-   Choose a username for your bot;
-   Done! You'll get a token to access the HTTP API.

Getting channel or chat (contact) ID
-   Start a conversation with [JsonDumpBot](https://t.me/JsonDumpBot);
-   It will reply with a json with information from the message;
-   Go to the channel or chat you want the id and forward a message from there to JsonDumpBot;
-   Find the id in the reply. It'll look something like this:
```bash
   {...
    "forward_from_chat": {
          "id": xxxxxxxxx,
   ...}
```
-   Don't forget to add the bot as admin in channel so messages can be sent.

Getting a group ID
-   Open [Telegram web](https://web.telegram.org);
-   Go to group and check the url on address bar of browser;
-   That's the group ID (-xxxxxxxxx), it'll look something like this:
```bash
  https://web.telegram.org/z/#-xxxxxxxxx
```

### TODO

-   General Cleanup
-   Restructure project to make it proper currently random files because I didn't know how to properly structure a project before. (in progress)
-   Add proper logging and service to run the program and remove excessive printing.
-   Better single config YAML, or DB maybe

### [More References/Documentation](References.md)
