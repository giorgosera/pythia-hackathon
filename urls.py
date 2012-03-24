#############################
# URL patterns.             #
# Author: Giorgos Eracleous #
#############################

from app.handlers import base,front

url_patterns = [
    ("/", front.FrontPageHandler),
    ("/home", front.FrontPageHandler),
    ("/keywords/send", front.KeywordHandler),
]
