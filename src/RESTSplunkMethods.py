import os, urllib, httplib2, json 
from time import sleep
import xml.etree.ElementTree as ET
from xml.dom import minidom

baseurl = 'https://splunk-itest.ercot.com:8089'
username = os.environ.get('SPLUNK_USERNAME')
password = os.environ.get('SPLUNK_PASSWORD')
myhttp = httplib2.Http(disable_ssl_certificate_validation=True)
sessionKey = None
searchTTL = 10


def connect():
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

		
# dashboard name is not always the same as the dashboard display name. Run listDashboardNames to get the correct name.
# namespace is the app where the dashboard is located.	
def getDashboardPDF(dashboard, namespace, *userInput):
	print("Working on getting dashboard PDF. This may take a while.")
	
	url = baseurl + ("/services/pdfgen/render?input-dashboard=%s&namespace=%s&paper-size=a4-landscape" % (dashboard, namespace))
	
	if userInput:
		XMLDashboard = formatXMLDashboardInput(dashboard, namespace, userInput)
		url = baseurl + ("/services/pdfgen/render?input-dashboard-xml=%s&paper-size=a4-landscape" % XMLDashboard)	
	
	response, content = myhttp.request(
		url,
		'POST',
		headers={'Authorization':('Splunk %s' % sessionKey)})
	
	if response.status == 200:
		pdfFileName = ('pdf_files/%s_%s.pdf' % (namespace, dashboard))
		pdfFile = open(pdfFileName,'wb')
		pdfFile.write(content)
		pdfFile.close()
		return pdfFileName
	else:
		raise Exception("Could not find dashboard with name '%s'" % dashboard)
	
	
def listDashboardNames(appName):
	response, content = myhttp.request(
		(baseurl + "/servicesNS/%s/%s/data/ui/views?output_mode=json" % (username, appName)), 
		'GET', 
		headers={'Authorization':('Splunk %s' % sessionKey)})
	
	decodedContent = json.loads(content.decode('utf-8'))
	
	if response.status == 200:
		listOfDashboards = []
		
		for entry in decodedContent["entry"]:
			if entry["content"]["isDashboard"]:
				listOfDashboards.append(entry["name"])
		
		return listOfDashboards
	else:
		errorMessage = decodedContent["messages"][0]["text"]
		raise Exception(errorMessage)
		
# pass the output of getDashboardPDF as filePath
def deleteDashboardPDFFile(filePath):
	os.remove(filePath)
	print("Deleted " + filePath)
	return
	

def getDashboardXML(dashboard, namespace):
	response, content = myhttp.request(
		baseurl + ("/servicesNS/%s/%s/data/ui/views/%s" % (username, namespace, dashboard)), 
		'GET',
		headers={'Authorization':('Splunk %s' % sessionKey)})
	
	decodedContent = content.decode('utf-8')
	
	if response.status == 200:
		return decodedContent
	else:
		errorMessage = decodedContent["messages"][0]["text"]
		raise Exception(errorMessage)
	

def listOptionalDashboardInputs(dashboard, namespace):
	XMLDashboard = getDashboardXML(dashboard, namespace)
	XMLDashboard=XMLDashboard.replace('![CDATA[<', '')
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
		optionalDashboardInputs.append(input.attrib)
		
	return optionalDashboardInputs 

	
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
		

def formatXMLDashboardInput(dashboard, namespace, userInput):
	print('[INFO] Formatting XML Dashboard Input')
	XMLDashboard = getDashboardXML(dashboard, namespace)
	XMLDashboard=XMLDashboard.replace('![CDATA[<', '')
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
 
	# UNDER CONSTRUCTION. Currently only supports a TIME token
	for input in userInput[0]:
		form = form.replace("$TIME.earliest$", input["earliest"])
		form = form.replace("$TIME.latest$", input["latest"])
	
	return form
	

