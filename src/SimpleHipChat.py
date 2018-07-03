from __future__ import print_function
import requests
import sys
import json
from os import path
from requests_toolbelt import MultipartEncoder

TOKEN = None
HOST = None
ROOM = '18'
Session = None
lastProcessedMessageID = None

def connect(token, host):
	global TOKEN, HOST, ROOM, Session, lastProcessedMessageID
	TOKEN = token
	HOST = host
	Session = requests.Session()
	Session.verify = False
	
	url = 'https://{0}/v2/room/{1}/history/latest'.format(HOST, ROOM)
	headers = {'Authorization':'Bearer ' + TOKEN}
	url += '?max-results=1'
	response = Session.get(url, headers=headers)
	response.raise_for_status()
	results = json.loads(response.text)
	lastProcessedMessageID = results['items'][0]['id']
	print(results['items'][0]['message'])
	print(results['items'][0]['id'])
	
def getEvents():
	global lastProcessedMessageID
	
	url = 'https://{0}/v2/room/{1}/history/latest'.format(HOST, ROOM)
	headers = {'Authorization':'Bearer ' + TOKEN}
	url += '?not-before=' + lastProcessedMessageID
	response = Session.get(url, headers=headers)
	response.raise_for_status()
	results = json.loads(response.text)
	for result in results['items']:
		result['channel'] = ROOM
	headers = response.headers
	print(headers['X-Ratelimit-Limit'])
	print(headers['X-Ratelimit-Remaining'])
	
	lastProcessedMessageID = results['items'][len(results['items']) - 1]['id']
	del results['items'][0]
	return results
	
def postMessage(message, room):
	url = 'https://{0}/v2/room/{1}/message'.format(HOST, ROOM)
	headers = {'Authorization':'Bearer ' + TOKEN}
	payload = {
		'message': message
	}
	response = Session.post(url, data=json.dumps(payload), headers=headers)
	response.raise_for_status()
	
def postFile(filePath, room = 18):
	url = 'https://{0}/v2/room/{1}/share/file'.format(HOST, ROOM)
	headers = {'Content-type':'multipart/related; boundary=boundary123456'}
	headers['Authorization'] = 'Bearer ' + TOKEN

	m = MultipartRelatedEncoder(fields={'metadata' : (None, '', 'application/json; charset=UTF-8'),
										'file'     : (path.basename(filePath), open(filePath, 'rb'), 'text/csv')})
										
	headers['Content-Type'] = m.content_type
	
	r = Session.post(url, data=m, headers=headers)
	
class MultipartRelatedEncoder(MultipartEncoder):
	"""A multipart/related encoder"""
	@property
	def content_type(self):
		return str('multipart/related; boundary={0}'.format(self.boundary_value))

	def _iter_fields(self):
		# change content-disposition from form-data to attachment
		for field in super(MultipartRelatedEncoder, self)._iter_fields():
			content_type = field.headers['Content-Type']
			field.make_multipart(content_disposition = 'attachment',
								 content_type        = content_type)
			yield field
	
# from __future__ import print_function
# import requests
# import sys
# import json

# def hipchat_notify(token, room, message, color='yellow', notify=False,
				   # format='text', host='api.hipchat.com'):
	# """Send notification to a HipChat room via API version 2
	# Parameters
	# ----------
	# token : str
		# HipChat API version 2 compatible token (room or user token)
	# room: str
		# Name or API ID of the room to notify
	# message: str
		# Message to send to room
	# color: str, optional
		# Background color for message, defaults to yellow
		# Valid values: yellow, green, red, purple, gray, random
	# notify: bool, optional
		# Whether message should trigger a user notification, defaults to False
	# format: str, optional
		# Format of message, defaults to text
		# Valid values: text, html
	# host: str, optional
		# Host to connect to, defaults to api.hipchat.com
	# """

	# if len(message) > 10000:
		# raise ValueError('Message too long')
	# if format not in ['text', 'html']:
		# raise ValueError("Invalid message format '{0}'".format(format))
	# if color not in ['yellow', 'green', 'red', 'purple', 'gray', 'random']:
		# raise ValueError("Invalid color {0}".format(color))
	# if not isinstance(notify, bool):
		# raise TypeError("Notify must be boolean")

	# url = "https://{0}/v2/room/{1}/notification".format(host, room)
	# headers = {'Content-type': 'application/json'}
	# headers['Authorization'] = "Bearer " + token
	# payload = {
		# 'message': message,
		# 'notify': notify,
		# 'message_format': format,
		# 'color': color
	# }
	# session = requests.Session()
	# session.verify = False
	# r = session.post(url, data=json.dumps(payload), headers=headers)
	# r.raise_for_status()


# try:
	# connect('', "hipchat.ercot.com")
	# postMessage("This is a test message", ROOM)
# except Exception as e:
		# msg = "[ERROR] HipChat notify failed: '{0}'".format(e)
		# print(msg, file=sys.stderr)
		# sys.exit(1)