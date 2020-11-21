### How It works
-   Takes data about every ~30 seconds from OpenSky Network or ADS-B Exchange and compares it to previous data with what I've defined as a landing or takeoff event.
-   A takeoff event is the plane is not on the ground, below 10k feet and ((previously no data and now getting data) or was previously on the ground).
-   A landing event is previously below 10k feet and (previously getting data, no longer getting data and previously not on the ground) or (now on the ground and previously not on the ground).
-   Given the coordinates of the aircraft the coordinates are reverse looked up for a location name. (GeoPY Nomination Geolocator)
-   At the time of takeoff a takeoff time is set, which is referenced in the landing event to calculate approximate total flight time.
-   A Static map image is created based off location name. (Google Static Maps API) or a screenshot of <https://global.adsbexchange.com/> is created using Selenium/ChromeDriver The selected plane is locked on in the screenshot.
-   If the landing event and takeoff events are true, It will output to any of the following built-in output methods. (Twitter, Pushbullet, and Discord all of which can be setup and enabled in each planes config file. Outputs the location name, map image and flight time on landing. (Tweepy and "Pushbullet.py" and Discord_webhooks)