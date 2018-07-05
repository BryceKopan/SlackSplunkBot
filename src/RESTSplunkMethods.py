import os, urllib, httplib2, json, threading 
from time import sleep
import xml.etree.ElementTree as ET
from xml.dom import minidom

BASE_URL = None
USER = None
SESSION_KEY = None
SEARCH_TTL = 10
PATH = os.path.abspath(os.path.dirname(__file__))
myhttp = httplib2.Http(disable_ssl_certificate_validation=True)

def connect(urlPrefix, username, password):
	"""
		Creates a connection with a Splunk enterprise instance and 
		sets a global session key to be used in subsequent requests.
		Parameters:
			urlPrefix (required) = the base URL for all requests (i.e. https://host:port)
			username (required) = Splunk username
			password (required) = Splunk password
	"""
	print("[CONNECT]")
	global BASE_URL, USER
	BASE_URL = urlPrefix
	USER = username
	
	response, content = myhttp.request(
		BASE_URL + '/services/auth/login?output_mode=json',
		'POST',
		headers={},
		body=urllib.parse.urlencode({'username':username, 'password':password, 'autoLogin':True}))
		
	decodedContent = json.loads(content.decode('utf-8'))
	
	if response.status == 200:
		global SESSION_KEY
		SESSION_KEY = decodedContent["sessionKey"]
		print("Successfully connected to Splunk server")
		thread = threading.Thread(target=autoReconnect, args=(urlPrefix, username, password))
		# thread.start()
		
		return
	else:
		errorMessage = decodedContent["messages"][0]["text"]
		raise Exception("%s - %s" % (response.status, errorMessage))

def autoReconnect(urlPrefix, username, password):
	sleep(59 * 60) # sleep for 59 minutes
	print("[AUTO RECONNECT] Attempting to reconnect with Splunk server")
	return connect(urlPrefix, username, password)

		
# ---------------------------------------- SEARCH METHODS ----------------------------------------	
 
def getSearchStatus(sid):
	"""
		Repeatedly retrieves the status of a search until the search completes or it times out.
		Parameters:
			sid (required) = search ID
	"""
	print("Getting search status")
	isNotDone = True
	elapsedTime = 0
	
	while isNotDone and elapsedTime < SEARCH_TTL:
		content = myhttp.request(
			(BASE_URL + "/services/search/jobs/%s?output_mode=json" % sid), 
			'GET', 
			headers={'Authorization':('Splunk %s' % SESSION_KEY)})[1]
		
		searchStatus = json.loads(content.decode('utf-8'))
		
		if not searchStatus["entry"][0]["content"]["isDone"]:
			elapsedTime += 1
			sleep(1)
		else:
			isNotDone = False
	
	if elapsedTime >= SEARCH_TTL:
		raise Exception("Search took too long. Try narrowing your time range")
	else:
		return

		
def getSearchResults(sid):
	"""
		Retrieves the results of a previously run search. Returns results in JSON form.
		Parameters:
			sid (required) = search ID
	"""
	getSearchStatus(sid)
	print("Getting search results")
	
	response, content = myhttp.request(
		(BASE_URL + "/services/search/jobs/%s/results?output_mode=json&count=0" % sid), 
		'GET', 
		headers={'Authorization':('Splunk %s' % SESSION_KEY)})
	
	if response.status == 200:
		results = "%s" % json.loads(content.decode('utf-8'))["results"] 
		return results.replace('},','},\n')
	else:
		errorMessage = json.loads(content.decode('utf-8'))["messages"][0]["text"]
		raise Exception(errorMessage)
	
	
def listSavedSearches(*searchString):
	"""
		Lists the names of saved searches (reports & alerts). Returns results in JSON form.
		Parameters:
			searchString (optional) = filters results. searchString is NOT case sensitive
	"""
	print("[LIST SAVED SEARCHES]")
	response, content = myhttp.request(
		BASE_URL + "/services/saved/searches?output_mode=json&count=0", 
		'GET', 
		headers={'Authorization':('Splunk %s' % SESSION_KEY)})

	decodedContent = json.loads(content.decode('utf-8'))
	
	if response.status == 200:
		listOfSavedSearches = []
		
		if searchString:
			for entry in decodedContent["entry"]:
				if ("%s" % searchString).lower() in entry["name"].lower() and entry["content"]["is_visible"]:
					listOfSavedSearches.append(entry["name"])
		else:
			for entry in decodedContent["entry"]:
				if entry["content"]["is_visible"]:
					listOfSavedSearches.append(entry["name"])
		
		listOfSavedSearches = "%s" % listOfSavedSearches	
		return listOfSavedSearches.replace(',',',\n')
	else:
		errorMessage = json.loads(content.decode('utf-8'))["messages"][0]["text"]
		raise Exception(errorMessage)
	
	
def runSavedSearch(savedSearchName, triggerActions=False):
	"""
		Runs a saved search. Returns results in JSON form.
		Run 'listSavedSearches' to get the correct name.
		Parameters:
			savedSearchName (required) = the name of the saved Splunk search
			triggerActions (optional) = specify whether to trigger alert actions (Boolean)
	"""
	print("[RUN SAVED SEARCH]: %s" % savedSearchName)
	# reformat saved search name for URL
	savedSearchName = savedSearchName.replace(' ', '%20')

	response, content = myhttp.request(
		(BASE_URL + "/services/saved/searches/%s/dispatch?output_mode=json&trigger_actions=%s" % (savedSearchName, triggerActions)), 
		'POST', 
		headers={'Authorization':('Splunk %s' % SESSION_KEY)})
	
	if response.status == 201:
		sid = json.loads(content.decode('utf-8'))["sid"]
		return getSearchResults(sid)
	else:
		errorMessage = json.loads(content.decode('utf-8'))["messages"][0]["text"]
		raise Exception(errorMessage)

			
def runSearch(searchString):
	"""
		Accepts ad hoc search strings. Returns results in JSON form.
		Parameters:
			searchString (required) = the ad hoc search string in the Splunk Search Processing Language (SPL)
	"""
	print("[RUN SEARCH]: %s" % searchString)
	if not searchString.startswith('search'):
		searchString = 'search ' + searchString

	response, content = myhttp.request(
		(BASE_URL + '/services/search/jobs?output_mode=json&auto_cancel=%s' % SEARCH_TTL),
		'POST',
		headers={'Authorization': 'Splunk %s' % SESSION_KEY},
		body=urllib.parse.urlencode({'search': searchString}))
	
	if response.status == 201:
		sid = json.loads(content.decode('utf-8'))["sid"]
		return getSearchResults(sid)
	else:		
		errorMessage = json.loads(content.decode('utf-8'))["messages"][0]["text"]
		raise Exception(errorMessage)

	
	
# ---------------------------------------- DASHBOARD METHODS ----------------------------------------
# dashboard name is not always the same as the dashboard display name. Run listDashboardNames to get the correct name.
# namespace is the app where the dashboard is located.

	
def listDashboardNames(namespace, *searchString):
	"""
		Lists the names of dashboards in the specified app. Returns results in JSON form.
		Parameters:
			namespace (required) = the app name
			searchString (optional) = filters results. searchString is NOT case sensitive
	"""
	print("[LIST DASHBOARD NAMES]: namespace=%s" % namespace)
	response, content = myhttp.request(
		(BASE_URL + "/servicesNS/%s/%s/data/ui/views?output_mode=json&count=0" % (USER, namespace)), 
		'GET', 
		headers={'Authorization':('Splunk %s' % SESSION_KEY)})
	
	decodedContent = json.loads(content.decode('utf-8'))
	
	if response.status == 200:
		listOfDashboards = []
		
		if searchString:
			for entry in decodedContent["entry"]:
				if entry["content"]["isDashboard"] and entry["content"]["isVisible"] and ("%s" % searchString).lower() in entry["name"].lower():
					listOfDashboards.append(entry["name"])
		else:
			for entry in decodedContent["entry"]:
				if entry["content"]["isDashboard"] and entry["content"]["isVisible"]:
					listOfDashboards.append(entry["name"])
		
		listOfDashboards = "%s" % listOfDashboards
		return listOfDashboards.replace(',',',\n')
	else:
		errorMessage = decodedContent["messages"][0]["text"]
		raise Exception(errorMessage)

		
def getDashboardXML(namespace, dashboard):
	"""
		Gets the specified dashboard XML.
		Parameters:
			namespace (required) = the name of the app where the dashboard is located
			dashboard (required) = the dashboard name
	"""
	print("Getting dashboard XML for namespace=%s, dashboard=%s" % (namespace, dashboard))
	response, content = myhttp.request(
		BASE_URL + ("/servicesNS/%s/%s/data/ui/views/%s" % (USER, namespace, dashboard)), 
		'GET',
		headers={'Authorization':('Splunk %s' % SESSION_KEY)})
	
	decodedContent = content.decode('utf-8')
	
	if response.status == 200:
		return decodedContent
	else:
		tree = ET.fromstring(decodedContent)
		messages = tree.find('messages')
		errorMessage = messages.find('msg').text
		raise Exception(errorMessage)
	
	
def listDashboardInputs(namespace, dashboard):
	"""
		Lists the dashboard tokens available to the specified dashboard. Returns results in JSON form.
		Parameters:
			namespace (required) = the name of the app where the dashboard is located
			dashboard (required) = the dashboard name
	"""
	print("[LIST DASHBOARD INPUTS] namespace=%s, dashboard=%s" % (namespace, dashboard))
	dashboardInputs = []
	XMLDashboard = getDashboardXML(namespace, dashboard)
	XMLDashboard=XMLDashboard.replace('![CDATA[<', '') # remove this xml tag so the xml can be parsed below
	XMLDashboard=XMLDashboard.replace(']]>', '')

	tree = ET.fromstring(XMLDashboard)
	entry = tree.find('{http://www.w3.org/2005/Atom}entry')
	content = entry.find('{http://www.w3.org/2005/Atom}content')
	dict = content.find('{http://dev.splunk.com/ns/rest}dict')

	global data
	for elem in dict:
		if elem.attrib["name"] == "eai:data":
			data = elem
			break

	form = data.find('{http://www.w3.org/2005/Atom}form')
	if form:
		fieldset = form.find('{http://www.w3.org/2005/Atom}fieldset')
			
		for input in fieldset:
			inputObject = {
				'type': '',
				'token': '',
				'values': {}
			}
			default = input.find('{http://www.w3.org/2005/Atom}default')
			
			if default: # some tokens may not have a default field
				for value in default:
					inputObject["values"][("%s" % (value.tag).split('}')[1])] = value.text
			
			inputObject["type"] = input.attrib["type"]
			inputObject["token"] = input.attrib["token"]
			
			dashboardInputs.append(inputObject)
	
	dashboardInputs = "%s" % dashboardInputs
	return dashboardInputs.replace('},','},\n') 

		
def formatDashboardInput(namespace, dashboard, userInput):
	"""
		Modifies the dashboard XML with the user input and returns the modified XML.
		Parameters:
			namespace (required) = the name of the app where the dashboard is located
			dashboard (required) = the dashboard name
			userInput (required) = user input with token values. Must be in the form [{'token':'TOKEN_NAME','values':{'property1':'value1','property2':'value2'}}]
	"""
	print('Formatting XML Dashboard Input')
	XMLDashboard = getDashboardXML(namespace, dashboard)
	XMLDashboard=XMLDashboard.replace('![CDATA[<', '') # remove this xml tag so the xml can be parsed below
	XMLDashboard=XMLDashboard.replace(']]>', '')
	
	tree = ET.fromstring(XMLDashboard)
	entry = tree.find('{http://www.w3.org/2005/Atom}entry')
	content = entry.find('{http://www.w3.org/2005/Atom}content')
	dict = content.find('{http://dev.splunk.com/ns/rest}dict')

	global data
	for elem in dict:
		if elem.attrib["name"] == "eai:data":
			data = elem
			break

	form = data.find('{http://www.w3.org/2005/Atom}form')
	form = ET.tostring(form).decode('utf-8')

	# replace characters in the form so the api will understand it
	form = form.replace('ns0:', '')
	form = form.replace('ns1:', '')
	form = form.replace('\n', '')
	form = form.replace(' ', '%20')
	form = form.replace('<', '%26lt%3B')
 
	for input in eval(userInput):
		for item in input["values"]:
			form = form.replace(("$%s.%s$" % (input["token"], item)), input["values"][item])
	
	return form
	


# ---------------------------------------- PDF RENDERING METHODS ----------------------------------------
	
def getDashboardPdf(namespace, dashboard, *userInput):
	"""
		Gets a PDF rendering of a dashboard and saves it to '/pdf_files/<namespace>_<dashboard>.pdf'
		Parameters:
			namespace (required) = the name of the app where the dashboard is located
			dashboard (required) = the dashboard name
			userInput (optional) = user input with token values. Must be in the form [{'token':'TOKEN_NAME','values':{'property1':'value1','property2':'value2'}}]
	"""
	print("[GET DASHBOARD PDF]: namespace=%s, dashboard=%s" % (namespace, dashboard))
	
	# This is the url to be used when there is no user input and no tokens associated with the dashboard
	url = BASE_URL + ("/services/pdfgen/render?namespace=%s&input-dashboard=%s&paper-size=a4-landscape&include-splunk-logo=False" % (namespace, dashboard))
	
	# If there is user input, get the dashboard xml, modify it with the user input, and send to the pdfgen/render endpoint
	if userInput:
		XMLDashboard = formatDashboardInput(namespace, dashboard, userInput[0])
		url = BASE_URL + ("/services/pdfgen/render?input-dashboard-xml=%s&paper-size=a4-landscape&include-splunk-logo=False" % XMLDashboard)
	else:
		# If there are tokens associated with the dashboard, get the dashboard xml, modify it with the default token values, and send to the pdfgen/render endpoint
		optionalDashboardInputs = eval(listDashboardInputs(namespace, dashboard))
		
		if len(optionalDashboardInputs) > 0:
			XMLDashboard = formatDashboardInput(namespace, dashboard, "%s" % optionalDashboardInputs)
			url = BASE_URL + ("/services/pdfgen/render?input-dashboard-xml=%s&paper-size=a4-landscape&include-splunk-logo=False" % XMLDashboard)
			
	
	response, content = myhttp.request(
		url,
		'POST',
		headers={'Authorization':('Splunk %s' % SESSION_KEY)})
	
	# save the PDF locally with naming convention of: namespace_dashboard.pdf
	if response.status == 200:
		pdfFileName = ('%s\pdf_files\%s_%s.pdf' % (PATH, namespace, dashboard))
		pdfFile = open(pdfFileName,'wb')
		pdfFile.write(content)
		pdfFile.close()
		return pdfFileName
	else:
		raise Exception("Could not find dashboard with name '%s'" % dashboard)

	
def getReportPdf(report):
	"""
		Gets a PDF rendering of a report/saved search and saves it to '/pdf_files/<report>.pdf'.
		Uses the original time range of the report
		Parameters:
			report (required) = the name of the report
	"""
	print("[GET REPORT PDF] report=%s" % report)
	pdfFileName = ('%s\pdf_files\%s.pdf' % (PATH, report))
	report = report.replace(' ','%20')

	url = BASE_URL + ("/services/pdfgen/render?input-report=%s&paper-size=a4-landscape&include-splunk-logo=False" % report)

	response, content = myhttp.request(
		url,
		'POST',
		headers={'Authorization':('Splunk %s' % SESSION_KEY)})
		
	if response.status == 200:
		pdfFile = open(pdfFileName,'wb')
		pdfFile.write(content)
		pdfFile.close()
		return pdfFileName
	else:
		if '404' in content.decode('utf-8'):
			raise Exception("Could not find report with name '%s'" % report.replace('%20',' '))
		else:
			raise Exception("An error occurred while generating PDF for report '%s'" % content.decode('utf-8'))


def getSearchPdf(searchString):
	"""
		Gets a PDF rendering of an ad hoc search and saves it to '/pdf_files/search.pdf'.
		NOTE: this method can only return the default visualization
		Parameters:
			searchString (required) = the ad hoc search string in the Splunk Search Processing Language (SPL) 
	"""
	print("[GET SEARCH PDF] %s" % searchString)
	searchString = searchString.replace(' ','%20')

	url = BASE_URL + ("/services/pdfgen/render?input-search=%s&paper-size=a4-landscape&include-splunk-logo=False" % (searchString))

	response, content = myhttp.request(
		url,
		'POST',
		headers={'Authorization':('Splunk %s' % SESSION_KEY)})

	if response.status == 200:
		pdfFileName = ('%s\pdf_files\search.pdf' % PATH)
		pdfFile = open(pdfFileName,'wb')
		pdfFile.write(content)
		pdfFile.close()
		return pdfFileName
	else:
		raise Exception("%s" % content.decode('utf-8'))
		

def deletePdfFile(filePath):
	"""
		Deletes the dashboard PDF file saved in the local directory
		Parameters:
			filePath (required) = the path to the file to be deleted (TIP: pass in the output of one of the PDF rendering methods)
	"""
	os.remove(filePath)
	print("Deleted " + filePath)
	return


	
# ---------------------------------------- ALERT METHODS ----------------------------------------
	
def disableAlert(savedSearchName, disableDuration=0):
	"""
		Disables an alert.
		Parameters:
			savedSearchName (required) = the name of the saved search
			disableDuration (optional) = How long to disable the alert (in minutes). If not set, the alert must be enabled manually
	"""
	print("[DISABLE ALERT] alert=%s" % savedSearchName)
	# reformat saved search name for URL
	savedSearchName = savedSearchName.replace(' ', '%20')
	
	response, content = myhttp.request(
		BASE_URL + ("/services/saved/searches/%s?output_mode=json" % savedSearchName), 
		'POST', 
		headers={'Authorization':('Splunk %s' % SESSION_KEY)},
		body=urllib.parse.urlencode({'disabled':True}))

	decodedContent = json.loads(content.decode('utf-8'))
	savedSearchName = savedSearchName.replace('%20', ' ')
	
	if response.status == 200:
		if disableDuration:
			thread = threading.Thread(target=autoEnableAlert, args=(savedSearchName, disableDuration))
			thread.start()
			return("Successfully disabled '%s'. It will automatically be enabled after %s minutes" % (savedSearchName, disableDuration))
		else:
			return("Successfully disabled '%s'" % savedSearchName)
	else:
		errorMessage = json.loads(content.decode('utf-8'))["messages"][0]["text"]
		raise Exception(errorMessage)
		
		
def enableAlert(savedSearchName):
	"""
		Enables an alert.
		Parameters:
			savedSearchName (required) = the name of the saved search
	"""
	print("[ENABLE ALERT] alert=%s" % savedSearchName)
	# reformat saved search name for URL
	savedSearchName = savedSearchName.replace(' ', '%20')
	
	response, content = myhttp.request(
		BASE_URL + ("/services/saved/searches/%s?output_mode=json" % savedSearchName), 
		'POST', 
		headers={'Authorization':('Splunk %s' % SESSION_KEY)},
		body=urllib.parse.urlencode({'disabled':False}))

	decodedContent = json.loads(content.decode('utf-8'))
	
	if response.status == 200:
		return("Successfully enabled '%s'" % savedSearchName.replace('%20',' '))
	else:
		errorMessage = json.loads(content.decode('utf-8'))["messages"][0]["text"]
		raise Exception(errorMessage)
	

def autoEnableAlert(savedSearchName, disableDuration):
	"""
		Enables an alert after the specified time.
		Parameters:
			savedSearchName (required) = the name of the saved search
			disableDuration (required) = How long to disable the alert (in minutes)
	"""
	sleep(disableDuration * 60) # transform to minutes
	print("[AUTO ENABLE ALERT] " + enableAlert(savedSearchName))
	
	
def listDisabledAlerts(*searchString):
	"""
		Lists the names of disabled alerts. Returns results in JSON form.
		Parameters:
			searchString (optional) = filters results. searchString is NOT case sensitive
	"""
	print("[LIST DISABLED ALERTS]")
	response, content = myhttp.request(
		BASE_URL + "/services/saved/searches?output_mode=json&count=0", 
		'GET', 
		headers={'Authorization':('Splunk %s' % SESSION_KEY)})

	decodedContent = json.loads(content.decode('utf-8'))
	
	if response.status == 200:
		listOfDisabledAlerts = []
		
		if searchString:
			for entry in decodedContent["entry"]:
				if ("%s" % searchString).lower() in entry["name"].lower() and entry["content"]["actions"] and entry["content"]["disabled"]:
					listOfDisabledAlerts.append(entry["name"])
		else:
			for entry in decodedContent["entry"]:
				if entry["content"]["actions"] and entry["content"]["disabled"]:
					listOfDisabledAlerts.append(entry["name"])
		
		listOfDisabledAlerts = "%s" % listOfDisabledAlerts
		return listOfDisabledAlerts.replace(',',',\n')
	else:
		errorMessage = json.loads(content.decode('utf-8'))["messages"][0]["text"]
		raise Exception(errorMessage)
	

def rescheduleAlert(savedSearchName, cronSchedule):
	"""
		Reschedules an alert by passing in a cron schedule.
		Parameters:
			savedSearchName (required) = the name of the saved search
			cronSchedule (required) = a cron schedule (i.e. to run at 30 minutes past each hour '30 * * * *')
	"""
	print("[RESCHEDULE ALERT] alert=%s, schedule=%s" % (savedSearchName, cronSchedule))
	# reformat saved search name for URL
	savedSearchName = savedSearchName.replace(' ', '%20')
	
	response, content = myhttp.request(
		BASE_URL + ("/services/saved/searches/%s?output_mode=json" % savedSearchName), 
		'POST', 
		headers={'Authorization':('Splunk %s' % SESSION_KEY)},
		body=urllib.parse.urlencode({'cron_schedule':cronSchedule}))

	decodedContent = json.loads(content.decode('utf-8'))
	
	if response.status == 200:
		return("Successfully rescheduled '%s' with cron schedule: '%s'" % (savedSearchName.replace('%20',' '), cronSchedule))
	else:
		errorMessage = json.loads(content.decode('utf-8'))["messages"][0]["text"]
		raise Exception(errorMessage)
	
	
	
# ---------------------------------------- OTHER METHODS ----------------------------------------	
	
def listAppNames(*searchString):
	"""
		Lists the app names for all apps in the current Splunk instance
		Parameters:
			searchString (optional) = filters results. searchString is NOT case sensitive
	"""
	print("[LIST APP NAMES]")
	response, content = myhttp.request(
		BASE_URL + "/services/apps/local?output_mode=json&count=0", 
		'GET', 
		headers={'Authorization':('Splunk %s' % SESSION_KEY)})

	decodedContent = json.loads(content.decode('utf-8'))
	
	if response.status == 200:
		listOfApps = []
		
		if searchString:
			for entry in decodedContent["entry"]:
				if ("%s" % searchString).lower() in entry["name"].lower():
					listOfApps.append(entry["name"])
		else:
			for entry in decodedContent["entry"]:
				listOfApps.append(entry["name"])
		
		listOfApps = "%s" % listOfApps
		return listOfApps.replace(',',',\n')
	else:
		errorMessage = json.loads(content.decode('utf-8'))["messages"][0]["text"]
		raise Exception(errorMessage)
	
	
	
	
	
	
