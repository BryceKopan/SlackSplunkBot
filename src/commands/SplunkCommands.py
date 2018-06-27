import os
import RESTSplunkMethods as Splunk
import SlackAPI as Slack
import Util

enviroment = "ITest"

def list_saved_searches(commandParameters, channel):
	results = Splunk.listSavedSearches()
	Slack.postMessage(results, channel)
	
def run_saved_search(commandParameters, channel):
	results = Splunk.runSavedSearch(commandParameters[0])
	Slack.postMessage(results, channel)
	
def run_search(commandParameters, channel):
	results = Splunk.runSearch(commandParameters[0])
	table = Util.formatResultsAsTable(results)
	Slack.postMessage(table, channel, False)
	
def list_apps(commandParameters, channel):
	if(len(commandParameters) > 0):
		results = Splunk.listAppNames(commandParameters[0])
	else:
		results = Splunk.listAppNames()
	Slack.postMessage(results, channel)
	
def list_dashboards(commandParameters, channel):
	results = Splunk.listDashboardNames(commandParameters[0])
	Slack.postMessage(results, channel)
	
#Testing Commands

def connect_to(commandParameters, channel):
	global enviroment

	if commandParameters == "ITest":
		enviroment = commandParameters
		BASE_URL = "https://splunk-itest.ercot.com:8089"
		USERNAME = os.environ.get('SPLUNK_USERNAME')
		PASSWORD = os.environ.get('SPLUNK_PASSWORD')
		
		Splunk.connect(BASE_URL, USERNAME, PASSWORD)
		Slack.postMessage("Connected to ITest", channel)
		
	elif commandParameters == "Local":
		enviroment = commandParameters
		BASE_URL = "https://localhost:8089"
		USERNAME = os.environ.get('SPLUNK_LOCAL_USERNAME')
		PASSWORD = os.environ.get('SPLUNK_LOCAL_PASSWORD')
		
		Splunk.connect(BASE_URL, USERNAME, PASSWORD)
		Slack.postMessage("Connected to Local", channel)
		
def which_enviroment(commandParameters, channel):
	Slack.postMessage("I am currently connected to {}".format(enviroment), channel)