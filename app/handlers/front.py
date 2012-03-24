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


    def on_post(self):
	qutation = self.get_argument("id",None)
	#user = User.objects(id = uid).get()
	
	return (feed,) 


    def on_success(self, feed):
        self.xhr_response.update({"feed": feed.moderator})  
        self.write(self.xhr_response) 
