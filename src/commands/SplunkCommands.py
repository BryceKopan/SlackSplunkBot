import os
import RESTSplunkMethods as Splunk
import Util
import SimpleHipChat as HipChat

enviroment = "LOCAL"

def list_saved_searches(commandParameters, channel):
	"""  """
	if(len(commandParameters) > 0):
		results = Splunk.listSavedSearches(commandParameters[0])
	else:
		results = Splunk.listSavedSearches()
	HipChat.postNotification(str(results), channel)
	
def list_reports(commandParameters, channel):
	if(len(commandParameters) > 0):
		results = Splunk.listReportNames(commandParameters[0])
	else:
		results = Splunk.listReportNames()
	results = eval(results)
	HipChat.postNotification(Util.formatArray(results), channel)
	
def run_saved_search(commandParameters, channel):
	results = Splunk.runSavedSearch(commandParameters[0])
	HipChat.postNotification(str(results), channel)
	
def run_search(commandParameters, channel):
	results = Splunk.runSearch(commandParameters[0])
	results = eval(results)
	table = Util.formatResultsAsHTMLTable(results)
	HipChat.postNotification(table, channel, format = 'html')
	
def list_apps(commandParameters, channel):
	if(len(commandParameters) > 0):
		results = Splunk.listAppNames(commandParameters[0])
	else:
		results = Splunk.listAppNames()
	results = eval(results)
	HipChat.postNotification(Util.formatArray(results), channel)
	
def list_dashboards(commandParameters, channel):
	if(len(commandParameters) > 1):
		results = Splunk.listDashboardNames(commandParameters[0], commandParameters[1])
	else:
		results = Splunk.listDashboardNames(commandParameters[0])
	results = eval(results)
	HipChat.postNotification(Util.formatArray(results), channel)
	
def get_dashboard(commandParameters, channel):
	HipChat.postNotification("Getting dashboard {} from {}".format(commandParameters[1], commandParameters[0]), channel)
	Splunk.getDashboardPdf(commandParameters[0], commandParameters[1])
	pdfName = commandParameters[0] + "_" + commandParameters[1]
	pngPaths = Util.convertPDFToPNG(pdfName)
	for path in pngPaths:
		HipChat.postFile(path, channel)
		
def list_alerts(commandParameters, channel):
	if(len(commandParameters) > 0):
		results = Splunk.listAlertNames(commandParameters[0])
	else:
		results = Splunk.listAlertNames()
	results = eval(results)
	HipChat.postNotification(Util.formatArray(results), channel)
		
def list_disabled_alerts(commandParameters, channel):
	if(len(commandParameters) > 0):
		results = Splunk.listDisabledAlerts(commandParameters[0])
	else:
		results = Splunk.listDisabledAlerts()
	results = eval(results)
	HipChat.postNotification(Util.formatArray(results), channel)
		
def enable_alert(commandParameters, channel):
	Splunk.enableAlert(commandParameters[0])
	HipChat.postNotification("{} enabled".format(commandParameters[0]), channel)
		
def disable_alert(commandParameters, channel):
	if(len(commandParameters) > 1):
		Splunk.disableAlert(commandParameters[0], int(commandParameters[1]))
		HipChat.postNotification("{} disabled for {} minutes".format(commandParameters[0], commandParameters[1]), channel)
	else:
		Splunk.disableAlert(commandParameters[0])
		HipChat.postNotification("{} disabled".format(commandParameters[0]), channel)
	
#Testing Commands

def connect_to(commandParameters, channel):
	global enviroment
	
	if commandParameters[0].upper() == "ITEST":
		enviroment = commandParameters[0].upper()
		BASE_URL = "https://splunk-itest.ercot.com:8089"
		USERNAME = os.environ.get('SPLUNK_USERNAME')
		PASSWORD = os.environ.get('SPLUNK_PASSWORD')
		
		Splunk.connect(BASE_URL, USERNAME, PASSWORD)
		HipChat.postNotification("Connected to ITest", channel)
		
	elif commandParameters[0].upper() == "LOCAL":
		enviroment = commandParameters[0].upper()
		BASE_URL = "https://localhost:8089"
		USERNAME = os.environ.get('SPLUNK_LOCAL_USERNAME')
		PASSWORD = os.environ.get('SPLUNK_LOCAL_PASSWORD')
		
		Splunk.connect(BASE_URL, USERNAME, PASSWORD)
		HipChat.postNotification("Connected to Local", channel)
		
def which_enviroment(commandParameters, channel):
	HipChat.postNotification("I am currently connected to {}".format(enviroment), channel)