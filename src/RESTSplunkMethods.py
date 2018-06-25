import os, urllib, httplib2, json 
from time import sleep
import xml.etree.ElementTree as ET
from xml.dom import minidom

baseurl = None
user = None
myhttp = httplib2.Http(disable_ssl_certificate_validation=True)
sessionKey = None
searchTTL = 10

# Creates a connection with a Splunk enterprise instance and sets a global session key to be used in subsequent requests
def connect(urlPrefix, username, password):
	global baseurl, user
	user = username
	baseurl = urlPrefix
	
	response, content = myhttp.request(
		baseurl + '/services/auth/login',
		'POST',
		headers={},
		body=urllib.parse.urlencode({'username':username, 'password':password, 'autoLogin':True}))
	
	if response.status == 200:
		global sessionKey
		sessionKey = minidom.parseString(content).getElementsByTagName('sessionKey')[0].childNodes[0].nodeValue
		return
	else:
		raise Exception("Service returned %s while trying to connect" % response.status)


# ---------------------------------------- SEARCH METHODS ----------------------------------------	
# Repeatedly retrieves the status of a search until the search completes or it times out (search timeout controlled by the 'searchTTL' variable set above) 
def getSearchStatus(sid):
	isNotDone = True
	elapsedTime = 0
	
	while isNotDone and elapsedTime < searchTTL:
		content = myhttp.request(
			(baseurl + "/services/search/jobs/%s?output_mode=json" % sid), 
			'GET', 
			headers={'Authorization':('Splunk %s' % sessionKey)})[1]
		
		searchStatus = json.loads(content.decode('utf-8'))
		
		if not searchStatus["entry"][0]["content"]["isDone"]:
			elapsedTime += 1
			sleep(1)
		else:
			isNotDone = False
	
	if elapsedTime >= searchTTL:
		raise Exception("Search took too long. Try narrowing your time range")
	else:
		return

		
# Gets the results of a previously run search. Returns results in JSON form	
def getSearchResults(sid):
	getSearchStatus(sid)
	
	response, content = myhttp.request(
		(baseurl + "/services/search/jobs/%s/results?output_mode=json&count=0" % sid), 
		'GET', 
		headers={'Authorization':('Splunk %s' % sessionKey)})
	
	if response.status == 200:
		return json.loads(content.decode('utf-8'))["results"]
	else:
		errorMessage = json.loads(content.decode('utf-8'))["messages"][0]["text"]
		raise Exception(errorMessage)
	
	
# Lists the names of saved searches. Returns results in JSON form
# Optional searchString to filter results
def listSavedSearches(*searchString):
	response, content = myhttp.request(
		baseurl + "/services/saved/searches?output_mode=json&count=0", 
		'GET', 
		headers={'Authorization':('Splunk %s' % sessionKey)})

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
def runSavedSearch(savedSearchName):
	# reformat saved search name for URL
	savedSearchName = savedSearchName.replace(' ', '%20')

	response, content = myhttp.request(
		(baseurl + "/services/saved/searches/%s/dispatch?output_mode=json" % savedSearchName), 
		'POST', 
		headers={'Authorization':('Splunk %s' % sessionKey)})
	
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
		(baseurl + '/services/search/jobs?output_mode=json&auto_cancel=%s' % searchTTL),
		'POST',
		headers={'Authorization': 'Splunk %s' % sessionKey},
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

# Gets a PDF rendering of a dashboard. Optional userInput for modifying dashboard tokens	
def getDashboardPDF(dashboard, namespace, *userInput):
	print("Working on getting dashboard PDF. This may take a while.")
	
	# This is the url to be used when there is no user input.
	# NOTE: If a dashboard panel relies on a token, that panel will not render with this url. Requires user input
	url = baseurl + ("/services/pdfgen/render?input-dashboard=%s&namespace=%s&paper-size=a4-landscape" % (dashboard, namespace))
	
	# If there is user input, get the dashboard xml, modify it with the user input, and send to the pdfgen/render endpoint
	if userInput:
		XMLDashboard = formatXMLDashboardInput(dashboard, namespace, userInput)
		url = baseurl + ("/services/pdfgen/render?input-dashboard-xml=%s&paper-size=a4-landscape" % XMLDashboard)	
	
	response, content = myhttp.request(
		url,
		'POST',
		headers={'Authorization':('Splunk %s' % sessionKey)})
	
	# save the PDF locally with naming convention of: namespace_dashboard.pdf
	if response.status == 200:
		pdfFileName = ('pdf_files/%s_%s.pdf' % (namespace, dashboard))
		pdfFile = open(pdfFileName,'wb')
		pdfFile.write(content)
		pdfFile.close()
		return pdfFileName
	else:
		raise Exception("Could not find dashboard with name '%s'" % dashboard)
	
	
# Lists the names of dashboards in the specified app. Returns results in JSON form	
def listDashboardNames(appName):
	response, content = myhttp.request(
		(baseurl + "/servicesNS/%s/%s/data/ui/views?output_mode=json" % (user, appName)), 
		'GET', 
		headers={'Authorization':('Splunk %s' % sessionKey)})
	
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

		
# Deletes the dashboard PDF file saved in the local directory		
# Pass the output of getDashboardPDF as filePath
def deleteDashboardPDFFile(filePath):
	os.remove(filePath)
	print("Deleted " + filePath)
	return
	
	
# Gets the specified dashboard XML
def getDashboardXML(dashboard, namespace):
	response, content = myhttp.request(
		baseurl + ("/servicesNS/%s/%s/data/ui/views/%s" % (user, namespace, dashboard)), 
		'GET',
		headers={'Authorization':('Splunk %s' % sessionKey)})
	
	decodedContent = content.decode('utf-8')
	
	if response.status == 200:
		return decodedContent
	else:
		print(decodedContent)
		errorMessage = decodedContent["messages"][0]["text"]
		raise Exception(errorMessage)
	
	
# Lists the dashboard tokens available to the specified dashboard. Returns results in JSON form
def listOptionalDashboardInputs(dashboard, namespace):
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
			'defaults': {}
		}
		default = input.find('{http://www.w3.org/2005/Atom}default')
		for value in default:
			inputObject["defaults"][("%s" % (value.tag).split('}')[1])] = value.text
		
		inputObject["type"] = input.attrib["type"]
		inputObject["token"] = input.attrib["token"]
		
		optionalDashboardInputs.append(inputObject)
		
	return optionalDashboardInputs 

	
# Modifies the dashboard XML with the user input and returns the modified XML	
def formatXMLDashboardInput(dashboard, namespace, userInput):
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
 
	for input in userInput[0]:
		for item in input["values"]:
			form = form.replace(("$%s.%s$" % (input["token"], item)), input["values"][item])
	
	return form

	
# Lists the app names for all apps in the current Splunk instance
# Optional searchString to filter results	
def listAppNames(*searchString):	
	response, content = myhttp.request(
		baseurl + "/services/apps/local?output_mode=json", 
		'GET', 
		headers={'Authorization':('Splunk %s' % sessionKey)})

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
	
	
# Gets a PDF rendering of a report
# Uses the original time range of the report
def getReportPDF(report, namespace):
	print("Working on getting report PDF. This may take a while.")
	pdfFileName = ('pdf_files/%s_%s.pdf' % (namespace, report))
	report = report.replace(' ','%20')

	url = baseurl + ("/services/pdfgen/render?input-report=%s&namespace=%s&paper-size=a4-landscape" % (report, namespace))

	response, content = myhttp.request(
		url,
		'POST',
		headers={'Authorization':('Splunk %s' % sessionKey)})

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

	url = baseurl + ("/services/pdfgen/render?input-search=%s&paper-size=a4-landscape" % (searchString))

	response, content = myhttp.request(
		url,
		'POST',
		headers={'Authorization':('Splunk %s' % sessionKey)})

	if response.status == 200:
		pdfFileName = 'pdf_files/search.pdf'
		pdfFile = open(pdfFileName,'wb')
		pdfFile.write(content)
		pdfFile.close()
		return pdfFileName
	else:
		raise Exception("%s" % content.decode('utf-8'))

