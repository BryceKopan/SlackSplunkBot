import re
import SimpleHipChat as HipChat
import Util

def handleCommand(command, channel):
	commandString, commandFunction = Util.getCommandFunction(command)
	if(commandString and commandFunction):
		commandVariables = command.split(commandString, 1)[1].lstrip()
		commandParameters = parseCommandVariables(commandVariables)
		commandFunction(commandParameters, channel)
		return
	
	HipChat.postNotification("Not sure what you mean. Try {}.".format('help'), channel)
		
def parseBotCommands(events, trigger):
	"""
		Parses a list of events coming from the Slack RTM API to find bot commands.
		If a bot command is found, this function returns a tuple of command and channel.
		If its not found, then this function returns None, None.
	"""
	for event in events['items']:#events:
		if event['type'] == 'message' or event['type'] == 'notification': #and not 'subtype' in event:
			triggered, message = parseDirectMention(event['message'], trigger)#event['text'])
			if triggered:
				return message, event['channel']
	return None, None
	
def parseDirectMention(messageText, trigger):
	if messageText.startswith(trigger):
		return True, messageText.split(trigger)[1].strip()
	else:
		return False, None
	
def parseCommandVariables(unparsedVariables):
	parameters = unparsedVariables.split(",")
	parameters = list(map(str.strip, parameters))
	
	if(parameters[0] == '' and len(parameters) == 1):
			parameters = []
			
	return parameters
	# parameters = []
	# options = []

	# splitVariables = unparsedVariables.split("-", 1)
	# if(splitVariables[0] != ""):
		# parameters = splitVariables[0].split(",")
		# parameters = list(map(str.strip, parameters))
	# if len(splitVariables) > 1:
		# options = splitVariables[1].split("-")
		# options = list(map(str.strip, options))
	
	# return parameters, options