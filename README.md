# tipico-betbot
Tipico betbot, which fetches football predictions from [boggio-analytics](https://boggio-analytics.com/fp-api/), parses them and places them with [Selenium](https://www.seleniumhq.org/) on [Tipico](https://www.tipico.de/en/online-sports-betting/).

Boggio-Analytics claims to have a success rate of 70-75% which should, theoretically end in a certain period, in profit.

# Note
Tested with `python3.6`.

This tool is still under development, I am not responsible for your money loss.

# Features
* Specify the wager for each single bet
* Only place bets with a minimum quote
* Specify the amount of bets that are placed
* get a notification mail, with all bets that has beend placed

# Getting Started
In order to use this tool, follow these instructions:

## Prerequisites
Of course you will need a [Tipico](https://www.tipico.de/en/online-sports-betting/)-Account.
Also you need to register at [Rapid-API](https://rapidapi.com/boggio-analytics/api/football-prediction), so that you can fetch the predictions (its free, but you will need a credit-card).
 
## Requirements
```
pip install jellyfish
```
## Installation
```shell script
git clone git@github.com:FalcoSuessgott/tipico-betbot.git
cd tipico-betbot
```

## Configuration
In `src/tipico-betbot.py`, specify the token, that you have received from Rapid-API.

```python
API_KEY = "121313223"
``` 

## Usage
Run the bot, with 2.50€ wage per bet in headless mode (a browser window will popup and displays you the action that are going to be made)

```python
python tipico-betbot.py -u TIPICO_EMAIL -p TIPICO_PASSWORD -W 2.50 -H
```

# ToDo's
* check cli options while starting script
