from app import webapp
from flask import render_template, request, session, redirect

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

import hashlib

from app.main import get_table, get_all_fragrances, get_most_reviews, get_trend_favors, get_top_rated
from config import my_email


@webapp.route('/sign_up', methods=['post'])
def sign_up():

	table = get_table('Users')

	account = request.form.get('account',"")
	password = request.form.get('password',"")
	conf_pw = request.form.get('conf_pw',"")
	first_name = request.form.get('first_name',"")
	last_name = request.form.get('last_name',"")

	frags_most_reviews = get_most_reviews(5)
	frags_trend_favors = get_trend_favors(5)
	frags_top_rated = get_top_rated(5)

	if password != conf_pw:
		err_msg = "Passwords do not match."
		return render_template('index.html',
								clickSignUp=True,
								signup_err_msg=err_msg,
								frags_most_reviews=frags_most_reviews,
								frags_trend_favors=frags_trend_favors,
								frags_top_rated=frags_top_rated,
								)


	try:
		response = table.get_item(
			Key={
				'account': account,
			})
	except ClientError as e:
		err_msg = e.response['Error']['Message']
		return render_template('index.html',
								clickSignUp=True,
								signup_err_msg=err_msg,
								frags_most_reviews=frags_most_reviews,
								frags_trend_favors=frags_trend_favors,
								frags_top_rated=frags_top_rated,
								)
	else:
		if ('Item' in response) and response['Item']['active']:
			err_msg = "Account already exists."
			return render_template('index.html',
									clickSignUp=True,
									signup_err_msg=err_msg,
									frags_most_reviews=frags_most_reviews,
									frags_trend_favors=frags_trend_favors,
									frags_top_rated=frags_top_rated,
									)
		else:
			src = account+password
			code = hashlib.md5(src).hexdigest()

			response = table.put_item(
				Item={
					'account': account,
					'password': password,
					'name': {
						'first': first_name,
						'last': last_name,
					},
					'favor': [],
					'post': [],
					'code': code,
					'active': False
				})

			ses = boto3.client('ses')

			name = first_name + " " + last_name
			link = request.url_root + 'sign_up/verify/' + account + '&' + code

			response = ses.send_email(
			    Source=my_email,
			    Destination={
			        'ToAddresses': [
			            account,
			        ]
			    },
			    Message={
			        'Subject': {
			            'Data': 'Welcome to the Fragrance Community'
			        },
			        'Body': {
			            # 'Text': {
			            #     'Data': 'string',
			            #     'Charset': 'string'
			            # },
			            'Html': {
			                'Data': '''
<h2>Hi 
'''+

name

+'''
!</h2>
<p>Welcome to the <a href="
'''+
request.url_root
+'''
">Fragrance Community</a>.</p>
<h3>Verify Your Account</h3>
<p>To complete your registration, please verify your email address by clicking this <a href="
'''+
link
+'''
"> Link </a>.</p>
<p>Alternatively, you can copy and paste the following link into your browser's address window: </p>
<p>
'''+
link+'''
</p>
			                '''
			            }
			        }
			    }
			)

			signUpMsg = ["To complete the registration, check your emails.",
				"You'll get an email with a link to comfirm that the address is yours."]
			return render_template('index.html',
									clickSignUp=True,
									signUpMsg=signUpMsg,
									frags_most_reviews=frags_most_reviews,
									frags_trend_favors=frags_trend_favors,
									frags_top_rated=frags_top_rated,
									)



@webapp.route('/sign_up/verify/<email>&<code>')
def verify(email, code):
	print email
	print code


	frags_most_reviews = get_most_reviews(5)
	frags_trend_favors = get_trend_favors(5)
	frags_top_rated = get_top_rated(5)

	table = get_table('Users')
	try:
		response = table.get_item(
			Key={
			'account': email
			})
	except Exception as e:
		raise e
	else:
		if 'Item' in response:
			user = response['Item']
			if user['active'] == True:
				return 'Your Account is Active.'
			elif user['code'] == code:
				response = table.update_item(
					Key={
						'account': email
					},
					UpdateExpression="set active = :a",
					ExpressionAttributeValues={
						':a': True
					},
					ReturnValues="UPDATED_NEW"
				)
				signUpMsg = ["Congratulations!",
					"Your account has been successfully created!",
					"Please login with your email and have fun! "
				]
				return render_template('index.html',
										clickSignUp=True,
										needSignUp=True,
										signUpMsg=signUpMsg,
										frags_most_reviews=frags_most_reviews,
										frags_trend_favors=frags_trend_favors,
										frags_top_rated=frags_top_rated,
										)
		else:
			signUpMsg = ['Your must Sign Up before activation.']
			return render_template('index.html',
									clickSignUp=True,
									signUpMsg=signUpMsg,
									frags_most_reviews=frags_most_reviews,
									frags_trend_favors=frags_trend_favors,
									frags_top_rated=frags_top_rated,
									)





