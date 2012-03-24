#############################
# URL patterns.             #
# Author: Giorgos Eracleous #
#############################

from app.handlers import base

url_patterns = [
    ("/", base.WelcomeHandler),
    ("/home", base.HomeHandler),
]
