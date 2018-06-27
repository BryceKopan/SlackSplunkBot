import os, urllib, httplib2, json, threading 
from time import sleep
import xml.etree.ElementTree as ET
from xml.dom import minidom

BASE_URL = None
USER = None
SESSION_KEY = None
SEARCH_TTL = 10
myhttp = httplib2.Http(disable_ssl_certificate_validation=True)

# Creates a connection with a Splunk enterprise instance and sets a global session key to be used in subsequent requests
def connect(urlPrefix, username, password):
	global BASE_URL, USER
	BASE_URL = urlPrefix
	USER = username
	
	response, content = myhttp.request(
		BASE_URL + '/services/auth/login',
		'POST',
		headers={},
		body=urllib.parse.urlencode({'username':username, 'password':password, 'autoLogin':True}))
	
	if response.status == 200:
		global SESSION_KEY
		SESSION_KEY = minidom.parseString(content).getElementsByTagName('sessionKey')[0].childNodes[0].nodeValue
		return
	else:
		raise Exception("Service returned %s while trying to connect" % response.status)


		
# ---------------------------------------- SEARCH METHODS ----------------------------------------	

# Repeatedly retrieves the status of a search until the search completes or it times out (search timeout controlled by the 'SEARCH_TTL' variable set above) 
def getSearchStatus(sid):
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

		
# Gets the results of a previously run search. Returns results in JSON form	
def getSearchResults(sid):
	getSearchStatus(sid)
	
	response, content = myhttp.request(
		(BASE_URL + "/services/search/jobs/%s/results?output_mode=json&count=0" % sid), 
		'GET', 
		headers={'Authorization':('Splunk %s' % SESSION_KEY)})
	
	if response.status == 200:
		return json.loads(content.decode('utf-8'))["results"]
	else:
		errorMessage = json.loads(content.decode('utf-8'))["messages"][0]["text"]
		raise Exception(errorMessage)
	
	
# Lists the names of saved searches. Returns results in JSON form
# Optional searchString to filter results. searchString is NOT case sensitive
def listSavedSearches(*searchString):
	response, content = myhttp.request(
		BASE_URL + "/services/saved/searches?output_mode=json&count=0", 
		'GET', 
		headers={'Authorization':('Splunk %s' % SESSION_KEY)})

	decodedContent = json.loads(content.decode('utf-8'))
	
	if response.status == 200:
		listOfSavedSearches = []
		
		if searchString:
			for entry in decodedContent["entry"]:
				if ("%s" % searchString).lower() in entry["name"].lower():
					listOfSavedSearches.append(entry["name"])
		else:
			for entry in decodedContent["entry"]:
				listOfSavedSearches.append(entry["name"])
				
		return listOfSavedSearches
	else:
		errorMessage = json.loads(content.decode('utf-8'))["messages"][0]["text"]
		raise Exception(errorMessage)
	
	
# Runs a saved search. Returns results in JSON form
# Run 'listSavedSearches' to get the correct name
# Optional triggerActions parameter
def runSavedSearch(savedSearchName, triggerActions=False):
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

		
# Accepts ad hoc search strings. Returns results in JSON form	
def runSearch(searchString): 
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

# Lists the names of dashboards in the specified app. Returns results in JSON form	
def listDashboardNames(namespace):
	response, content = myhttp.request(
		(BASE_URL + "/servicesNS/%s/%s/data/ui/views?output_mode=json" % (USER, namespace)), 
		'GET', 
		headers={'Authorization':('Splunk %s' % SESSION_KEY)})
	
	decodedContent = json.loads(content.decode('utf-8'))
	
	if response.status == 200:
		listOfDashboards = []
		
		for entry in decodedContent["entry"]:
			if entry["content"]["isDashboard"]: # check to make sure this is a dashboard entry
				listOfDashboards.append(entry["name"])
		
		return listOfDashboards
	else:
		errorMessage = decodedContent["messages"][0]["text"]
		raise Exception(errorMessage)

		
# Gets the specified dashboard XML
def getDashboardXML(dashboard, namespace):
	response, content = myhttp.request(
		BASE_URL + ("/servicesNS/%s/%s/data/ui/views/%s" % (USER, namespace, dashboard)), 
		'GET',
		headers={'Authorization':('Splunk %s' % SESSION_KEY)})
	
	decodedContent = content.decode('utf-8')
	
	if response.status == 200:
		return decodedContent
	else:
		print(decodedContent)
		errorMessage = decodedContent["messages"][0]["text"]
		raise Exception(errorMessage)
	
	
# Lists the dashboard tokens available to the specified dashboard. Returns results in JSON form
def listDashboardInputs(dashboard, namespace):
	XMLDashboard = getDashboardXML(dashboard, namespace)
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
	fieldset = form.find('{http://www.w3.org/2005/Atom}fieldset')
		
	optionalDashboardInputs = []
		
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
		
		optionalDashboardInputs.append(inputObject)
		
	return optionalDashboardInputs 

	
# Modifies the dashboard XML with the user input and returns the modified XML	
def formatDashboardInput(dashboard, namespace, userInput):
	print('[INFO] Formatting XML Dashboard Input')
	XMLDashboard = getDashboardXML(dashboard, namespace)
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
 
	for input in userInput:
		for item in input["values"]:
			form = form.replace(("$%s.%s$" % (input["token"], item)), input["values"][item])
	
	return form
	


# ---------------------------------------- PDF RENDERING METHODS ----------------------------------------
	
# Gets a PDF rendering of a dashboard. Optional userInput for modifying dashboard tokens
# Example userInput: [{"token":"TIME","values":{"earliest":"0","latest":""}}]	
def getDashboardPDF(dashboard, namespace, *userInput):
	print("Working on getting dashboard PDF. This may take a while.")
	
	# This is the url to be used when there is no user input and no tokens associated with the dashboard
	url = BASE_URL + ("/services/pdfgen/render?input-dashboard=%s&namespace=%s&paper-size=a4-landscape" % (dashboard, namespace))
	
	# If there is user input, get the dashboard xml, modify it with the user input, and send to the pdfgen/render endpoint
	if userInput:
		XMLDashboard = formatDashboardInput(dashboard, namespace, userInput[0])
		url = BASE_URL + ("/services/pdfgen/render?input-dashboard-xml=%s&paper-size=a4-landscape" % XMLDashboard)
	else:
		# If there are tokens associated with the dashboard, get the dashboard xml, modify it with the default token values, and send to the pdfgen/render endpoint
		optionalDashboardInputs = listDashboardInputs(dashboard, namespace)
		
		if len(optionalDashboardInputs) > 0:
			XMLDashboard = formatDashboardInput(dashboard, namespace, optionalDashboardInputs)
			url = BASE_URL + ("/services/pdfgen/render?input-dashboard-xml=%s&paper-size=a4-landscape" % XMLDashboard)
			
	
	response, content = myhttp.request(
		url,
		'POST',
		headers={'Authorization':('Splunk %s' % SESSION_KEY)})
	
	# save the PDF locally with naming convention of: namespace_dashboard.pdf
	if response.status == 200:
		pdfFileName = ('pdf_files/%s_%s.pdf' % (namespace, dashboard))
		pdfFile = open(pdfFileName,'wb')
		pdfFile.write(content)
		pdfFile.close()
		return pdfFileName
	else:
		raise Exception("Could not find dashboard with name '%s'" % dashboard)

	
# Gets a PDF rendering of a report/saved search
# Uses the original time range of the report
def getReportPDF(report):
	print("Working on getting report PDF. This may take a while.")
	pdfFileName = ('pdf_files/%s.pdf' % report)
	report = report.replace(' ','%20')

	url = BASE_URL + ("/services/pdfgen/render?input-report=%s&paper-size=a4-landscape" % report)

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


# Gets a PDF rendering of an ad hoc search
# NOTE: can only return the default visualization			
def getSearchPDF(searchString):
	print("Working on getting search PDF. This may take a while.")
	searchString = searchString.replace(' ','%20')

	url = BASE_URL + ("/services/pdfgen/render?input-search=%s&paper-size=a4-landscape" % (searchString))

	response, content = myhttp.request(
		url,
		'POST',
		headers={'Authorization':('Splunk %s' % SESSION_KEY)})

	if response.status == 200:
		pdfFileName = 'pdf_files/search.pdf'
		pdfFile = open(pdfFileName,'wb')
		pdfFile.write(content)
		pdfFile.close()
		return pdfFileName
	else:
		raise Exception("%s" % content.decode('utf-8'))
		

# Deletes the dashboard PDF file saved in the local directory		
# Pass the output of one of the PDF rendering methods as filePath
def deletePDFFile(filePath):
	os.remove(filePath)
	print("Deleted " + filePath)
	return


	
# ---------------------------------------- ALERT METHODS ----------------------------------------

# Optional disableDuration(in minutes). autoEnableAlert will enable the alert after the disableDuration
# If disableDuration is not set, the alert must be enabled manually	
def disableAlert(savedSearchName, disableDuration=0):
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
	sleep(disableDuration * 60) # transform to minutes
	# Could have this call the SlackAPI method "postMessage"
	print("[AUTO ENABLE ALERT] " + enableAlert(savedSearchName))
	
	
# Lists the names of disabled alerts. Returns results in JSON form
# Optional searchString to filter results. searchString is NOT case sensitive
def listDisabledAlerts(*searchString):
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
				
		return listOfDisabledAlerts
	else:
		errorMessage = json.loads(content.decode('utf-8'))["messages"][0]["text"]
		raise Exception(errorMessage)
	

# reschedule an alert by passing in a cron schedule
def rescheduleAlert(savedSearchName, cronSchedule):
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
	
# Lists the app names for all apps in the current Splunk instance
# Optional searchString to filter results. searchString is NOT case sensitive	
def listAppNames(*searchString):	
	response, content = myhttp.request(
		BASE_URL + "/services/apps/local?output_mode=json", 
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
				
		return listOfApps
	else:
		errorMessage = json.loads(content.decode('utf-8'))["messages"][0]["text"]
		raise Exception(errorMessage)
	
	
	
	
	
	
