import os, sys
import splunklib.client as client
import splunklib.results as results
from time import sleep

def connect():
	HOST = "localhost"
	PORT = 8089
	USERNAME = os.environ['SPLUNK_USERNAME']
	PASSWORD = os.environ['SPLUNK_PASSWORD']

	# Create a Service instance and log in 
	service = client.connect(
		host=HOST,
		port=PORT,
		username=USERNAME,
		password=PASSWORD)
	
	return service 

def newSearch(service, searchString):
	job = service.jobs.create("search " + searchString)
	resultsToReturn = []

	while not job.is_done():
		sleep(.2)
	
	jobresults = results.ResultsReader(job.results())
	
	for result in jobresults:
		resultsToReturn.append(result)
	
	assert jobresults.is_preview == False
	
	return resultsToReturn
	

