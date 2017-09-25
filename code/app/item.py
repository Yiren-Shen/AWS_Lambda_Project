from app import webapp
from flask import render_template, session, redirect, url_for, request, jsonify

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import json
import decimal
import datetime

from app.main import get_table, get_all_fragrances
from search import sort


class DecimalEncoder(json.JSONEncoder):
	def default(self, o):
		if isinstance(o, decimal.Decimal):
			if o % 1 > 0:
				return float(o)
			else:
				return int(o)
			return super(DecimalEncoder, self).default(o)


@webapp.route('/list')
def list():
	items = get_all_fragrances()
	items = sort(items,'name')
	if 'account' in session:
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
			return render_template('list.html',
									name=user['name'],
									items=items,
									viewAll=True
									)
	else:
		return render_template('list.html',
								items=items,
								viewAll=True
								)

@webapp.route('/list/sort',methods=['post'])
def list_sort():
	sortBy = request.form.get('sortBy',"name")

	items = get_all_fragrances()
	items = sort(items, sortBy)
	if 'account' not in session:
		return render_template('list.html',
								items=items,
								sortBy=sortBy,
								viewAll=True
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
			return render_template('list.html',
									name=user['name'],
									items=items,
									sortBy=sortBy,
									viewAll=True
									)

@webapp.route('/items/info/<brand>&<name>')
def info(brand, name):
	
	table = get_table('Fragrances')
	key = {
		'brand': brand,
		'name': name
	}
	try:
		response = table.get_item(
			Key=key
			)
	except ClientError as e:
		raise e
	else:
		item = response['Item']

		# if 'reviews' not in item:
		# 	reviews = 1
		# else:
		# 	reviews = item['reviews'] + 1

		# response = table.update_item(
		# 	Key = key,
		# 	UpdateExpression="set reviews = :r",
		# 	ExpressionAttributeValues={
		# 	':r': reviews
		# 	},
		# 	ReturnValues="UPDATED_NEW"
		# 	)

		if 'account' not in session:
			return render_template('info.html',
									item=item,
									)
		else:
			account = session['account']
			table = get_table('Users')

			try:
				response = table.get_item(
					Key={
					'account': account
					})
			except ClientError as e:
				raise e
			else:
				user = response['Item']
				if key in user['favor']:
					hasFavored = True
				else:
					hasFavored = False

				hasRated = False
				u_score = None
				if 'rated' in user:
					for ratedItem in user['rated']:
						if ratedItem['brand'] == key['brand'] and ratedItem['name'] == key['name']:
							hasRated = True
							u_score = ratedItem['u_score']
							break

				return render_template('info.html',
										item=item,
										name=user['name'],
										u_score=u_score,
										hasFavored=hasFavored,
										hasRated=hasRated)


@webapp.route('/items/rate', methods=['get', 'post'])
def rate():
	score = request.form.get('score')
	brand = request.form.get('brand')
	name = request.form.get('name')
	score = decimal.Decimal(score)
	u_score = score

	brand = brand.replace('&amp;','&')
	name = name.replace('&amp;','&')

	table = get_table('Fragrances')

	try:
		response = table.get_item(
			Key={
				'brand': brand,
				'name': name
			})
	except ClientError as e:
		raise e
	else:
		item = response['Item']

		if 'account' not in session:
			return render_template('info.html',
									item=item,
									notLogin=True)

		if item['rating'] == None:
			num = decimal.Decimal(1)
			rating = {
				'score': score,
				'num': num
			}
		else:
			num = item['rating']['num'] + 1
			score = (item['rating']['score']*(num-1) + score) / num
			print score
			score = decimal.Decimal(score).quantize(decimal.Decimal('0.0'))
			print score
			rating = {
				'score': score,
				'num': num
			}

		response = table.update_item(
			Key = {
				'brand': brand,
				'name': name
			},
			UpdateExpression="set rating = :r",
			ExpressionAttributeValues={
			':r': rating
			},
			ReturnValues="UPDATED_NEW"
		)

		account = session['account']
		table = get_table('Users')

		try:
			response = table.get_item(
				Key={
					'account': account
				})
		except Exception as e:
			raise e
		else:
			user = response['Item']

			if 'rated' not in user:
				rated = []
				rated.append({
						'brand': brand,
						'name': name,
						'u_score': u_score
					})
			else:
				rated = user['rated']
				rated.append({
						'brand': brand,
						'name': name,
						'u_score': u_score
					})
			response = table.update_item(
				Key = {
					'account': account
				},
				UpdateExpression="set rated = :r",
				ExpressionAttributeValues={
				':r': rated
				},
				ReturnValues="UPDATED_NEW"
			)

			return jsonify(ret={
					'score': float(score),
					'num': int(num),
					'u_score': int(u_score)
				})


@webapp.route('/items/info/addfavor/<brand>&<name>')
def addfavor(brand, name):

	if 'account' not in session:
		table = get_table('Fragrances')
		key = {
		'brand': brand,
		'name': name
		}

		try:
			response = table.get_item(
				Key = key)
		except ClientError as e:
			raise e
		else:
			item = response['Item']
		return render_template('info.html',
								item=item,
								notLogin=True)
	else:
		table = get_table('Fragrances')
		key = {
		'brand': brand,
		'name': name
		}

		try:
			response = table.get_item(
				Key = key)
		except ClientError as e:
			raise e
		else:
			item = response['Item']

		if 'favors' not in item:
			favors = 1
		else:
			favors = item['favors'] + 1

		response = table.update_item(
			Key = {
			'brand': brand,
			'name': name
			},
			UpdateExpression="set favors = :f",
			ExpressionAttributeValues={
			':f': favors
			},
			ReturnValues="UPDATED_NEW"
			)

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
			favor = user['favor']
			# favor.append(key)
			favor.insert(0, {
						'brand': brand,
						'name': name
					})

			response = table.update_item(
				Key = {'account':account},
				UpdateExpression="set favor = :f",
				ExpressionAttributeValues={
				':f': favor
				},
				ReturnValues="UPDATED_NEW"
				)
			return redirect(url_for('info',brand=brand,name=name))
			# return render_template('info.html',
									# item=item)


@webapp.route('/items/info/removefavor/<brand>&<name>')
def rmfavor(brand, name):

	if 'account' not in session:
		table = get_table('Fragrances')
		key = {
		'brand': brand,
		'name': name
		}

		try:
			response = table.get_item(
				Key = key)
		except ClientError as e:
			raise e
		else:
			item = response['Item']
		return render_template('info.html',
								item=item,
								notLogin=True)
	else:
		table = get_table('Fragrances')
		key = {
		'brand': brand,
		'name': name
		}

		try:
			response = table.get_item(
				Key = key)
		except ClientError as e:
			raise e
		else:
			item = response['Item']

		if 'favors' not in item:
			favors = 1
		if item['favors'] > 0:
			favors = item['favors'] - 1
			response = table.update_item(
				Key = {
				'brand': brand,
				'name': name
				},
				UpdateExpression="set favors = :f",
				ExpressionAttributeValues={
				':f': favors
				},
				ReturnValues="UPDATED_NEW"
				)

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
			favor = user['favor']
			key = {
				'brand': brand,
				'name': name
				}
			if key in favor:
				favor.remove({
							'brand': brand,
							'name': name
						})

				response = table.update_item(
					Key = {'account':account},
					UpdateExpression="set favor = :f",
					ExpressionAttributeValues={
					':f': favor
					},
					ReturnValues="UPDATED_NEW"
					)
			return redirect(url_for('info',brand=brand,name=name))


@webapp.route('/addreview/<brand>&<name>', methods=['post'])
def addreview(brand, name):
	title = request.form.get('title',"")
	content = request.form.get('content',"")
	date = datetime.datetime.utcnow().strftime('(UTC)%H:%M:%S, %B %d, %Y')

	if 'account' not in session:
		table = get_table('Fragrances')
		key = {
		'brand': brand,
		'name': name
		}

		try:
			response = table.get_item(
				Key = key)
		except ClientError as e:
			raise e
		else:
			item = response['Item']
		return render_template('info.html',
								item=item,
								notLogin=True)
	else:
		account = session['account']
		table = get_table('Users')
		key = {
			'account': account
		}
		response = table.get_item(
				Key = key)
		user = response['Item']

		table = get_table('Fragrances')

		key = {
			'brand': brand,
			'name': name
		}
		response = table.get_item(
			Key=key)
		item = response['Item']
		if 'comments' not in item:
			comments = []
		else:
			comments = item['comments']

		newComment = {
			'name': user['name'],
			'date': date,
			'title': title,
			'content': content
		}
		comments.insert(0,newComment)
		response = table.update_item(
			Key = key,
			UpdateExpression="set comments = :c, reviews=:r",
			ExpressionAttributeValues={
			':c': comments,
			':r': len(comments)
			},
			ReturnValues="UPDATED_NEW"
			)
		return redirect(url_for('info',brand=brand,name=name))


@webapp.route('/favor_list')
def favorList():
	if 'account' not in session:
		return redirect(url_for('index'))
	else:
		account = session['account']
		table = get_table('Users')

		try:
			response = table.get_item(
				Key={
				'account': account
				})
		except ClientError as e:
			raise e
		else:
			user = response['Item']
			table = get_table('Fragrances')
			favors = []
			for favor in user['favor']:
				try:
					response = table.get_item(
						Key = {
						'brand': favor['brand'],
						'name': favor['name'],
						})
				except ClientError as e:
					raise e
				else:
					item = response['Item']
					favors.append({
						'brand': item['brand'],
						'name': item['name'],
						'key': item['key']
					})


			return render_template('list.html',
									name=user['name'],
									items=favors,
									)


# # # # # # # # # # # # # # # # # # # # # # # # # # search
# def filterByKeys(items, keys):
# 	options = {
# 		'brand': [],
# 		'family': [],
# 		'top': [],
# 		'heart': [],
# 		'base': [],
# 		'flavorist': [],
# 		'style': []
# 	}
# 	for item in items[::-1]:
# 		order = 0
# 		for key in keys:
# 			if key.lower() in str(item).lower():
# 				order += 1
# 			else:
# 				order -= 1
# 		if order < 1:
# 			items.remove(item)
# 		else:
# 			item['order'] = order
# 			if item['brand'] not in options['brand']:
# 				options['brand'].append(item['brand'])
# 			if item['family'] not in options['family']:
# 				options['family'].append(item['family'])
# 			for op in item['note']['top']:
# 				if op not in options['top']:
# 					options['top'].append(op)
# 			for op in item['note']['heart']:
# 				if op not in options['heart']:
# 					options['heart'].append(op)
# 			for op in item['note']['base']:
# 				if op not in options['base']:
# 					options['base'].append(op)
# 			for op in item['flavorist']:
# 				if op not in options['flavorist']:
# 					options['falsvorist'].append(op)
# 			for op in item['style']:
# 				if op not in options['style']:
# 					options['style'].append(op)
# 	return items

# def sort(items, sortBy='correlation'):
# 	if sortBy == 'correlation':
# 		items.sort(key=lambda k: (k.get('name',0),k.get('brand',0)))
# 		items.sort(key=lambda k: (k.get('rated',0),k.get('reviews',0)), reverse=True)
# 		items.sort(key=lambda k: (k.get('order',0)), reverse=True)
# 	elif sortBy == 'rated':
# 		items.sort(key=lambda k: (k.get('name',0),k.get('brand',0)))
# 		items.sort(key=lambda k: (k.get('order',0),k.get('reviews',0)), reverse=True)
# 		items.sort(key=lambda k: (k.get('rated',0)), reverse=True)
# 	elif sortBy == 'reviews':
# 		items.sort(key=lambda k: (k.get('name',0),k.get('brand',0)))
# 		items.sort(key=lambda k: (k.get('order',0),k.get('rated',0)), reverse=True)
# 		items.sort(key=lambda k: (k.get('reviews',0)), reverse=True)
# 	elif sortBy == 'brand':
# 		items.sort(key=lambda k: (k.get('name',0)))
# 		items.sort(key=lambda k: (k.get('order',0),k.get('rated',0),k.get('reviews',0)), reverse=True)
# 		items.sort(key=lambda k: (k.get('brand',0)))
# 	elif sortBy == 'name':
# 		items.sort(key=lambda k: (k.get('brand',0)))
# 		items.sort(key=lambda k: (k.get('order',0),k.get('rated',0),k.get('reviews',0)), reverse=True)
# 		items.sort(key=lambda k: (k.get('name',0)))

# 	return items, options


# @webapp.route('/search', methods=['post'])
# def search():
# 	keywords = request.form.get('keywords',"")
# 	if type(keywords) != str:
# 		keywords = str(keywords)
# 	keywords = keywords.replace(","," ")
# 	keywords = keywords.replace("."," ")
# 	keywords = keywords.replace("/"," ")
# 	keywords = keywords.replace("\\"," ")
# 	keywords = keywords.replace(";"," ")
# 	keywords = keywords.replace("&"," ")
# 	keywords = keywords.replace("%"," ")
# 	keywords = keywords.replace("|"," ")
# 	keywords = keywords.replace("#"," ")
# 	keywords = keywords.split()

# 	table = get_table('Fragrances')
# 	try:
# 		response = table.scan()
# 	except ClientError as e:
# 		raise e
# 	else:
# 		items = response['Items']
# 		items, options = filterByKeys(items, keywords)
# 		items = sort(items)
# 		num = len(items)

# 	if 'account' not in session:
# 		return render_template('search.html',
# 								items=items,
# 								num=num,
# 								keywords=" ".join(keywords),
# 								options=options
# 								)
# 	else:
# 		table = get_item('Users')
# 		try:
# 			response = table.get_item(
# 				Key = {
# 				'account': account
# 				})
# 		except ClientError as e:
# 			raise e
# 		else:
# 			user = response['Item']
# 			return render_template('search.html',
# 									name=user['name'],
# 									items=items,
# 									num=num,
# 									keywords=" ".join(keywords),
# 									optioins=options
# 									)

# @webapp.route('/search/resort/<keywords>', methods=['post'])
# def reSort(keywords):

# 	sortBy = request.form.get('sortBy',"correlation")

# 	if type(keywords) != str:
# 		keywords = str(keywords)
# 	keywords = keywords.replace(","," ")
# 	keywords = keywords.replace("."," ")
# 	keywords = keywords.replace("/"," ")
# 	keywords = keywords.replace("\\"," ")
# 	keywords = keywords.replace(";"," ")
# 	keywords = keywords.replace("&"," ")
# 	keywords = keywords.replace("%"," ")
# 	keywords = keywords.replace("|"," ")
# 	keywords = keywords.replace("#"," ")
# 	keywords = keywords.split()

# 	print keywords
# 	print sortBy
# 	table = get_table('Fragrances')
# 	try:
# 		response = table.scan()
# 	except ClientError as e:
# 		raise e
# 	else:
# 		items = response['Items']
# 		items, options = filterByKeys(items, keywords)
# 		items = sort(items, sortBy)
# 		num = len(items)

# 	if 'account' not in session:
# 		return render_template('search.html',
# 								items=items,
# 								num=num,
# 								keywords=" ".join(keywords),
# 								sortBy=sortBy
# 								)
# 	else:
# 		table = get_item('Users')
# 		try:
# 			response = table.get_item(
# 				Key = {
# 				'account': account
# 				})
# 		except ClientError as e:
# 			raise e
# 		else:
# 			user = response['Item']
# 			return render_template('search.html',
# 									name=user['name'],
# 									items=items,
# 									num=num,
# 									keywords=" ".join(keywords),
# 									sortBy=sortBy
# 									)

