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
	self.base_render("welcome.html")

class KeywordHandler(base.BaseHandler):
    def on_post(self):
	keywords = self.get_argument("keywords",None)
	#user = User.objects(id = uid).get()
	
	return (keywords,) 


    def on_success(self, feed):
        self.xhr_response.update({"feed": kewords})  
        self.write(self.xhr_response) 

