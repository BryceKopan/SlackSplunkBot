import os, time, traceback
import RESTSplunkMethods as Splunk
import Command
import SimpleHipChat as HipChat

import Util

HIPCHAT_BOT_TOKEN = os.environ.get('HIPCHAT_BOT_TOKEN')
HIPCHAT_HOST = 'hipchat.ercot.com'
SPLUNK_BASE_URL = "https://localhost:8089"
USERNAME = os.environ.get('SPLUNK_LOCAL_USERNAME')
PASSWORD = os.environ.get('SPLUNK_LOCAL_PASSWORD')

#constants
RTM_READ_DELAY = 5 # second delay between reading from RTM

if __name__ == "__main__":
	HipChat.connect(HIPCHAT_BOT_TOKEN, HIPCHAT_HOST)
	trigger = '!'
	print("\nSplunkBot connected to HipChat")
	
	Splunk.connect(SPLUNK_BASE_URL, USERNAME, PASSWORD)
	print("\nSplunkBot connected to Splunk")
	
	while True:
		try:
			command, channel = Command.parseBotCommands(HipChat.getEvents(), trigger)
			
			if command:
				try:
					print(command)
					Command.handleCommand(command, channel)
				except Exception:
					HipChat.postMessage("Error Running Command: {}".format(command), channel)
					print("\nError Running Command: {}\n".format(command))
					traceback.print_exc()
		except Exception:
			print("\nError parsing chat for commands\n")
			traceback.print_exc()
			
		time.sleep(RTM_READ_DELAY)