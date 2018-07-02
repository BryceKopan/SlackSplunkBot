import os
import RESTSplunkMethods as Splunk
import Util
import SimpleHipChat as HipChat

enviroment = "ITest"

def list_saved_searches(commandParameters, channel):
	results = Splunk.listSavedSearches()
	HipChat.postMessage(results, channel)
	
def run_saved_search(commandParameters, channel):
	results = Splunk.runSavedSearch(commandParameters[0])
	HipChat.postMessage(results, channel)
	
def run_search(commandParameters, channel):
	results = Splunk.runSearch(commandParameters[0])
	table = Util.formatResultsAsTable(results)
	HipChat.postMessage(table, channel)
	
def list_apps(commandParameters, channel):
	if(len(commandParameters) > 0):
		results = Splunk.listAppNames(commandParameters[0])
	else:
		results = Splunk.listAppNames()
	HipChat.postMessage(results, channel)
	
def list_dashboards(commandParameters, channel):
	if(len(commandParameters) > 1):
		results = Splunk.listDashboardNames(commandParameters[0], commandParameters[1])
	else:
		results = Splunk.listDashboardNames(commandParameters[0])
	HipChat.postMessage(results, channel)
	
def get_dashboard(commandParameters, channel):
	Splunk.getDashboardPDF(commandParameters[0], commandParameters[1])
	name = commandParameters[0] + "_" + commandParameters[1]
	HipChat.postImage("pdf_files/"+ pdfName + ".pdf", pdfName, channel)
	
#Testing Commands

def connect_to(commandParameters, channel):
	global enviroment

	if commandParameters == "ITest":
		enviroment = commandParameters
		BASE_URL = "https://splunk-itest.ercot.com:8089"
		USERNAME = os.environ.get('SPLUNK_USERNAME')
		PASSWORD = os.environ.get('SPLUNK_PASSWORD')
		
		Splunk.connect(BASE_URL, USERNAME, PASSWORD)
		HipChat.postMessage("Connected to ITest", channel)
		
	elif commandParameters == "Local":
		enviroment = commandParameters
		BASE_URL = "https://localhost:8089"
		USERNAME = os.environ.get('SPLUNK_LOCAL_USERNAME')
		PASSWORD = os.environ.get('SPLUNK_LOCAL_PASSWORD')
		
		Splunk.connect(BASE_URL, USERNAME, PASSWORD)
		HipChat.postMessage("Connected to Local", channel)
		
def which_enviroment(commandParameters, channel):
	HipChat.postMessage("I am currently connected to {}".format(enviroment), channel)