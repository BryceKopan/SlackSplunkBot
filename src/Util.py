
def formatResultsAsTable(results):
	tableString = ""
	maxCharcterSizes = []
	
	if(len(results) > 0):
	
		for key, value in results[0].items():
			maxCharcterSizes.append(len(key))
				
		for dict in results:
			for index, (key, value) in enumerate(dict.items()):
				if(maxCharcterSizes[index] < len(value)):
					maxCharcterSizes[index] = len(value)

		#maxCharcterSizes[:] = [i + 1 for i in maxCharcterSizes]
			
		tableString += "┌─"
		
		for index, (characterLength) in enumerate(maxCharcterSizes):
			tableString += "─" * characterLength
			if(index + 1 < len(maxCharcterSizes)):
				tableString += "─┬─"
		
		tableString += "─┐\n"
			
		tableString += "│ "
			
		for index, (key, value) in enumerate(results[0].items()):
			tableString += "{}{}{} │ ".format("{:", maxCharcterSizes[index],"}").format(key)
				
		tableString += "\n├─"
		
		for index, (characterLength) in enumerate(maxCharcterSizes):
			tableString += "─" * characterLength
			if(index + 1 < len(maxCharcterSizes)):
				tableString += "─┼─"
		
		tableString += "─┤\n"
		
		for dict in results:
			tableString += "│ "
		
			for index, (key, value) in enumerate(dict.items()):
				tableString += "{}{}{} │ ".format("{:", maxCharcterSizes[index],"}").format(value)
				
			tableString += "\n"
				
		tableString += "└─"
		
		for index, (characterLength) in enumerate(maxCharcterSizes):
			tableString += "─" * characterLength
			if(index + 1 < len(maxCharcterSizes)):
				tableString += "─┴─"
		
		tableString += "─┘"
	else:
		tableString = "No Results"
		
	return tableString