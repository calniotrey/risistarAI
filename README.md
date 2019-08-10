# risistarAI
Code that play Risistar (a Ogame-like game based on 2-Moons) automatically.
In this section you will find informations about setup, configuration, startup and troubleshooting.
In the next section, you will find informations for developers about the internal working of the AI.

## Requirements :
Python 3 (3.6 should be fine)
BeautifulSoup 4 (pip install beautifulsoup4)

## Configuration :
### First step : Login credentials
You need to specify your credentials in a secret.txt (or modify the code, but be careful not to upload your credentials)
First line : username (no "usernameHere" nor username=usernameHere)
Second line : password (yes in clear)
Then you can write some other informations (like the email used and so on), it won't be used
**NEVER UPLOAD/SHARE secret.txt !!!**

### Second step : Configure the AI
To do that, copy the file 'defaulConfig.txt' to a file named 'config.txt'.
Open that file with your favorite text editor and change the settings (more info on the features in next sub-section).
You *can* upload and share the 'config.txt' **IF YOU DON'T HAVE THE DISCORD PING ENABLED**
We highly recommend to keep the 'defaultConfig.txt' alongside your 'config.txt'.
The AI first loads the 'defaultConfig.txt' and overrides it with the 'config.txt'.
That way, if a needed settings from a newer version is needed but is missing from 'config.txt', the AI will fall back to the one from 'defaultConfig.txt', preventing some errors. It is useful so you can keep the same 'config.txt' when updating.

### Third Step : Set the game language in French
Sadly this was developed for and by French users. So we used the French settings.
Maybe in the future we will implement ways to make the AI language independent, but not in the near future.

## Features
### AutoBuild
The AI will build on all your planets (not on the moons) following a building plan configurable with 'config.txt'.
It will only build mines, solar plant, hangars and robot factory.

In the future, we plan to make the AI build all the types of buildings and follow different build orders (a research planet, several mining planets ...).
Additionally, we are thinking about allowing the AI to send resources between planets to speed up the constructions (currently all planets are independent).

### customBuildOrder
The AI will follow a custom build order instead of the default build decisions.
By setting `useDefaultBuildPlanWhenEmpty=True` in the build order file, it will fall back to the default build decisions when all buildings specified by the custom build order are built.
You can add more custom build orders in the folder (which name is defined in the configurations files).
Do not use an "=" in the name of a custom build order file (everything else *should* be ok).
The AI will give each planet a custom build order according to the planet name.
To specify which planet name should add which custom build order, you can alter the `customBuildOrdersPairingFile.txt` (name of the file defined in the configuration).
**DO NOT** add buildings before the needed buildings/researchs/officers for it are taken.

In the future, we plan to add a check if the building is buildable (ie. if the buildings/researchs/officiers it needs are taken).
Additionally, we are thinking about adding a settings which will allow if the current building isn't buildable to build the next one instead.

### AutoFleetScan
The AI will scan all fleets. When an incoming enemy attacking fleet is detected, it will log it.
Please leave a high time between scans (at least 30 seconds, 1 minute is better).

In the future we plan to scan fleets for your whole alliance.

### DefenderDiscordPing
If this feature and AutoFleetScan is enabled, whenever an enemy attacking fleet is detected, the AI will ping a user on a discord channel.
For this you need to have a discord server with administrative rights.
Then create a webhook (**DO NOT SHARE IT**).
Then copy the id of the user to ping (go to settings > display > activate developer mode > right click on a user and copy id).
You can customize a message.

In the future, we plan to give you an option to ping when a ally is being attacked (when the scan works for you allies).

### AutoEvasion
If this feature and AutoFleetScan is enabled, whenever an enemy attacking fleet is detected, the AI will send your fleet to a configured location.
The fleet will take all available resources (deuterium then crystal then metal).
The AI will build some transporters with the rest and spend the rest in defenses.
The fleet is sent before the attack hits, but not if the attack is to fast (by a spying probe for example).
Then, if no enemy fleet is incoming, it will turn the evading fleet back.

In the future, we want to only evade dangerous fleets (currently a single cruiser would make you evade despite your defenses).
Additionally, we want to allow more evading destinations, and possibly taunting messages to be sent (to simulate human activity).

## Updating :
Just pull the master branch. Then, you may need to change your settings from 'config.txt' to enable new features.
You can see what new settings are available by looking at the 'defaultConfig.txt'.

## Startup :
Place yourself in the folder containing 'start.py', open a terminal and type :
`python start.py`
or
`python3 start.py`

Alternatively, you can launch 'start.py' from a python IDE. Just make sure to launch it from the same folder (else the imports won't work).

## Troubleshooting :
### Logging :
First of, the AI logs a lot of stuff. Most of it is just information so you can see what it is doing.
The logging function logs with the following format :
`hh:mm:ss [PLANET_ID] String`
1. `hh:mm:ss` : Obviously the time at the moment the AI logged this line.
2. `PLANET_ID` : Either a number, which indicates one of your planets, or a blank space which indicates that it is independent of a planet (logins, ...).
3. `String` : A string which indicates the problem or the information logged. All time is indicated in seconds (543 is 9 minutes 3 seconds).

### Logging of errors :
The majority of the logs just give information about what the AI is doing (what it is building, when an enemy fleet is detected or evaded ...).
However, sometimes some error message can be found in it. Here are a few of them and how to solve them:

#### Configuration errors :
If the AI terminates just after launch, there is probably a problem with your configuration.
If there is just an error such as "File not found", make sure 'secret.txt' and 'config.txt' exists and are in the same folder as 'risistar.py'.
If the error persists, make sure you are launching 'start.py' from the folder containing it.
If "Bad configuration !" is printed, it means your configuration isn't coherent. There will be another printed string before it which will indicates how to solve it.
Other errors :
  * `Login/Password incorrect` : Your credentials are incorrect (make sure the domain in the config is the right one)
  * `Bad Cookie. Clearing session cookies and trying to reconnect using credentials` : You were disconnected or used a bad cookie and the AI will login. Not an error.
  * `No more building planned by the custom build order !` : You are using a custom build order and it doesn't fall back to the default build when all the buildings are built. You can fix this by setting `useDefaultBuildPlanWhenEmpty=True`

#### Errors you can't do much about :
In this case just send us your logs and a few informations (such as if you were doing things on the game alongside the AI).
**DO NOT SEND US CREDENTIALS OR COOKIE CONTENT**
List of such errors :
  * `No more tasks ! ALERT` (the AI doesn't have anything to do, shouldn't happen)
  * `ERROR LOL` (Error while evading an ennemy fleet. A lot can go wrong here. Just make sure to check your discord settings if enabled)
  * `Erreur lors de l'annulation` (Error while sending back an evading fleet, shouldn't happen)
  * `Error while sending the fleet` (Error while sending a fleet. It can happen when sending 0 ships. Isn't noteworthy if there was no ships left)

# Developer part : Internal working of the AI
First off, there isn't really an AI in this code. The only part with decision making is when choosing the building to be built. And that is just some ifs.
However, I chose to still label it as an AI for two reasons. First one, it is an artificial intelligence for a game. It doesn't require it to be evolved, only to work. Secondly, why not ? :P

## Classes :
IA : has some informations about the tasks that should be carried (like building)  
Player : has planets and darkmatter (and in the future technologies ...)  
Planet : has resources and buildings  
Building : has level, cost and time to upgrade, and functions to upgrade it  
Task : has time when it should be executed. Extended Tasks have an execute function that carries it (like build a building)  
