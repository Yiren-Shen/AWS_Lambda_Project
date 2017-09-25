from app import webapp
from flask import render_template, request, session, redirect, url_for

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from app.main import get_table, get_all_fragrances, get_most_reviews, get_trend_favors, get_top_rated


@webapp.route('/login', methods=['post'])
def login():

	table = get_table('Users')

	session['account'] = request.form['account']
	account = session['account']
	password = request.form.get('password', "")


	frags_most_reviews = get_most_reviews(5)
	frags_trend_favors = get_trend_favors(5)
	frags_top_rated = get_top_rated(5)

	try:
		response = table.get_item(
			Key = {
				'account': account,
			})
	except ClientError as e:
		session.pop('account', None)
		err_msg = e.response['Error']['Message']
		return render_template('index.html',
								frags_most_reviews=frags_most_reviews,
								frags_trend_favors=frags_trend_favors,
								frags_top_rated=frags_top_rated,
								login_err_msg=err_msg,
								)
	else:
		if 'Item' not in response:
			session.pop('account', None)
			err_msg = "Account does not exist."
			return render_template('index.html',
									frags_most_reviews=frags_most_reviews,
									frags_trend_favors=frags_trend_favors,
									frags_top_rated=frags_top_rated,
									login_err_msg=err_msg,
									)
		elif response['Item']['active']:
			user = response['Item']
			if (password != user['password']):
				session.pop('account', None)
				err_msg = "Incorrect password."
				return render_template('index.html',
										frags_most_reviews=frags_most_reviews,
										frags_trend_favors=frags_trend_favors,
										frags_top_rated=frags_top_rated,
										login_err_msg=err_msg,
										)
			else:
				return redirect(url_for('index'))
		else:
			session.pop('account', None)
			err_msg = "Your email hasn't been verified. You can register again if you lost the verification email. "
			return render_template('index.html',
									frags_most_reviews=frags_most_reviews,
									frags_trend_favors=frags_trend_favors,
									frags_top_rated=frags_top_rated,
									login_err_msg=err_msg,
									)

@webapp.route('/logout')
def logout():
	session.pop('account', None)
	return redirect(url_for('index'))
