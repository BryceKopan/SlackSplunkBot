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
	botCommands = Util.getCommandList()
	for commandString, commandFunction in botCommands:
		commandString = commandString.replace('_', ' ')
		if(commandParameters[0].startswith(commandString)):
			del commandParameters[0]
			HipChat.postNotification("Running Command {} with parameters {}".format(commandString, str(commandParameters)), channel)
			try:
				commandFunction(commandParameters, channel)
			except Exception:
				HipChat.postNotification(traceback.format_exc(), channel)
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