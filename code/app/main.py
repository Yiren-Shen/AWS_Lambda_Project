from app import webapp
from flask import render_template, session , request

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


def get_table(table_name):
	dynamodb = boto3.resource('dynamodb')
	table = dynamodb.Table(table_name)
	return table

from search import sort

def get_all_fragrances():
	table = get_table('Fragrances')
	response = table.scan()
	items = response['Items']
	return items

def get_most_reviews(topN):
	items = get_all_fragrances()
	items = sort(items, 'reviews')
	if len(items) < topN:
		return items
	else:
		items = items[:topN]
		return items

def get_trend_favors(topN):
	items = get_all_fragrances()
	items = sort(items, 'favors')
	if len(items) < topN:
		return items
	else:
		items = items[:topN]
		return items

def get_top_rated(topN):
	items = get_all_fragrances()
	items = sort(items, 'rating')
	if len(items) < topN:
		return items
	else:
		items = items[:topN]
		return items


def get_favorites(user, num):
	table = get_table('Fragrances')
	favorites = []
	count = 0
	if user['favor'] != None:
		for favorite in user['favor']:
			try:
				response = table.get_item(
					Key = {
					'brand': favorite['brand'],
					'name': favorite['name'],
					})
			except ClientError as e:
				raise e
			else:
				item = response['Item']
				favorites.append({
					'brand': item['brand'],
					'name': item['name'],
					'key': item['key']
				})
				count += 1
				if count == num:
					break
	return favorites


@webapp.route('/')
@webapp.route('/index')
def index():

	# hottest fragrances
	frags_most_reviews = get_most_reviews(5)
	frags_trend_favors = get_trend_favors(5)
	frags_top_rated = get_top_rated(5)

	# is user login
	if 'account' not in session:
		return render_template('index.html',
								frags_most_reviews=frags_most_reviews,
								frags_trend_favors=frags_trend_favors,
								frags_top_rated=frags_top_rated,
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
			session.pop('account', None)
			err_msg = e.response['Error']['Message']
			return render_template('index.html',
									login_err_msg=err_msg,
									frags_most_reviews=frags_most_reviews,
									frags_trend_favors=frags_trend_favors,
									frags_top_rated=frags_top_rated,
									)
		else:
			user = response['Item']
			favorites = get_favorites(user, 5)
			return render_template('index.html',
									frags_most_reviews=frags_most_reviews,
									frags_trend_favors=frags_trend_favors,
									frags_top_rated=frags_top_rated,
									name=user['name'],
									favorites=favorites,
									)







