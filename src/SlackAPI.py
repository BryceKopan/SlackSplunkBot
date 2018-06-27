import warnings
from slackclient import SlackClient

slackClient = None

def connect(botToken):
	global slackClient 
	slackClient = SlackClient(botToken)
	if not slackClient.rtm_connect(with_team_state=False):
		print("Connection failed. Exception traceback printed above.")
		
def getBotID():
	with warnings.catch_warnings():
		warnings.simplefilter("ignore")
		return slackClient.api_call("auth.test")["user_id"]

def getSlackEvents():
	return slackClient.rtm_read()
	
def postMessage(message, channel, formatting = True):
	if not formatting:
		message = "```" + message + "```"
	
	with warnings.catch_warnings():
		warnings.simplefilter("ignore")
		try:
			slackClient.api_call(
			"chat.postMessage",
			channel=channel,
			text=message
			)
		except Exception:
			print("\nError Posting Message\n")
			raise
			
def postImage(image_path, image_title, channel):
	with warnings.catch_warnings():
		warnings.simplefilter("ignore")
		try:
			with open(image_path, 'rb') as file_content:
				slackClient.api_call(
					"files.upload",
					channels=channel,
					file=file_content,
					title=image_title
				)
		except Exception:
			print("\nError Posting Image\n")
			raise