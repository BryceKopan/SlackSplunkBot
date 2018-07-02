import os, sys, time
import __main__
import SimpleHipChat as HipChat

def restart(commandParameters, channel):
	HipChat.postMessage("Restarting", channel)
	os.execl(sys.executable, 'python', __main__.__file__, *sys.argv[1:])
	
def shutdown(commandParameters, channel):
	HipChat.postMessage("Shutting Down", channel)
	sys.exit("Shutdown command used")
	
#Testing Commands
	
def parameter_test(commandParameters, channel):
	return
	
def raise_error(commandParameters, channel):
	raise Exception("Test Error")
	
def test(commandParameters, channel):
	HipChat.postMessage("Test \n new line", channel)