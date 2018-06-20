import os, time, traceback
import SlackAPI as Slack
import RESTSplunkMethods as Splunk
import Command

SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM

if __name__ == "__main__":
	Slack.connect(SLACK_BOT_TOKEN)
	botID = Slack.getBotID()
	print("\nSlackSplunkBot connected to Slack")
	
	Splunk.connect()
	print("\nSlackSplunkBot connected to Splunk")
	
	while True:
		command, channel = Command.parseBotCommands(Slack.getSlackEvents(), botID)
		if command:
			Command.handleCommand(command, channel)
		time.sleep(RTM_READ_DELAY)