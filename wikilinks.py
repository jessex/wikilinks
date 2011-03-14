import urllib2, re
from sys import argv, exit
from time import sleep

#namespaces of Wikipedia pages which we wish to ignore
namespaces = ["Wikipedia:", "Category:", "Talk:", "File:", "Portal:", "User:", 
"WT:", "MediaWiki:", "Template:", "Image:", "WP:", "Wikipedia_talk:", "Help:",
"Book:", "Media:", "Project:", "Project_talk:", "Image_talk:", "User_talk:",
"Thread:", "Summary:", "Thread_talk:", "Summary_talk:", "Book_talk:", 
"MediaWiki_talk:", "Template_talk:", "Help_talk:", "Portal_talk:", "Special:",
"Category_talk:"]

user_agent = "wikilinks/1.0" #Wikipedia denies urllib2's default user agent

re_link = re.compile("<a\s*href=['\"](.*?)['\"].*?>") #pulls links from HTML
re_wiki = re.compile("/wiki/.+") #cares only for links to Wikipedia articles
re_next = re.compile("/w/index.php\?title=Special:WhatLinksHere/.*namespace=0.*limit=500.*from=.*back=.*") #finds links to another page of incoming links
re_input = re.compile("http://en.wikipedia.org/wiki/.+")

to_file = False

#proper arguments usage: 
#wikilinks.py , http://en.wikipedia.org/wiki/whatever , OPTIONAL: -f filename
def process_args(args):
	global to_file, out_file
	
	#validate the starting article input
	input = args[1]
	if re_input.match(input) == None:
		print "Start link must be from English Wikipedia's default namespace"
		exit("Must be of the form: http://en.wikipedia.org/wiki/...")
	else:
		valid = True
		for ns in namespaces:
			if ns in input:
				valid = False
				break
		if not valid:
			print "Start link must be from English Wikipedia's main namespace"
			exit("For more information on namespaces, " \
			"visit: http://en.wikipedia.org/wiki/Wikipedia:Namespace")
	#check if writing output to a file
	if len(args) > 2:
		if args[2] == "-f":
			if len(args) > 3:
				out_file = args[3]
				to_file = True
			else:
				exit("Must include file name after the file flag '-f'")
		else:
			exit("Usage: Wikipedia_article [-f output_file]")
	return input
	

#pass in a url and receive the page source HTML
def page_html(url, verbose=True):
	request = urllib2.Request(url) #craft our request for the input page
	request.add_header("User-Agent", user_agent)
	if verbose:
		print "Requesting page...", url

	try:
		response = urllib2.urlopen(request) #send GET request to server
	except IOError, e: #HTTPError extends URLError which extends IOError
		if hasattr(e, "reason"): #URLError
			print "Could not reach server: ", e.reason
		elif hasattr(e, "code"): #HTTPError 
			print "Could not fulfill request: ", e.code
		exit(0)
	else: #received a good, valid response
		return response.read() #page source
		
#get a list of the links to all outgoing articles from the passed HTML page
def outgoing_articles(html, verbose=True):
	if verbose:
		print "Searching for outgoing Wikipedia articles..."
		
	links = re_link.findall(html) #all outgoing links from input page
	outlinks = [] #all outgoing links within Wikipedia
	for link in links:
		if link.lower() == article.lower(): #skip circular links (to self)
			continue
		elif link == "/wiki/Main_Page": #on every page, not article
			continue
		if re_wiki.match(link) != None:
			main_ns = True
			for ns in namespaces: #check for non-main namespaces
				if ns in link:
					main_ns = False
					break
			if main_ns:
				if link not in outlinks:
					outlinks.append(link)
	return outlinks

#get a list of all articles which link to the article with the given title
def incoming_articles(title, verbose=True):
	if verbose:
		print "Searching for incoming Wikipedia articles..."
		
	link = "http://en.wikipedia.org/w/index.php?title=Special:WhatLinksHere/"
	link += title + "&limit=500"
	whatlinkshere = page_html(link)
	
	inlinks = []
	more = True
	while more: #scroll through all incoming links
		inlinks += outgoing_articles(whatlinkshere, verbose=False)
		next_page = re_next.findall(whatlinkshere)
		if not next_page:
			more = False
		else:
			newlink = "http://en.wikipedia.org" + next_page[0]
			sleep(1) #wait one second before next request (politeness)
			whatlinkshere = page_html(newlink)
	return inlinks
	

if __name__ == "__main__":
	if len(argv) < 2:
		exit("Please include a starting Wikipedia article link")

	input = process_args(argv) #form: http://en.wikipedia.org/wiki/whatever
	article = input.replace("http://en.wikipedia.org", "") #form: /wiki/whatever
	title = article.replace("/wiki/", "") #form: whatever
	
	#valid starting article at this point, beginning crawl of page
	print "Starting article:", input

	html = page_html(input)
	outlinks = outgoing_articles(html)
	sleep(1) #wait one second before next request (politeness)
	inlinks = incoming_articles(title)

	#have list of all articles pointed to by start article at this point
	if not to_file: #printing output to screen
		print "\n%d outgoing links from starting article" % len(outlinks)
		if outlinks:
			print "Outgoing articles:"
			for link in outlinks:
				print "http://en.wikipedia.org%s" % link
		print "\n%d incoming links to starting article" % len(inlinks)
		if inlinks:
			print "Incoming articles:"
			for link in inlinks:
				print "http://en.wikipedia.org%s" % link
				
	else: #writing output to file
		f = open(out_file, "w")
		output = "Start: %s\nOutgoing(%d):\n" % (input, len(outlinks))
		for link in outlinks:
			output += "http://en.wikipedia.org%s\n" % link
		output += "Incoming(%d):\n" % len(inlinks)
		for link in inlinks:
			output += "http://en.wikipedia.org%s\n" % link
		f.write(output)
		f.close()
		print "Output written to file: '%s'" % out_file

		
	

