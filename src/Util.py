import inspect
import commands.BotCommands as BotCommands
import commands.SplunkCommands as SplunkCommands
from wand.image import Image
from wand.color import Color

def formatResultsAsTable(results):
	tableString = ''
	maxCharcterSizes = []
	
	print(results)
	if(len(results) > 0):
	
		for key, value in results[0].items():
			maxCharcterSizes.append(len(key))
				
		for dict in results:
			for index, (key, value) in enumerate(dict.items()):
				if(maxCharcterSizes[index] < len(value)):
					maxCharcterSizes[index] = len(value)

		#maxCharcterSizes[:] = [i + 1 for i in maxCharcterSizes]
			
		tableString += '┌─'
		
		for index, (characterLength) in enumerate(maxCharcterSizes):
			tableString += '─' * characterLength
			if(index + 1 < len(maxCharcterSizes)):
				tableString += '─┬─'
		
		tableString += '─┐\n'
			
		tableString += '│ '
			
		for index, (key, value) in enumerate(results[0].items()):
			tableString += '{}{}{} │ '.format('{:', maxCharcterSizes[index],'}').format(key)
				
		tableString += '\n├─'
		
		for index, (characterLength) in enumerate(maxCharcterSizes):
			tableString += '─' * characterLength
			if(index + 1 < len(maxCharcterSizes)):
				tableString += '─┼─'
		
		tableString += '─┤\n'
		
		for dict in results:
			tableString += '│ '
		
			for index, (key, value) in enumerate(dict.items()):
				tableString += '{}{}{} │ '.format('{:', maxCharcterSizes[index],'}').format(value)
				
			tableString += '\n'
				
		tableString += '└─'
		
		for index, (characterLength) in enumerate(maxCharcterSizes):
			tableString += '─' * characterLength
			if(index + 1 < len(maxCharcterSizes)):
				tableString += '─┴─'
		
		tableString += '─┘'
	else:
		tableString = "No Results"
		
	return tableString
	
def formatResultsAsHTMLTable(results):
	tableString = '<table style="width:100%" align="left">'
	maxCharcterSizes = []
	
	if(len(results) > 0):
		
		tableString += '<tr>'
		
		for key, value in results[0].items():
			tableString += '<th>{}</th>'.format(key)	
			
		tableString += '</tr>'
		
		for dict in results:
			tableString += '<tr>'
		
			for key, value in dict.items():
				tableString += '<td>{}</td>'.format(value)
				
			tableString += '</tr>'
				
		tableString += '</table>'
	else:
		tableString = "No Results"
		
	return tableString
	
def formatArray(array):
	formattedArray = ""

	for entry in array:
		formattedArray += '{}\n'.format(entry)
		
	return formattedArray
	
def getCommandFunction(command):
	botCommands = getCommandList()
	
	for commandString, commandFunction in botCommands:
		commandString = commandString.replace('_', ' ')
		if(command.startswith(commandString)):
			return commandString, commandFunction
	
	return None, None
	
def getCommandList():
	botCommands = []
	botCommands.extend(inspect.getmembers(BotCommands, inspect.isfunction))
	botCommands.extend(inspect.getmembers(SplunkCommands, inspect.isfunction))
	return botCommands
	
def convertPDFToPNG(pdfName):
	pdfPath = 'pdf_files/{}.pdf'.format(pdfName)
	pngPaths = []
	
	with Image(filename=pdfPath, resolution=200) as source:
		images=source.sequence
		for index, singleImg in enumerate(images):
			pngPath = 'pdf_files/{}{}.png'.format(pdfName, str(index))
			img = Image(singleImg)
			img.background_color = Color('white')
			img.alpha_channel = 'remove'
			# img = removeSplunkBorderFromPNG(img)
			img.save(filename=pngPath)
			pngPaths.append(pngPath)
	return pngPaths

def removeSplunkBorderFromPNG(img):
	img.background_color = Color('snow4')
	img.alpha_channel = 'remove'
	img.trim(fuzz=50)
	img.trim(fuzz=50)
	img.trim()
	return img
	