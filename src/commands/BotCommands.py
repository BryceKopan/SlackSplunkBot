import SlackAPI as Slack

def help(channel, commandParameters):
	Slack.postMessage("New Command Structure Success", channel)
	
def command_with_spaces(channel, commandParameters):
	Slack.postMessage("Wooooo", channel)