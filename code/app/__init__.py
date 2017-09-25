from flask import Flask

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

webapp = Flask(__name__)
webapp.secret_key = 'secret_key'

from app import main
from app import sign_up
from app import log
from app import item
from app import search