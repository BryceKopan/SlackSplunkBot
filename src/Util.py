from wand.image import Image
from wand.color import Color

def formatResultsAsTable(results):
	tableString = ''
	maxCharcterSizes = []
	
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
	
def convertPDFToPNG(pdfName):
	pdfPath = 'pdf_files/{}.pdf'.format(pdfName)
	pngPaths = []
	
	with Image(filename=pdfPath, resolution=200) as source:
		images=source.sequence
		pages=len(images)
		for i in range(pages):
			Image(images[i]).background_color = Color("white")
			Image(images[i]).alpha_channel = 'remove'
			pngPath = 'pdf_files/{}{}.png'.format(pdfName, str(i))
			Image(images[i]).save(filename=pngPath)
			pngPaths.append(pngPath)
	return pngPaths
