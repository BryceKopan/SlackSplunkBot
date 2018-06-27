import os, sys, time
import SlackAPI as Slack
import __main__

def restart(commandParameters, channel):
	Slack.postMessage("Restarting", channel)
	os.execl(sys.executable, 'python', __main__.__file__, *sys.argv[1:])
	
def shutdown(commandParameters, channel):
	Slack.postMessage("Shutting Down", channel)
	sys.exit("Shutdown command used")
	
#Testing Commands
	
def parameter_test(commandParameters, channel):
	return
	
def raise_error(commandParameters, channel):
	raise Exception("Test Error")
	
def test(commandParameters, channel):
	Slack.postMessage("Test \n new line", channel)