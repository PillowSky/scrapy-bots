# -*- coding: utf-8 -*-
from scrapy.http import Request
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from pyquery import PyQuery as pyq
from pymongo import MongoClient

class MainSpider(CrawlSpider):
	name = "bbs"
	allowed_domains = ['0575bbs.com']
	start_urls = [
		'http://www.0575bbs.com/',
		'http://bbs.0575bbs.com/',
		'http://food.0575bbs.com/',
		'http://travel.0575bbs.com/',
		'http://marry.0575bbs.com/',
		'http://baby.0575bbs.com/',
		'http://prepaid.0575bbs.com/',
	]

	'''
	Forbid directly fetch thread pages, or follow field pages
	Because haven't check if they are recent post, and by always, not.
	Manually check and schedule later.
	'''
	rules = (
		Rule(LinkExtractor(allow=('thread-htm-fid', 'thread\.php\?fid')), callback='parseField'),
	)

	def __init__(self):
		super(MainSpider, self).__init__()
		self.db = MongoClient().sybbs
		self.collection = self.db.thread

	def parseField(self, response):

		'''
		Check if need to fetch next field page
		Exceptions:
		* Login required pages.
		'''
		try:
			lastThread = response.css('tbody#threadlist > tr:last-child')
			if '-' not in lastThread.css('td.author > p > a::text').extract()[0]:
				nextPageUrl = self.start_urls[0] + response.css('div.pages > b + a::attr(href)').extract()[0]
				yield Request(nextPageUrl, callback=self.parseField)
		except Exception, e:
			self.log('Exception occured: %s, %s' % (response.url, e))

		'''
		Filter and fetch thread page
		Based whether on '-' in time to test if it is a recent thread
		For nested tags, use pyquery
		Exceptions:
		* stick top thread don't have field
		* global stick top even don't have timestamp
		'''

		for thread in response.css('tr.tr3'):
			try:
				if '-' in thread.css('td.author > p > a::text').extract()[0]:
					continue
			except Exception, e:
				# This exception is caused by global stick top didn't have time stamp
				# So it will occured in every field, have to comment out
				# self.log('Exception occured: %s, %s' % (response.url, e))
				continue

			info ={}
			try:
				info['url'] = self.start_urls[0] + thread.css('a.subject_t::attr(href)').extract()[0]
				info['timestamp'] = thread.css('td.author > p > a::attr(title)').extract()[0]
				info['title'] = pyq(thread.css('a.subject_t').extract()[0]).text()
				info['field'] = thread.css('a.view::text').extract()[0].strip('[]')
			except Exception, e:
				# This exception is caused by stick top thread didn't have field
				# It also occured very frequently, have to comment out
				# self.log('Exception occured: %s, %s' % (response.url, e))
				pass

			self.collection.update({"url": info['url']}, {"$set": info}, True)

			'''
			the scheduler of yield here is different from that in tornado or twisted,
			it will call `next()` immediately, rather than the IO has completed
			so just use yield, it is still in parallel 
			'''
			yield Request(info['url'], callback=self.parseThread)


	def parseThread(self, response):
		url = response.url.replace('http://bbs', 'http://www')
		reply = []
		for floor in response.css('div.tpc_content').extract():
			reply.append(pyq(floor).text())

		self.collection.update({"url": response.url}, {'$set': {"reply": reply}}, True)
