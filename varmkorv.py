from inspect import signature
from werkzeug.wrappers import Request, Response
from werkzeug.utils import cached_property
from secure_cookie.cookie import SecureCookie


class ControllerApps(object):
    def __init__(self):
        self.apps = []

    def register(self, app: "App"):
        if app not in self.apps:
            self.apps.append(app)

    def notify(self):
        for app in self.apps:
            app._compile()


class Controller(object):
    def __init__(self):
        self._apps = ControllerApps()

    def __setattr__(self, prop, val):
        object.__setattr__(self, prop, val)
        if not prop.startswith("_"):
            self._apps.notify()


class Caller(object):
    def __init__(self, app: "App", environ, start_response, request: Request):
        self.app = app
        self.environ = environ
        self.start_response = start_response
        self.request = request

    def __call__(self, c, properties: list, sign: list):
        num_properties = len(properties)

        if num_properties > len(sign):
            print("There are too many properties in the URI")
            # TODO: Throw exception instead
            return self._execute(self.app._render_404, [self.request])

        args = [self.request]

        for i, param in enumerate(sign):
            if num_properties > i:
                print(param["name"], "exist")
                try:
                    args.append(param["annotation"](properties[i]))
                except ValueError:
                    print("Value error")
                    # TODO: Throw exception instead
                    return self._execute(self.app._render_404, [self.request])
                continue
            # print(param["name"], "does not exist")
            if param["mandatory"]:
                print("FAILURE, it's mandatory")
                # TODO: Throw exception instead
                return self._execute(self.app._render_404, [self.request])
            args.append(param["default"])

        return self._execute(c, args)

    def _execute(self, c, args: list):
        response = c(*args)
        for c in self.app.on_response:
            c(self.request, response)
        return response(self.environ, self.start_response)


def _compile_signature(c):
    sign = signature(c)
    params = sign.parameters.values()
    first = True
    out = []
    for param in params:
        if first:
            first = False
            continue
        out.append(
            {
                "name": param.name,
                "mandatory": param.default is param.empty,
                "default": param.default,
                "annotation": param.annotation,
            }
        )
    return out


class App(object):
    def __init__(self, root: Controller):
        self.root = root
        self._routes = None
        self._routes_num = None
        self._routes_max = None
        self._compile()
        self.on_request = []
        self.on_response = []

    def _compile(self):
        data = {}

        def compile_entry(controller: Controller, parents: tuple = ()):
            controller._apps.register(self)
            if callable(controller):
                entry = {
                    "signature": _compile_signature(controller),
                    "instance": controller,
                }
                data[parents] = entry
            for prop_name in dir(controller):
                if len(prop_name) == 0 or prop_name[0] == "_":
                    continue
                prop = getattr(controller, prop_name)
                name = list(parents)
                name.append(prop_name)
                if callable(prop):
                    entry = {
                        "signature": _compile_signature(prop),
                        "instance": prop,
                    }
                    data[tuple(name)] = entry
                if isinstance(prop, Controller):
                    compile_entry(prop, tuple(name))

        compile_entry(self.root)

        ma = 0
        grouped = {}
        for path, route in data.items():
            if len(path) not in grouped:
                grouped[len(path)] = {}
            grouped[len(path)][path] = route
            if len(path) > ma:
                ma = len(path)

        self._routes = grouped
        self._routes_num = tuple(sorted(grouped, reverse=True))
        self._routes_max = ma

    def __call__(self, environ, start_response):
        request = Request(environ)
        for c in self.on_request:
            c(request)
        parts = request.path.strip("/").split("/")
        caller = Caller(self, environ, start_response, request)
        if len(parts) == 1 and parts[0] == "":
            parts = []
        lowest = min(self._routes_max, len(parts))
        for i in range(lowest, -1, -1):
            try:
                routes = self._routes[i]
            except KeyError:
                continue
            name = tuple(parts[:i])
            try:
                route = routes[name]
            except KeyError:
                continue
            return caller(route["instance"], parts[i:], route["signature"])
        return caller(self._render_404, [], [])

    def _render_404(self, request: Request):
        return Response("404")


class LoginInstance:
    def __init__(self, request: Request, login: "LoginManager"):
        self._request = request
        self._login = login

    @cached_property
    def session(self) -> SecureCookie:
        data = self._request.cookies.get(self._login.cookie_name)
        if not data:
            return SecureCookie(secret_key=self._login.secret_key)
        return SecureCookie.unserialize(data, self._login.secret_key)

    @cached_property
    def user(self):
        try:
            user_id = self.session["user_id"]
        except KeyError:
            return None
        if not user_id:
            return None
        return self._login.load_user(user_id)

    def login_user(self, user):
        self.session["user_id"] = user.get_id()
        del self.user


class LoginManager:
    def __init__(self, secret_key, load_user, cookie_name="session", httponly=True):
        self.secret_key = secret_key
        self.load_user = load_user
        self.cookie_name = cookie_name
        self.httponly = httponly

    def _on_request(self, request: Request):
        setattr(request, "login", LoginInstance(request, self))

    def _on_response(self, request: Request, response: Response):
        if getattr(request, "login").session.should_save:
            session_data = getattr(request, "login").login.session.serialize()
            response.set_cookie(self.cookie_name, session_data, httponly=self.httponly)

    def wrap_application(self, app: App):
        app.on_request.append(self._on_request)
        app.on_response.append(self._on_response)


class PeeweeWrapper:
    def __init__(self, db):
        self.db = db

    def _on_request(self, request: Request):
        self.db.connect(reuse_if_open=True)

    def _on_response(self, request: Request, response: Response):
        def close_db():
            if not self.db.is_closed():
                self.db.close()

        response.call_on_close(close_db)

    def wrap_application(self, app: App):
        app.on_request.append(self._on_request)
        app.on_response.append(self._on_response)