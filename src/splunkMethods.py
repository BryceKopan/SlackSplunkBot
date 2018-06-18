import os, sys
import splunklib.client as client
import splunklib.results as results
from time import sleep

service = None

def connect():
	HOST = "localhost"
	PORT = 8089
	USERNAME = os.environ['SPLUNK_USERNAME']
	PASSWORD = os.environ['SPLUNK_PASSWORD']

	# Create a Service instance and log in
	global service
	service = client.connect(
		host=HOST,
		port=PORT,
		username=USERNAME,
		password=PASSWORD,
		autologin=True)


def newSearch(searchString):
	job = service.jobs.create("search " + searchString)
	resultsToReturn = []

	while not job.is_done():
		sleep(.2)
	
	jobResults = results.ResultsReader(job.results())
	
	for result in jobResults:
		resultsToReturn.append(result)
	
	assert jobResults.is_preview == False
	
	return resultsToReturn
	
	
def savedSearch(savedSearchName):
	try: 
		mySavedSearch = service.saved_searches[savedSearchName]
		job = mySavedSearch.dispatch()
		resultsToReturn = []
		
		while not job.is_done():
			sleep(.2)

		jobResults = results.ResultsReader(job.results())
		
		for result in jobResults:
			resultsToReturn.append(result)
		
		assert jobResults.is_preview == False
		
		return resultsToReturn
	except KeyError:
		return "Invalid saved search name"
		
	
def listSavedSearches():
	savedSearches = service.saved_searches
	resultsToReturn = []
	
	for savedSearch in savedSearches:
		resultsToReturn.append(savedSearch.name)
		
	return resultsToReturn
	
	
