import os, time, traceback
import SlackAPI as Slack
import RESTSplunkMethods as Splunk
import Command

import Util

SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM

if __name__ == "__main__":
	Slack.connect(SLACK_BOT_TOKEN)
	botID = Slack.getBotID()
	print("\nSlackSplunkBot connected to Slack")
	
	Splunk.connect()
	print("\nSlackSplunkBot connected to Splunk")
	
	results = Splunk.runSearch("index=_audit action= * user=* earliest=-60m latest=now() | stats count by user")
	Util.formatResultsAsTable(results)
	
	while True:
		command, channel = Command.parseBotCommands(Slack.getSlackEvents(), botID)
		if command:
			try:
				Command.handleCommand(command, channel)
			except Exception:
				Slack.postMessage("Error Running Command: {}".format(command), channel)
				print("\nError Running Command: {}\n".format(command))
				traceback.print_exc()
		time.sleep(RTM_READ_DELAY)