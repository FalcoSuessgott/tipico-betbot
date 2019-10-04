# tipico-betbot
Tipico betbot, which fetches football predictions from [boggio-analytics](https://boggio-analytics.com/fp-api/), parses them and places them with [Selenium](https://www.seleniumhq.org/) on [Tipico](https://www.tipico.de/en/online-sports-betting/).
Boggio-Analytics claim to have a success rate of 70-75%, which should theoretically, in a certain period, end in profit.

# Note
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
Also you need to register at [Rapid-API](https://rapidapi.com/boggio-analytics/api/football-prediction), so that you can fetch the predictions (its for free, but you will need a credit-card).
 
## Installation
```shell script
git clone https://www.github.com/FalcoSuessgott/tipico-betbot
cd tipico-betbot
```

## Configuration
In `tipico-betbot.py`, specify the token, that you have received from Rapid-API.

```python
API_KEY = "23da3be5b7msh1cee41ef14ca891p1f7711jsncc9ae84efe91"
``` 

## Usage
Run the bot, with 2.50€ wage per bet

```python
python tipico-betbot.py --username TIPICO_EMAIL --password TIPICO_PASSWORD --wager 2.50 -H
```
``
