from collections import defaultdict
from inspect import signature
from werkzeug.wrappers import Request, Response


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
        self._middlewares = []

    def __setattr__(self, prop, val):
        object.__setattr__(self, prop, val)
        if not prop.startswith("_") and prop != "add_middleware":
            self._apps.notify()

    def add_middleware(self, middleware):
        self._middlewares.append(middleware)
        self._apps.notify()
        return self

    def _get_exposed(self):
        actions = []
        controllers = {}
        if callable(self):
            actions.append(
                {
                    "name": None,
                    "instance": self,
                    "verb": None,
                }
            )
        for prop_name in dir(self):
            if (
                len(prop_name) == 0
                or prop_name[0] == "_"
                or prop_name == "add_middleware"
            ):
                continue
            prop = getattr(self, prop_name)
            if callable(prop):
                actions.append(
                    {
                        "name": prop_name,
                        "instance": prop,
                        "verb": None,
                    }
                )
            if isinstance(prop, Controller):
                controllers[prop_name] = prop
        return {
            "actions": actions,
            "controllers": controllers,
        }


class VerbController(Controller):
    def __init__(self):
        self._verbs = {
            "_get": "GET",
            "_head": "HEAD",
            "_post": "POST",
            "_put": "PUT",
            "_delete": "DELETE",
            "_connect": "CONNECT",
            "_options": "OPTIONS",
            "_trace": "TRACE",
            "_patch": "PATCH",
        }
        Controller.__init__(self)

    def __setattr__(self, prop, val):
        object.__setattr__(self, prop, val)
        if prop == "add_middleware":
            return
        if not prop.startswith("_") or prop in self._verbs:
            self._apps.notify()

    def _get_exposed(self):
        actions = []
        controllers = {}
        for prop_name in dir(self):
            if len(prop_name) == 0 or prop_name == "add_middleware":
                continue
            prop = getattr(self, prop_name)
            if callable(prop) and prop_name in self._verbs:
                actions.append(
                    {
                        "name": None,
                        "instance": prop,
                        "verb": self._verbs[prop_name],
                    }
                )
            if isinstance(prop, Controller):
                controllers[prop_name] = prop
        return {
            "actions": actions,
            "controllers": controllers,
        }


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
        self._middlewares = []
        self._compile()

    def _compile(self):
        data = defaultdict(dict)

        def compile_entry(
            controller: Controller, parents: tuple = (), controller_instances=[]
        ):
            controller_instances.append(controller)

            def add_middlewares(instance):
                for controller_instance in reversed(controller_instances):
                    for middleware in reversed(controller_instance._middlewares):
                        instance = middleware(instance)
                for middleware in reversed(self._middlewares):
                    instance = middleware(instance)
                return instance

            controller._apps.register(self)

            exposed = controller._get_exposed()

            for action in exposed["actions"]:
                name = list(parents)
                if action["name"]:
                    name.append(action["name"])
                entry = {
                    "signature": _compile_signature(action["instance"]),
                    "instance": add_middlewares(action["instance"]),
                }
                data[tuple(name)][action["verb"]] = entry

            for prop_name, prop in exposed["controllers"].items():
                name = list(parents)
                name.append(prop_name)
                compile_entry(prop, tuple(name), controller_instances)

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

    def _print_route_debug(self):
        for data in self._routes.values():
            for name_tuple, routes_data in data.items():
                print(name_tuple)
                for verb, route in routes_data.items():
                    print("    Verb:", verb)
                    print("        Signature:", route["signature"])
                    print("        Instance:", route["instance"])

    def __call__(self, environ, start_response):
        request = Request(environ)
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
            verb = request.method
            try:
                route = routes[name][verb]
            except KeyError:
                try:
                    route = routes[name][None]
                except KeyError:
                    continue
            return caller(route["instance"], parts[i:], route["signature"])
        return caller(self._render_404, [], [])

    def _render_404(self, request: Request):
        return Response("404")

    def add_middleware(self, handler):
        self._middlewares.append(handler)
        self._compile()
        return self
