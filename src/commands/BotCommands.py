import os, sys, time
import __main__
import SimpleHipChat as HipChat

def restart(commandParameters, channel):
	HipChat.postNotification("Restarting", channel)
	os.execl(sys.executable, 'python', __main__.__file__, *sys.argv[1:])
	
def shutdown(commandParameters, channel):
	HipChat.postNotification("Shutting Down", channel)
	sys.exit("Shutdown command used")
	
#Testing Commands
	
def post_image(commandParameters, channel):
	HipChat.postFile('res\\SplunkBot.png')
	return
	
def post_pdf(commandParameters, channel):
	HipChat.postFile('pdf_files\\alert_logevent_7day.pdf')
	return
	
def parameter_test(commandParameters, channel):
	return
	
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