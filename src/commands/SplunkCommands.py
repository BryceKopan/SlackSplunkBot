import RESTSplunkMethods as Splunk
import SlackAPI as Slack
import Util

def list_saved_searches(commandParameters, channel):
	results = Splunk.listSavedSearches()
	Slack.postMessage(results, channel)
	
def run_saved_search(commandParameters, channel):
	results = Splunk.runSavedSearch(commandParameters)
	Slack.postMessage(results, channel)
	
def run_search(commandParameters, channel):
	results = Splunk.runSearch(commandParameters)
	table = Util.formatResultsAsTable(results)
	Slack.postMessage(table, channel)