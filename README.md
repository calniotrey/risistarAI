# risistarAI
codes that play Risistar automatically

## Requirements :
Python 3(3.6 sould be fine)
BeautifulSoup 4 (pip install beautifulsoup4)

## Parameters :
You need to specify your credentials in a secret.txt (or modify the code, but be careful not to upload them)
First line : username (no " nor username=...)
Second line : password
Then you can write some other informations (like the email used and so on), it won't be used

## Startup :
`python start.py`
or
`python3 start.py`

## Classes :
IA : has some informations about the tasks that should be carried (like building)  
Player : has planets and darkmatter (and in the future technologies ...)  
Planet : has ressources and buildings  
Building : has level, cost and time to upgrade, and functions to upgrade it  
Task : has time when it should be executed. Extended Tasks have an execute function that carries it (like build a building)  
