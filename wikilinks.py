import urllib2, re
from sys import argv, exit

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
    

if __name__ == "__main__":
    if len(argv) < 2:
        exit("Please include a starting Wikipedia article link")

    input = process_args(argv)

    #valid starting article at this point, beginning crawl of page
    print "Starting article:", input
    article = input.replace("http://en.wikipedia.org", "") #form: /wiki/whatever

    request = urllib2.Request(input) #craft our request for the input page
    request.add_header("User-Agent", user_agent)
    print "Requesting page..."

    try:
        response = urllib2.urlopen(request) #send GET request to server
    except IOError, e: #HTTPError extends URLError which extends IOError
        if hasattr(e, "reason"): #URLError
            print "Could not reach server: ", e.reason
        elif hasattr(e, "code"): #HTTPError 
            print "Could not fulfill request: ", e.code
        exit(0)
    else: #received a good, valid response
        html = response.read() #page source
        print "Finding hyperlinks..."
        links = re_link.findall(html) #all outgoing links from input page
        print "Filtering for regular Wikipedia articles..."
        wikilinks = [] #all outgoing links within Wikipedia
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
		            if link not in wikilinks:
			            wikilinks.append(link)
	
        #have list of all articles pointed to by start article at this point
        if not to_file: #printing output to screen
            print "\n%d outgoing links from starting article" % len(wikilinks)
            if len(wikilinks) > 0:
                print "Outgoing articles:"
                for link in wikilinks:
	                print "http://en.wikipedia.org%s" % link
        else: #writing output to file
            f = open(out_file, "w")
            output = "Start: %s\nOutgoing(%d):\n" % (input, len(wikilinks))
            for link in wikilinks:
                output += "http://en.wikipedia.org%s\n" % link
            f.write(output)
            f.close()
            print "Output written to file: '%s'" % out_file

        
	

