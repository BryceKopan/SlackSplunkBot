import os, urllib, httplib2, json 
from time import sleep
from xml.dom import minidom

baseurl = 'https://localhost:8089'
username = os.environ.get('SPLUNK_USERNAME')
password = os.environ.get('SPLUNK_PASSWORD')
myhttp = httplib2.Http(disable_ssl_certificate_validation=True)
sessionKey = None

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
	while isNotDone:
		content = myhttp.request(
			(baseurl + "/services/search/jobs/%s?output_mode=json" % sid), 
			'GET', 
			headers={'Authorization':('Splunk %s' % sessionKey)})[1]
		
		searchStatus = json.loads(content.decode('utf-8'))
		
		if not searchStatus["entry"][0]["content"]["isDone"]:
			sleep(1)
		else:
			isNotDone = False
	
	return

	
def getSearchResults(sid):
	getSearchStatus(sid)
	
	response, content = myhttp.request(
		(baseurl + "/services/search/jobs/%s/results?output_mode=json" % sid), 
		'GET', 
		headers={'Authorization':('Splunk %s' % sessionKey)})
	
	if response.status == 200:
		return json.loads(content.decode('utf-8'))["results"]
	else:
		errorMessage = json.loads(content.decode('utf-8'))["messages"][0]["text"]
		raise Exception(errorMessage)
	

def listSavedSearches():
	response, content = myhttp.request(
		baseurl + "/services/saved/searches?output_mode=json", 
		'GET', 
		headers={'Authorization':('Splunk %s' % sessionKey)})

	decodedContent = json.loads(content.decode('utf-8'))
	
	if response.status == 200:
		listOfSavedSearches = []
		
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
		baseurl + '/services/search/jobs?output_mode=json',
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
def getDashboardPDF(dashboard,namespace):
	print("Working on getting dashboard PDF. This may take a while.")
	response, content = myhttp.request(
		baseurl + ("/services/pdfgen/render?input-dashboard=%s&namespace=%s&paper-size=a4-landscape" % (dashboard, namespace)), 
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
	
	
def listDashboardNames(user, appName):
	response, content = myhttp.request(
		(baseurl + "/servicesNS/%s/%s/data/ui/views?output_mode=json" % (user, appName)), 
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
