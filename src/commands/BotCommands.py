import os, sys, time, traceback
import __main__
import SimpleHipChat as HipChat
import Util

def restart(commandParameters, channel):
	HipChat.postNotification("Restarting", channel)
	os.execl(sys.executable, 'python', __main__.__file__, *sys.argv[1:])
	
def shutdown(commandParameters, channel):
	HipChat.postNotification("Shutting Down", channel)
	sys.exit("Shutdown command used")
	
def debug(commandParameters, channel):
	HipChat.postNotification("Debugging {}".format(commandParameters[0]), channel)
	commandString, commandFunction = Util.getCommandFunction(commandParameters[0])
	if(commandString and commandFunction):
		del commandParameters[0]
		HipChat.postNotification("Running Command {} with parameters {}".format(commandString, str(commandParameters)), channel)
		try:
			commandFunction(commandParameters, channel)
			HipChat.postNotification("Command {} completed without error".format(commandString), channel)
		except Exception:
			HipChat.postNotification(traceback.format_exc(), channel)
		return

def list_commands(commandParameters, channel):
	botCommands = Util.getCommandList()
	commandList = ''
	searchString = ''
	if(len(commandParameters)>0):
		searchString = commandParameters[0]
	for commandString, commandFunction in botCommands:
		if(searchString in commandString):
			commandList += commandString.replace('_', ' ') + '\n'
	HipChat.postNotification(commandList, channel)

def help(commandParameters, channel):
	if(len(commandParameters) > 0):
		commandString, commandFunction = Util.getCommandFunction(commandParameters[0])
		if(commandString and commandFunction):
			HipChat.postNotification(commandFunction.__doc__, channel)
		elif(commandParameters[0] == 'Basics'):
			helpString = ("SplunkBot monitors chat rooms and performs commands posted in them.\n "
							"Commands to SplunkBot must start with an exclamation mark.\n "
							"Certain commands use parameters. They are placed after the command name and separated by commas\n "
							"Ex: 'commandName parameter1, parameter2, parameter3'\n "
							"Many commands have multiple ways in which they can be called, be sure to use 'help <commandName>' for specific information on a command.\n "
							"All list commands can be passed a search string as the last parameter. The list command will only return things containing that string.\n ")
		elif(commandParameters[0] == 'Searches'):
			helpString = ("SplunkBot's primary purpose is to allow Splunk searches to be run from within the chat room.\n "
							"SplunkBot can run a search written completely in the chat.\n "
							"Ex: 'run search index=* Error'\n "
							"SplunkBot can run saved searches from the Splunk environment it is connect to.\n "
							"Ex: 'run saved search <savedSearchName>'\n "
							"SplunkBot can list saved searches with the command 'list saved searches'.\n")
		elif(commandParameters[0] == 'Dashboards'):
			helpString = ("SplunkBot can return graphical representations of data from dashboards.\n "
							"Ex: 'get dashboard <appName>, <dashboardName>'\n "
							"This method requires the name of the app the dashboard belongs to and the name of the dashboard.\n "
							"These can be acquired with 'list apps' and 'list dashboards <appName>' respectively.\n")
		elif(commandParameters[0] == 'Alerts'):
			helpString = ("SplunkBot can interact with Splunk alerts as well.\n "
							"Alerts can be listed with 'list alerts'.\n "
							"Alerts can be enabled with 'enable alert <alertName>'.\n "
							"Alerts can be disabled with 'disable alert <alertName>'.\n "
							"Alerts can be enabled for X minutes with 'disable alert <alertName>, <X>'.\n ")
		elif(commandParameters[0] == 'Splunk Enviroment'):
			helpString = ("SplunkBot can currently be connected to ITest or Local.\n "
							"The default environment is Local.\n "
							"'which environment' can be used to find out the environment the bot is currently connected to.\n "
							"'connect to ITest' and 'connect to Local' can be used to change environment.\n ")
	else:
		helpString = ("'list commands' can be used to list all possible commands.\n "
						"'help <commandName>' can be used to receive detailed information on a command.\n "
						"\n "
						"'help <subjectName>' can be used to gain more information on any of the following subjects.\n "
						"Basics \n Searches\n Dashboards\n Alerts\n Splunk Environment\n")
	HipChat.postNotification(helpString, channel)
#Testing Commands
	
def self_command_test(commandParameters, channel):
	HipChat.postNotification("!test", channel)
	
def post_image(commandParameters, channel):
	HipChat.postFile('res\\SplunkBot.png')
	
def post_pdf(commandParameters, channel):
	HipChat.postFile('pdf_files\\alert_logevent_7day.pdf')
	
def parameter_test(commandParameters, channel):
	HipChat.postNotification(str(commandParameters), channel)
	
def raise_error(commandParameters, channel):
	raise Exception("Test Error")
	
def test(commandParameters, channel):
	""" This is a test docstring """
	HipChat.postNotification("Test \n new line", channel)
	
def api_throttle_test(commandParameters, channel):
	for i in range(100):
		HipChat.getEvents()
		HipChat.getEvents()
		HipChat.getEvents()
		HipChat.postNotification(str(i * 4), channel)
	
def api_flood_test(commandParameters, channel):
	for i in range(100):
		HipChat.postNotification(str(i), channel)