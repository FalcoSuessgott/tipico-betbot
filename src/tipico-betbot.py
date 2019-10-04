#!/usr/bin/env python
#
#   Fetches predictions from football-prediction-api.p.rapidapi.com
#   and sets them on tipico
#
#   Author: tom-morelly@gmx.de
#   Date:   16.04.2019
#
#

import argparse
import os
import sys
import requests
import time
import json
import jellyfish
import smtplib
from datetime import date
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

TIPICO_URL = "https://www.tipico.de/"
API_KEY = ""
API_HOST = "football-prediction-api.p.rapidapi.com"
PRED_PATH = "/tmp/"
MAIL = "mail@gmail.com"
MAIL_PW = ""


def parseArgs():
	""" Args parse"""
	parser = argparse.ArgumentParser()
	parser.add_argument("-u", "--username", dest="username", action="store", help="E-Mail")
	parser.add_argument("-p", "--password", dest="password", action="store", help="Password")
	parser.add_argument("-w", "--wager", dest="wager", action="store", type=float, help="Wager per bet")
	parser.add_argument("-a", "--amount", dest="amount", action="store", type=int, help="Amount of bets")
	parser.add_argument("-M", "--minimum-quote", dest="minimum", action="store", type=float, help="Minimum quote, fore example \"1.50\"")
	parser.add_argument("-H", "--headless", dest="headless", action="store_true", help="Opens Selenium in headless mode.")

	if len(sys.argv) == 1:
		print("No arguments were specified.\nExiting.")
		parser.print_help()
		sys.exit(1)

	parser = parser.parse_args()

	if API_KEY is "":
		print("Please specify \"API_KEY\" with the token from %s. Exiting." % API_HOST)
		sys.exit(1)

	if not parser.password or not parser.username:
		print("Username or password missing.")
		sys.exit(1)

	if not parser.wager:
		print("Please specify a wage, that is used for each single bet.")
		sys.exit(1)

	if parser.password and parser.username:
		mail_content = ""
		data = fetch_bet_predictions()

		if parser.headless:
			driver = initialize_selenium_driver(True)
		else:
			driver = initialize_selenium_driver(False)

		login_to_tipico(driver, parser.username, parser.password)

		print("Starting iterating through predictions ...")

		driver.get(TIPICO_URL + "en/online-sports-betting/football/g1102/")
		driver.find_element_by_id('jq-navBlock-GROUP-1101').click()
		driver.find_element_by_id('jq-further-1101').click()

		i = 0
		placed_bets = 0

		for p in data['data']:
			i += 1
			driver.refresh()
			print("[%s/%s] " % (i, len(data['data'])), end='')
			bet = place_bet_routine(driver, p, parser.wager, parser.minimum)

			if bet is not None:
				mail_content += bet
				placed_bets += 1
				if placed_bets == int(parser.amount):
					print("Placed %d bets. Exiting." % placed_bets)
					send_notification_mail(MAIL, MAIL_PW, parser.username, mail_content)
					sys.exit(0)

	driver.close()


def initialize_selenium_driver(headless):
	""" init web driver """

	try:
		print("Initializing selenium driver ... ", end=' ')
		if headless:
			options = Options()
			options.headless = True
			webdriver.Firefox(options=options, executable_path=os.path.dirname(os.path.realpath(__file__)) + '/selenium/geckodriver')
		driver = webdriver.Firefox(executable_path=os.path.dirname(os.path.realpath(__file__)) + '/selenium/geckodriver')
		print("Successfully loaded selenium driver.")
		return driver
	except Exception as e:
		print("Error while loading driver.")
		print(e)
		sys.exit(1)


def login_to_tipico(driver, user, passwd):
	"""" Logs into tipico using USER and PASSWORD """

	try:
		print("Login in to %s with %s ... " % (TIPICO_URL, user), end=' ')
		driver.get(TIPICO_URL + "/login")
		driver.find_element_by_class_name('login-button').click()
		driver.find_element_by_id("login").send_keys(user)
		driver.find_element_by_id("password").send_keys(passwd)
		time.sleep(2)
		driver.find_element_by_id("loginButton").click()
		print("Successfully logged in.")
	except Exception:
		print("Error while trying to login. Exiting.\n")
		sys.exit(1)


def fetch_bet_predictions():
	""" Received Predictions """
	try:
		print("Getting bet predictions from %s ... " % API_HOST, end=' ')

		headers = {
			"X-RapidAPI-Host": API_HOST,
			"X-RapidAPI-Key": API_KEY
		}

		response = requests.get("https://football-prediction-api.p.rapidapi.com/api/v1/predictions", headers=headers)
		data = json.loads(response.text)
		write_predictions_to_file(response.text, PRED_PATH)
		with open("/tmp/pred.json") as outfile:
			data = json.load(outfile)
			print("Wrote predictions to /tmp/pred.json")
		print("Gathered %s predictions." % len(data['data']))
		return data
	except Exception as e:
		print("Error while getting predictions. Exiting.")
		print(e)
		sys.exit(1)


def write_predictions_to_file(data, path):
	""" Writes data to specified path"""

	now = datetime.now()
	dt_string = now.strftime("%d%m%Y_%H%M%S")
	f = open(path + "pred.json", "w")

	try:
		print("Writing predictions to " + path + "predictions_" + dt_string)
		f.write(str(data))
		print("Successfully created file.")
	except Exception as e:
		print("Something went wrong while writing to file.")
		print(e)
		sys.exit(1)
	finally:
		f.close()


def place_bet_routine(driver, data, wager, minimum):
	""" places a single Bet"""

	bet_output = "Country: %s, Competition: %s, %s vs. %s, Odds: %s, Prediction: %s" % (
		data['competition_cluster'],
		data['competition_name'],
		data['home_team'],
		data['away_team'],
		data['odds'][data['prediction']],
		data['prediction']
	)
	print(bet_output)

	if data['odds'][data['prediction']] <= float(minimum):
		print("Bet does not have the specified minimum quote. Skipping.")
		return

	nation_id = get_nation(driver, data['competition_cluster'])

	if nation_id is not None:
		if not get_league(driver, nation_id, data['competition_name']):
			print("Skipping Bet.")
			return None
	else:
		print("Skipping Bet.")
		return None

	if navigate_to_game(driver, data['home_team'], data['away_team'], data['prediction']):
		place_bet_for_game(driver, wager)
		delete_bets(driver)

	if nation_id is not None:
		get_nation(driver, data['competition_cluster'])

	deselect_all(driver)
	return bet_output


def get_nation(driver, nation):
	""" navigates to the specified nation """

	nation_holder = driver.find_element_by_id("comp-GROUP_1101")

	try:
		for nat in nation_holder.find_elements_by_class_name('nav_2'):
			if nation.lower() in nat.get_attribute('href'):
				nat.click()
				return nat.get_attribute('id').split("-")[3] # nation ID
	except Exception as e:
		print("Cannot find %s." % nation)
		return None


def get_league(driver, nation_id, league):
	""" navigates to the specified league """

	league_holder = driver.find_element_by_id("comp-GROUP_" + nation_id)

	try:
		for l in league_holder.find_elements_by_tag_name("li"):
			if get_similarity(l.text, league) <= 5:
				l.click()
				return True
		print("Cannot find %s." % league)
		return False
	except Exception as e:
		print("Error occurred while getting %s. Still trying to find the game." % league)
		pass


def deselect_all(driver):
	""" deselects all options """
	element = driver.find_element_by_id('jq-navBlock-GROUP-1101')

	try:
		for e in element.find_elements_by_xpath(".//*"):
			if e.get_attribute('class') == "num_r hide":
				for subElement in e.find_elements_by_xpath(".//*"):
					if subElement.get_attribute('width') == "12":
						driver.execute_script("arguments[0].click();", subElement)
	except Exception as e:
		return

def delete_bets(driver):
	""" deletes all bets """
	ticket_body = driver.find_element_by_xpath("//div[starts-with(@id,'ticket_body')]")

	try:
		for e in ticket_body.find_elements_by_xpath(".//*"):
			if e.get_attribute('class') == "remove_all red align_r":
				e.click()
	except Exception as e:
		return


def navigate_to_game(driver, home_team, away_team, bet):
	""" navigates to the specific game"""

	events = driver.find_elements_by_xpath("//div[starts-with(@id,'_program_group')]")

	i = 0
	for event in events:
		i += 1
		if not find_matching_team(event, home_team) or not find_matching_team(event, away_team):
			continue

		if find_matching_team(event, home_team) and find_matching_team(event, away_team):
			expand_bet_options(event)
			set_prediction_to_game(event, bet, i)
			return True
	return False


def find_matching_team(event, team):
	"""returns true if the specified team participate in the event"""

	for subElement in event.find_elements_by_xpath(".//*"):
		className = subElement.get_attribute('class')

		if "t_cell w" in className:
			ratio = get_similarity(team, subElement.text)
			if ratio <= 5:
				return True

	return False


def get_similarity(a, b):
	return jellyfish.hamming_distance(a, b)


def expand_bet_options(event):
	""" expands the bet options for a single game"""

	for subElement in event.find_elements_by_xpath(".//*"):
		try:
			className = subElement.get_attribute('class')

			if "t_more bl" in className:
				subElement.click()
		except Exception as e:
			pass


def set_prediction_to_game(event, bet, eventNumber):
	""" sets the prediction to the gamet"""

	bets = event.find_elements_by_xpath("//div[starts-with(@class,'qbut  qbut-')]")

	if eventNumber == 1:
		quotes = bets[0:6]
	if eventNumber == 2:
		quotes = bets[3:9]
	if eventNumber > 2:
		quotes = bets[eventNumber * 2: (eventNumber * 2) + 6]

	try:
		if bet == "1":
			print("Placed bet \"1\" for this event.")
			quotes[0].click()
		elif bet == "X":
			print("Placed bet \"X\" for this event.")
			quotes[1].click()
		elif bet == "2":
			print("Placed bet \"2\" for this event.")
			quotes[2].click()
		elif bet == "1X":
			print("Placed bet \"1X\" for this event.")
			quotes[3].click()
		elif bet == "12":
			print("Placed bet \"12\" for this event.")
			quotes[4].click()
		elif bet == "X2":
			print("Placed bet \"X2\" for this event.")
			quotes[5].click()
		else:
			print("Invalid bet.")
	except Exception:
		pass


def place_bet_for_game(driver, wager):
	""" Sets the wager for the bet and placed it"""

	try:
		driver.refresh()
		driver.find_element_by_id("editorForm:amountDisplay").send_keys(wager)
		time.sleep(2)
		driver.find_element_by_id("editorForm:reactionRepeat:0:cmdReaction").click()
		print("Bet placed.")
	except Exception:
		pass

def send_notification_mail(user, pwd, recipient, body):
	""" sends an email """
	today = date.today()
	FROM = user
	TO = recipient if isinstance(recipient, list) else [recipient]
	SUBJECT = "Tipico Bets placed by betbot %s" % today.strftime("%d.%m.%Y")
	TEXT = body

	message = """From: %s\nTo: %s\nSubject: %s\n\n%s
	    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
	try:
		server = smtplib.SMTP("smtp.googlemail.com", 587)
		server.ehlo()
		server.starttls()
		server.login(user, pwd)
		server.sendmail(FROM, TO, message)
		server.close()
		print('successfully send mail')
	except Exception as e:
		print(e)
		print("failed to send mail")


if __name__ == '__main__':
	parseArgs()
