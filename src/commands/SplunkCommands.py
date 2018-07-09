import os
import RESTSplunkMethods as Splunk
import Util
import SimpleHipChat as HipChat

enviroment = "LOCAL"

def list_saved_searches(commandParameters, channel):
	results = Splunk.listSavedSearches()
	HipChat.postMessage(results, channel)
	
def run_saved_search(commandParameters, channel):
	results = Splunk.runSavedSearch(commandParameters[0])
	HipChat.postMessage(results, channel)
	
def run_search(commandParameters, channel):
	results = Splunk.runSearch(commandParameters[0])
	table = Util.formatResultsAsHTMLTable(results)
	HipChat.postNotification(table, channel, format = 'html')
	
def list_apps(commandParameters, channel):
	if(len(commandParameters) > 0):
		results = Splunk.listAppNames(commandParameters[0])
	else:
		results = Splunk.listAppNames()
	HipChat.postMessage(str(results), channel)
	
def list_dashboards(commandParameters, channel):
	if(len(commandParameters) > 1):
		results = Splunk.listDashboardNames(commandParameters[0], commandParameters[1])
	else:
		results = Splunk.listDashboardNames(commandParameters[0])
	HipChat.postMessage(str(results), channel)
	
def get_dashboard(commandParameters, channel):
	Splunk.getDashboardPdf(commandParameters[0], commandParameters[1])
	pdfName = commandParameters[0] + "_" + commandParameters[1]
	pngPaths = Util.convertPDFToPNG(pdfName)
	for path in pngPaths:
		HipChat.postFile(path, channel)
		
def list_disabled_alerts(commandParameters, channel):
	if(len(commandParameters) > 0):
		results = Splunk.listDisabledAlerts(commandParameters[0])
	else:
		results = Splunk.listDisabledAlerts()
	HipChat.postMessage(str(results), channel)
		
def enable_alert(commandParameters, channel):
	Splunk.enableAlert(commandParameters[0])
	HipChat.postMessage("{} enabled".format(commandParameters[0]), channel)
		
def disable_alert(commandParameters, channel):
	Splunk.disableAlert(commandParameters[0], int(commandParameters[1]))
	HipChat.postMessage("{} disabled for {} minutes".format(commandParameters[0], commandParameters[1]), channel)
	
#Testing Commands

def connect_to(commandParameters, channel):
	global enviroment
	
	if commandParameters[0].upper() == "ITEST":
		enviroment = commandParameters[0].upper()
		BASE_URL = "https://splunk-itest.ercot.com:8089"
		USERNAME = os.environ.get('SPLUNK_USERNAME')
		PASSWORD = os.environ.get('SPLUNK_PASSWORD')
		
		Splunk.connect(BASE_URL, USERNAME, PASSWORD)
		HipChat.postMessage("Connected to ITest", channel)
		
	elif commandParameters[0].upper() == "LOCAL":
		enviroment = commandParameters[0].upper()
		BASE_URL = "https://localhost:8089"
		USERNAME = os.environ.get('SPLUNK_LOCAL_USERNAME')
		PASSWORD = os.environ.get('SPLUNK_LOCAL_PASSWORD')
		
		Splunk.connect(BASE_URL, USERNAME, PASSWORD)
		HipChat.postMessage("Connected to Local", channel)
		
def which_enviroment(commandParameters, channel):
	HipChat.postMessage("I am currently connected to {}".format(enviroment), channel)