import bottle

SERVER = None


class Router(object):
    #================================================================================
    # Construction
    #================================================================================
    def __init__(self):
        pass

    def start(self):
        pass

    #================================================================================
    # Internal
    #================================================================================

    #================================================================================
    # Public
    #================================================================================
    def register_server(self, server):
        global SERVER
        SERVER = server




@bottle.post()
def login(state):
    if SERVER:
        return SERVER.login(state)


@bottle.post('/logout')
def logout():
    if SERVER:
        return SERVER.logout()


@bottle.get("/")
def index():
    if SERVER:
        return SERVER.index()
