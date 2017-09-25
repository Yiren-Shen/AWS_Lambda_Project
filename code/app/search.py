from app import webapp
from flask import render_template, session, redirect, url_for, request, jsonify

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import json
import decimal

from app.main import get_table

def isCorrelated(item, keyword):
	correlation = 0
	if isinstance(item, unicode):
		item = item.encode("utf-8")
	elif isinstance(item, decimal.Decimal):
		item = str(float(item))
	elif isinstance(item, list):
		for i in item:
			correlation += isCorrelated(i, keyword)
	elif isinstance(item, dict):
		for val in item.values():
			correlation += isCorrelated(val, keyword)

	if isinstance(item, str):
		item = item.lower()
		keyword = keyword.lower()
		correlation += item.count(keyword)
	return correlation


def filterByKeywords(items, keywords):
	for item in items[::-1]:
		correlation = 0
		for keyword in keywords:
			correlation += isCorrelated(item, keyword)
		if correlation == 0:
			items.remove(item)
		elif correlation > 0:
			item['correlation'] = correlation
	return items

# def filterByKeywords(items, keywords):
# 	for item in items[::-1]:
# 		correlation = 0
# 		for keyword in keywords:
# 			if keyword.lower() in str(item).lower():
# 				correlation += 1
# 			else:
# 				correlation -= 1
# 		if correlation < 1:
# 			items.remove(item)
# 	return items



def sort(items, sortBy='correlation'):
	if sortBy == 'correlation':
		items.sort(key=lambda k: (k.get('name',0),k.get('brand',0)))
		items.sort(key=lambda k: (k.get('rating',0).get('score',0),k.get('favors',0),k.get('reviews',0)), reverse=True)
		items.sort(key=lambda k: (k.get('correlation',0)), reverse=True)
	elif sortBy == 'rating':
		items.sort(key=lambda k: (k.get('name',0),k.get('brand',0)))
		items.sort(key=lambda k: (k.get('correlation',0),k.get('favors',0),k.get('reviews',0)), reverse=True)
		items.sort(key=lambda k: (k.get('rating',0).get('score',0)), reverse=True)
	elif sortBy == 'reviews':
		items.sort(key=lambda k: (k.get('name',0),k.get('brand',0)))
		items.sort(key=lambda k: (k.get('correlation',0),k.get('rating',0).get('score',0),k.get('favors',0)), reverse=True)
		items.sort(key=lambda k: (k.get('reviews',0)), reverse=True)
	elif sortBy == 'favors':
		items.sort(key=lambda k: (k.get('name',0),k.get('brand',0)))
		items.sort(key=lambda k: (k.get('correlation',0),k.get('rating',0).get('score',0),k.get('reviews',0)), reverse=True)
		items.sort(key=lambda k: (k.get('favors',0)), reverse=True)
	elif sortBy == 'brand':
		items.sort(key=lambda k: (k.get('name',0)))
		items.sort(key=lambda k: (k.get('correlation',0),k.get('rating',0).get('score',0),k.get('favors',0),k.get('reviews',0)), reverse=True)
		items.sort(key=lambda k: (k.get('brand',0)))
	elif sortBy == 'name':
		items.sort(key=lambda k: (k.get('brand',0)))
		items.sort(key=lambda k: (k.get('correlation',0),k.get('rating',0).get('score',0),k.get('favors',0),k.get('reviews',0)), reverse=True)
		items.sort(key=lambda k: (k.get('name',0)))

	return items


@webapp.route('/search/<keywords>')
def search(keywords):
	keywords = keywords.strip().encode("utf-8")
	print keywords
	print len(keywords)
	print type(keywords)

	if type(keywords) != str:
		keywords = str(keywords)
	keywords = keywords.replace(","," ")
	keywords = keywords.replace("/"," ")
	keywords = keywords.replace("\\"," ")
	keywords = keywords.replace(";"," ")
	keywords = keywords.replace("%"," ")
	keywords = keywords.replace("|"," ")
	keywords = keywords.split()

	table = get_table('Fragrances')
	try:
		response = table.scan()
	except ClientError as e:
		raise e
	else:
		items = response['Items']
		for item in items:
			del item['properties']['description']
		items = filterByKeywords(items, keywords)
		items = sort(items)
		num = len(items)

	if 'account' not in session:
		return render_template('search.html',
								items=items,
								num=num,
								keywords=" ".join(keywords),
								)
	else:
		table = get_table('Users')
		account = session['account']
		try:
			response = table.get_item(
				Key = {
				'account': account
				})
		except ClientError as e:
			raise e
		else:
			user = response['Item']
			return render_template('search.html',
									name=user['name'],
									items=items,
									num=num,
									keywords=" ".join(keywords),
									)

@webapp.route('/search/resort/<keywords>', methods=['post'])
def reSort(keywords):

	sortBy = request.form.get('sortBy',"correlation")

	if type(keywords) != str:
		keywords = str(keywords)
	keywords = keywords.replace(","," ")
	keywords = keywords.replace("/"," ")
	keywords = keywords.replace("\\"," ")
	keywords = keywords.replace(";"," ")
	keywords = keywords.replace("%"," ")
	keywords = keywords.replace("|"," ")
	keywords = keywords.split()

	table = get_table('Fragrances')
	try:
		response = table.scan()
	except ClientError as e:
		raise e
	else:
		items = response['Items']
		for item in items:
			del item['properties']['description']
		items = sort(items, sortBy)
		items = filterByKeywords(items, keywords)
		num = len(items)

		if 'account' not in session:
			return render_template('search.html',
									items=items,
									num=num,
									keywords=" ".join(keywords),
									sortBy=sortBy
									)
		else:
			account = session['account']
			table = get_table('Users')
			try:
				response = table.get_item(
					Key = {
					'account': account
					})
			except ClientError as e:
				raise e
			else:
				user = response['Item']
				return render_template('search.html',
										name=user['name'],
										items=items,
										num=num,
										keywords=" ".join(keywords),
										sortBy=sortBy
									)

# @webapp.route('/search/test',methods=['post'])
# def ajax_test():
# 	brand = request.form.get('brand')
# 	print brand
# 	return jsonify(ret={
# 					'score': 1
# 				})



@webapp.route('/search/filter/<keywords>&<key>&<value>')
def filter(keywords, key, value):
	key = key.strip().encode("utf-8") 
	keywords = keywords.strip().encode("utf-8") 
	value = value.strip().encode("utf-8") 

	print keywords, key, value
	print type(keywords), type(key), type(value)
	print len(keywords), len(key), len(value)

	if type(keywords) != str:
		keywords = str(keywords)
	keywords = keywords.replace(","," ")
	keywords = keywords.replace("/"," ")
	keywords = keywords.replace("\\"," ")
	keywords = keywords.replace(";"," ")
	keywords = keywords.replace("%"," ")
	keywords = keywords.replace("|"," ")
	keywords = keywords.split()
	key = key.split()

	table = get_table('Fragrances')
	try:
		response = table.scan()
	except ClientError as e:
		raise e
	else:
		items = response['Items']
		for item in items:
			del item['properties']['description']

		if len(key) == 1:
			for item in items[::-1]:
				if value not in item[key[0]]:
					items.remove(item)
		elif len(key) == 2:
			for item in items[::-1]:
				if value not in item[key[0]][key[1]]:
					items.remove(item)
		elif len(key) == 3:
			for item in items[::-1]:
				if value not in item[key[0]][key[1]][key[2]]:
					items.remove(item)
		items = filterByKeywords(items, keywords)
		items = sort(items)
		num = len(items)

	if 'account' not in session:
		return render_template('search.html',
								items=items,
								num=num,
								keywords=" ".join(keywords),
								)
	else:
		table = get_table('Users')
		account = session['account']
		try:
			response = table.get_item(
				Key = {
				'account': account
				})
		except ClientError as e:
			raise e
		else:
			user = response['Item']
			return render_template('search.html',
									name=user['name'],
									items=items,
									num=num,
									keywords=" ".join(keywords),
									)







