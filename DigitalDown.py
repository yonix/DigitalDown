#!/usr/bin/env python

import urllib2, argparse
from re import findall
from sys import argv
from urllib import urlretrieve
from lxml.html import fromstring
from sys import stdout
import math

# 
# Author: MrBot,Shrek0
# Version: 0.3
#
# The first version: http://www.hacking.org.il/showthread.php?t=4960
#
# Description: 
#	Download DigitalWhisper issues.
#

__VERSION__ = 0.3


# Taken from "https://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python" with some changes
def size(size):
   size_name = ('B',"KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   if(size < 1024):
	   return (str(size), size_name[0])
   i = int(math.floor(math.log(size,1024)))
   p = math.pow(1024,i)
   s = round(size/p,2)
   if (s > 0):
       return (s,size_name[i])
   else:
       return '0B'

def padding(var, to_padding, padding_char = ' '):
	return str(var) + ((to_padding - len(str(var))) * padding_char)

class DigitalWhisper(object):
	
	def __init__(self,options):
		self._options = options
		
		self.files = []
		
		self._html_cache_data = ''
		self._html_cache_id = 0
		
		if self._options.Format == 'many':
			self._lxml_cache_data = ''
			self._lxml_cache_id = 0
		
		self._last_id_cache_data = -1
		
		self._titles_cache_data = []
		self._titles_cache_id = []
		
		self.content_list = ['idd', 'id', 'title', 'filename']

	## Global functions.
	
	# Public function, add id for download.
	def add_to_download(self, id):
		self.files += self.get_files_list(id)
		
	# Public function, download all files that added before.
	def download(self):
			counter = 1
			files_len = len(self.files)
                
			for f in self.files:
				path = self._options.path + '/' + f['save_name']
				print '(%d/%d) Downloading %s to %s:' % (counter, files_len, f['link'], path)
				self.save(path, f['link'])
				
				counter+=1
				
	# Private-Public function, return the last id. 
	def last(self):
		if self._last_id_cache_data == -1:
			source = self.request("http://www.digitalwhisper.co.il/")
			self._last_id_cache_data = int(findall('<a href="http://www.digitalwhisper.co.il/issue([0-9]+)"><b>', source)[0])
			
		return self._last_id_cache_data
	
	# Private function, return list of files to download.
	def get_files_list(self, id):
		files  = []
		links = self.get_all_links(id)
		idd = 0
		
		for link in links:
			files.append({'link':self.fix_link(link), 'save_name':self.get_format_save_name(link, id, idd)})
			
			idd += 1
		
		return files
	
	# Private function, return the required contents for the file save format.
	# Used in get_format_save_name function,
	def get_required_contents(self):
		contents = []
		
		for c in self.content_list:
			if self._options.SaveFormat.find(c) > -1:
				contents.append(c)
				
		return contents

	## Link functions.
	
	# Private function, return fixed link by link.
	def fix_link(self, link):
		return link.replace('../../', '')
	
	def get_all_links(self, id):
		links = []
		
		if self._options.Format == 'many':
			if self._lxml_cache_id != id:
				self.download_html(id)
				
				self._lxml_cache_data = fromstring(self._html_cache_data)
				self._lxml_cache_id = id
				
			self._lxml_cache_data.make_links_absolute("http://www.digitalwhisper.co.il")
			
			links = self._lxml_cache_data.xpath("//td/a/@href")
			
			if len(links) < 2:
				links +=  self._lxml_cache_data.xpath("//td/font/a/@href")
			if len(links) < 2: # Damn, it's still the same.
				links +=  self._lxml_cache_data.xpath("//span/a/@href")
				
		elif self._options.Format == 'one':
			links.append('http://www.digitalwhisper.co.il/files/Zines/0x%02X/DigitalWhisper%d.pdf' % (id, id))
		
		return links
	
	## Title functions.
	
	# Private function, return title by id and idd.
	def get_title(self, id, idd):
		if self._titles_cache_id != id:
			self._titles_cache_data = self.get_all_titles(id)
			self.titles_cache_id = id
		
		if len(self._titles_cache_data) <= idd: # if the titles length
			print "Warning: links and titles length is not equal! may be a problem in the title. id:%d" % (id)
			return "Untitled %d|%d" % (id, idd)
			
		return self._titles_cache_data[idd]
	
	# Private function, return all titles of id.
	def get_all_titles(self, id):
		titles = []
		
		if self._options.Format == 'many':
			# No need to check the cache again, get_all_links method was called before and did these things. 
			
			titles = self._lxml_cache_data.xpath("//td/a/text()")
			
			if len(titles) < 2:
					titles += self._lxml_cache_data.xpath("//td/font/a/text()")
					titles += self._lxml_cache_data.xpath("//td/a/font/text()")
			if len(titles) < 2:
				titles += self._lxml_cache_data.xpath("//span/a/text()")
		elif self._options.Format == 'one':
			titles.append('Digital Whisper Full Issue %d' % id)
		
		return titles
	
	## File name functions.
	
	# Private function, return file without bad characters.
	def clear_bad_chars(self, string):
		return string.replace('/', 'or').replace('\\', 'or')

	# Private function, return file name by link.
	def get_file_name(self, link):
		return findall('files/Zines/0x[A-F0-9]+/([-A-Za-z0-9.\/_]+).pdf', link)[0]

	# Private function, return the save name.
	def get_format_save_name(self,link, id, idd):
		save_name = self._options.SaveFormat
		replaces = []
		words = []
		
		required_contents = self.get_required_contents()
		
		for c in required_contents:
			words.append('#' + c)
			if c == 'idd':
				replaces.append(str(idd))
			elif c == 'id':
				replaces.append(str(id))
			elif c == 'title':
				replaces.append(self.get_title(id, idd))
			elif c == 'filename':
				replaces.append(self.get_file_name(link))
						
		for word,replace  in zip(words, replaces):
			save_name = save_name.replace(word, replace)
		
		return self.clear_bad_chars(save_name)
	
	## Download pdf functions.
	
	# Private function, show reprot about the download. Used in 'save' function.
	def report_hook(self,count,block_size,total_size):
		percentage = (count * block_size)*100/total_size
		stdout.write('\r%s %% : ' % padding(str(percentage), 3))
		
		stdout.write(padding(percentage * '#', 101))
		
		count = size(count * block_size)
		count = '%s %s' % (padding(count[0], 6), padding(count[1], 2))
		
		total_size = size(total_size)
		total_size = '%s %s' % (total_size[0], total_size[1])
		
		stdout.write('| %s of %s'% (count, total_size))
		
		stdout.flush()
	
	def save(self, path, url):
			urlretrieve(url, path, self.report_hook)
			print
                        
	## Download html functions.
	
	# Private function, get response by url.
	def request(self, url):
		c = urllib2.urlopen(url)
		data = c.read()
		c.close()
		return data
	
	# Private function, download html of id if it not in the cache.
	def download_html(self, id):
		if self._html_cache_id != id:
			self._html_cache_id = id
			self._html_cache_data = self.request("http://www.digitalwhisper.co.il/issue%d" %  id)

def main(options):	
	dw = DigitalWhisper(options)
	
	if options.Download == 'last':
		dw.add_to_download(dw.last())
	elif options.Download.find('-') > 0: #range
		range_ = options.Download.split('-')
		
		if range_[1] == 'last': # range: something to last (9-last).
			range_[1] = dw.last()
			
		for i in range(int(range_[0]), int(range_[1])+1):
			dw.add_to_download(i)
			
	elif options.Download == 'all':
		for i in range(1, dw.last()):
			dw.add_to_download(i)
	else:
		dw.add_to_download(int(options.Download))
		
	# Now, download the files:
	dw.download()
	
	return
 
if __name__ == '__main__':
	
	parser = argparse.ArgumentParser(description='Digital Whisper Downloader')
	parser.add_argument("-d","--download", dest="Download", help="Digital Whisper ID for download, IDs range (Example: 10-20, 7-last), all or last [default: last]", metavar="ID", default='last') 
	parser.add_argument("-f", "--format", dest="Format", help="Digital Whisper format: one PDF [default], or many PDFs", metavar='FORMAT',default="one")
	parser.add_argument("-s", "--save", dest="SaveFormat", help="Save format [default: #filename.pdf]. Example: #id_#filename_#title_TEXT -> 4_DW4-1-HTTP-Fingerprints_HTTP Fingerprints_TEXT)", metavar='FORMAT',default="#filename.pdf")
	parser.add_argument("-v", "--version", action='version', version=str(__VERSION__))
	parser.add_argument(dest="path", help="Save files path",default="./", nargs='?')

	args = parser.parse_args()
	
	main(args)
