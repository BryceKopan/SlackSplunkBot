import os, time, traceback
import RESTSplunkMethods as Splunk
import Command
import SimpleHipChat as HipChat

import Util

#if you want to switch back to Slack look before GitHub commit 2384add
HIPCHAT_BOT_TOKEN = os.environ.get('HIPCHAT_BOT_TOKEN')
HIPCHAT_HOST = 'hipchat.ercot.com'

#to Change default Splunk host use commented lines 
#in SplunkCommands change to variable environment as well
# SPLUNK_BASE_URL = "https://localhost:8089"
# USERNAME = os.environ.get('SPLUNK_LOCAL_USERNAME')
# PASSWORD = os.environ.get('SPLUNK_LOCAL_PASSWORD')
SPLUNK_BASE_URL = "https://splunk-itest.ercot.com:8089"
USERNAME = os.environ.get('SPLUNK_USERNAME')
PASSWORD = os.environ.get('SPLUNK_PASSWORD')

#the room of hipchat that is watched is a variable set in SimpleHipChat

#constants
RTM_READ_DELAY = 5 #second delay between reading from RTM

if __name__ == "__main__":
	HipChat.connect(HIPCHAT_BOT_TOKEN, HIPCHAT_HOST)
	#Trigger is the character that triggers command parsing
	trigger = '!'
	print("\nSplunkBot connected to HipChat")
	
	Splunk.connect(SPLUNK_BASE_URL, USERNAME, PASSWORD)
	
	while True:
		try:
			#return messages from chat that start with the trigger
			command, channel = Command.parseBotCommands(HipChat.getEvents(), trigger)
			
			if command:
				try:
					Splunk.checkConnection()
					print(command)
					Command.handleCommand(command, channel)
				except Exception:
					HipChat.postNotification("Error Running Command: {}".format(command), channel)
					print("\nError Running Command: {}\n".format(command))
					traceback.print_exc()
		except Exception:
			print("\nError parsing chat for commands\n")
			traceback.print_exc()
			
		time.sleep(RTM_READ_DELAY)