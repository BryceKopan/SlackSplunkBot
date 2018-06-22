import re, inspect
import SlackAPI as Slack
import commands.BotCommands as BotCommands
import commands.SplunkCommands as SplunkCommands

MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

def parseBotCommands(slackEvents, botID):
	"""
		Parses a list of events coming from the Slack RTM API to find bot commands.
		If a bot command is found, this function returns a tuple of command and channel.
		If its not found, then this function returns None, None.
	"""
	for event in slackEvents:
		if event["type"] == "message" and not "subtype" in event:
			userID, message = parseDirectMention(event["text"])
			if userID == botID:
				return message, event["channel"]
	return None, None
	
def parseDirectMention(messageText):
	"""
		Finds a direct mention (a mention that is at the beginning) in message text
		and returns the user ID which was mentioned. If there is no direct mention, returns None
	"""
	matches = re.search(MENTION_REGEX, messageText)
	# the first group contains the username, the second group contains the remaining message
	return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handleCommand(command, channel):
	botCommands = []
	botCommands.extend(inspect.getmembers(BotCommands, inspect.isfunction))
	botCommands.extend(inspect.getmembers(SplunkCommands, inspect.isfunction))
	
	for commandString, commandFunction in botCommands:
		commandString = commandString.replace("_", " ")
		if(command.startswith(commandString)):
			commandParameters = command.split(commandString, 1)[1].lstrip()
			commandFunction(commandParameters, channel)
			return
	
	if(command.startswith("help")):
		for commandString, commandFunction in botCommands:
			Slack.postMessage(commandString.replace("_", " "), channel)
	else:
		Slack.postMessage("Not sure what you mean. Try *{}*.".format("help"), channel)
	
	