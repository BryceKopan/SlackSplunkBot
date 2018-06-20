import re, inspect
import SlackAPI as Slack
import commands.BotCommands as BotCommands

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
	botCommands = inspect.getmembers(BotCommands, inspect.isfunction)
	
	# commandNoSpaces = command.replace(" ", "_")

	# print(type(command))
	# print(command)
	# print(commandNoSpaces)
	
	for commandString, commandFunction in botCommands:
		if(commandNoSpaces.startswith(commandString)):
			commandParameters = command.split(commandString, 1)[1].lstrip()
			commandFunction(channel, commandParameters)
			return
	
"""def handleCommand(command, channel):
	# Commands	
	if command.startswith("print"):
		Slack.postMessage(command.split("print", 1)[1], channel)

	elif command.startswith("help"):
		Slack.postMessage("I don't know anything, figure it out. :)", channel)

	elif command.startswith("adminhelp"):
		Slack.postMessage("Commands: restart, shutdown", channel)

	elif command.startswith("restart"):
		Slack.postMessage("Restarting", channel)
		try:
			os.execl(sys.executable, 'python', __file__, *sys.argv[1:])
		except Exception as e:
			Slack.postMessage("Error Restarting", channel)
			print (e)

	elif command.startswith("shutdown"):
		Slack.postMessage("Shutting Down", channel)
		sys.exit("Shutdown command used")

	elif command.startswith("what do you look like?"):
		Slack.postImage("SplunkBot.png", "Self Portrait", channel)

	else:
		Slack.postMessage("Not sure what you mean. Try *{}*.".format("help"), channel)
"""
