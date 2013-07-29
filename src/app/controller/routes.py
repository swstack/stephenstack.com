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


@bottle.get('/static/<filepath:path>')
def static(filepath):
    if SERVER:
        return bottle.static_file(filepath, root=SERVER.get_static_root())


@bottle.post("/signin/<state>")
def signin(state):
    if SERVER:
        return SERVER.signin(state)


@bottle.post('/logout')
def logout():
    if SERVER:
        return SERVER.logout()


@bottle.get("/")
def index():
    if SERVER:
        return SERVER.index()
