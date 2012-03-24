from app.handlers import base
from mongoengine.queryset import DoesNotExist

class FrontPageHandler(base.BaseHandler):
    '''
    Check user status and either load the home screen or the
    welcome page.
    '''
    def on_get(self):
        #if not self.current_user:
        #    self.base_render("welcome.html")
        #else:
        #    self.redirect("/home")
	#self.base_render("welcome.html")
	self.base_render("intro.html")

class KeywordHandler(base.BaseHandler):
    def on_post(self):
	keywords = self.get_argument("txtSearch",None)
	if not keywords:
		return ("No Keywords entered",)
	keyword_array = keywords.split(" ")#User.objects(id = uid).get()
	if keywords=="suzu":
		keywords = "takkos"
	return (keywords,) 


    def on_success(self, feed):	
	self.base_render("timeline.html", feed = feed)
	

