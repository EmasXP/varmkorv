# Varmkorv

Varmkorv is a CherryPy inspired micro framework using Werkzeug.

This is just a proof of concept. You are free to use it if you like, or find inspiration from it, or copy bits and pieces of it.

You might wonder if the world really need another Python web framework, and the answer is probably: no. I created this framework out of curiosity. The routes are "complied" (and recompiled if changed during runtime), and it does not contain much fluff at all. That makes this framework really speedy - way speedier than CherryPy (and Flask too for that matter).

I have implemented support for cookie authentication and Peewee. That is what I need for my personal projects, and might not suit all.


## Hello, world!

```python
from varmkorv import Controller, App
from werkzeug import Request, Response

class First(Controller):
    def __call__(self, request: Request):
        return Response('Hello, world!')

app = App(First())

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

Point your browser to `http://localhost:8080/` and feel welcomed (if you call yourself "world", that is).


## Actions (views)

The example above contain just one route (or action, or view, or whatever name you use). Let's add a few more:

```python
from varmkorv import Controller, App
from werkzeug import Request, Response

class First(Controller):
    def __call__(self, request: Request):
        return Response('Hello, world!')

    def kebab(self, request: Request):
        return Response('So nice')

    def pizza(self, request: Request):
        return Response('Also very nice')

app = App(First())

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

We now have three routes:

* `http://localhost:8080/`
* `http://localhost:8080/kebab`
* `http://localhost:8080/pizza`


## Sub-controllers

If you are familiar with Flask, you probably know about Blueprints, but Varmkorv uses sub-controllers instead:

```python
from varmkorv import Controller, App
from werkzeug import Request, Response

class Food(Controller):
    def __call__(self, request: Request):
        return Response('One has to eat')

    def kebab(self, request: Request):
        return Response('So nice')

    def pizza(self, request: Request):
        return Response('Also very nice')

class First(Controller):
    def __call__(self, request: Request):
        return Response('Hello, world!')

first = First()
first.food = Food()

app = App(first)

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

In this example we are creating an instance of `Food` and pass it as a the property `food` of `First`.

We now have these routes:

* `http://localhost:8080/`
* `http://localhost:8080/food`
* `http://localhost:8080/food/kebab`
* `http://localhost:8080/food/pizza`


### Sub-controllers in \_\_init\_\_

```python
from varmkorv import Controller, App
from werkzeug import Request, Response

class Food(Controller):
    def __call__(self, request: Request):
        return Response('You got to eat')

    def kebab(self, request: Request):
        return Response('So nice')

    def pizza(self, request: Request):
        return Response('Also very nice')

class First(Controller):
    def __init__(self):
        Controller.__init__(self)
        self.food = Food()

    def __call__(self, request: Request):
        return Response('Hello, world!')

app = App(First())

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

### More on the properties of a controller

Every callable property of a controller that does not start with a `_` (underscore) are treated as an action (or view, or whatever you want to call it).

Every property that inherits `Controller` that does not start with a `_` is treated as a sub-controller. A sub-controller is _also_ treated as an action (or view, and so on) if it's callable.


## URL parameters

Let's create a very simple app:

```python
from varmkorv import Controller, App
from werkzeug import Request, Response

class First(Controller):
    def __call__(self, request: Request):
        return Response('Good morning')

    def hello(self, request: Request, name: str):
        return Response('Hello, ' + name)

app = App(First())

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

The `hello` action now has a _mandatory_ `name` parameter.

* `http://localhost:8080/` - Says "Good morning"
* `http://localhost:8080/hello` - Gives 404
* `http://localhost:8080/hello/Gordon` - Says "Hello, Gordon"


### Optional parameters

And now, let's alter the code to support an _optional_ `name` parameter instead:

```python
from varmkorv import Controller, App
from werkzeug import Request, Response

class First(Controller):
    def __call__(self, request: Request):
        return Response('Good morning')

    def hello(self, request: Request, name: str = None):
        if not name:
            return Response('Hello, mysterious person')
        return Response('Hello, ' + name)

app = App(First())

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

It's just as simple as adding `= None` to the definition.


### Value error

```python
from varmkorv import Controller, App
from werkzeug import Request, Response

class First(Controller):
    def __call__(self, request: Request):
        return Response('Good morning')

    def user(self, request: Request, user_id: int):
        user = User.find_or_none(User.id == user_id)
        if not user:
            return Response('Nobody')
        return Response(user.name)

app = App(First())

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

* `http://localhost:8080/hello` - Gives 404
* `http://localhost:8080/hello/123` - Tells us the name of the user
* `http://localhost:8080/hello/Gordon` - Gives 404 because "Gordon" is not an integer


### Custom data types


```python
from varmkorv import Controller, App
from werkzeug import Request, Response

class Food(object):
    def __init__(self, value):
        if value == 'human':
            raise ValueError;
        self.value = value

class First(Controller):
    def __call__(self, request: Request):
        return Response('Good morning')

    def eat(self, request: Request, food: Food):
        return Response(food.value + ' sounds good')

app = App(First())

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

* `http://localhost:8080/eat/kebab` - Says "kebab sounds good"
* `http://localhost:8080/eat/pizza` - Says "pizza sounds good"
* `http://localhost:8080/eat/human` - Gives 404

## VerbController

A `Controller` does not care which HTTP method is used when requesting a page. That is not always the desired behavior. Writing a REST API this way would be an interesting challenge. Or maybe one can see it as a good way of learning new swear words. Another solution would be to use `VerbController` instead.

```python
from varmkorv import VerbController, App
from werkzeug import Request, Response

class Food(VerbController):
    def _get(self, request: Request):
        return Response('GET me some food')

    def _post(self, request: Request):
        return Response('POST me some food')

class First(VerbController):
    def __init__(self):
        VerbController.__init__(self)
        self.food = Food()

    def _get(self, request: Request):
        return Response('Hello, GET')

app = App(First())

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

Now we have these endpoints:

* `GET http://localhost:8080/` - Says "Hello, GET"
* `GET http://localhost:8080/food` - Says "GET me some food"
* `POST http://localhost:8080/food` - Says "POST me some food"

One can have a `VerbController` as a sub-controller of `Controller` and vice verca.

These are the available methods:

* \_get - GET
* \_head - HEAD
* \_post - POST
* \_put - PUT
* \_delete - DELETE
* \_connect - CONNECT
* \_options - OPTIONS
* \_trace - TRACE
* \_patch - PATCH

## Middleware

I am going to show how middlewares work later under this section, but first I want to show you the two built in middlewares: Peewee and CookieLogin.

### Peewee

```python
from varmkorv import Controller, App
from varmkorv.middleware.peewee import PeeweeMiddleware
from werkzeug import Request, Response
from playhouse.apsw_ext import APSWDatabase

class First(Controller):
    def __call__(self, request: Request, user_id: int):
        user = User.find_or_none(User.id == user_id)
        if not user:
            return Response('Nobody')
        return Response(user.name)

app = App(First())

db = APSWDatabase('my-food-website.db')

app.add_middleware(PeeweeMiddleware(db))

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```


### CookieLogin

```python
from varmkorv import Controller, App
from varmkorv.middleware.peewee import PeeweeMiddleware
from varmkorv.middleware.cookielogin import CookieLoginMiddleware
from peewee import Model, AutoField, CharField
from playhouse.apsw_ext import APSWDatabase

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    id = AutoField()
    username = CharField()
    password = CharField()

    def verify_password(self, password):
        # Verify the password. I recommend using passlib.
        # I'll just return True here for the sake of it
        # This method is not needed by LoginManager, but you probably need
        # something similar
        return True

    def get_id(self):
        # Return the id of the user. This one is needed by LoginManager
        return str(self.id)

class First(Controller):
    def login(self, request: Request):
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.find_or_none(User.username == username)

        if not user or not user.verify_password(password):
            return Response('Wrong username or password')

        request.login.login_user(user)

        return Response('Successfully logged in')

    def check(self, request: Request):
        if not request.login.user:
            return Response('Not logged in')
        return Response('Logged in as ' + request.login.user.username)

app = App(First())

db = APSWDatabase('my-food-website.db')
app.add_middleware(PeeweeMiddleware(db))

def load_user(user_id):
    return User.get_or_none(User.id == user_id)

app.add_middleware(CookieLoginMiddleware('secret', load_user))
```

I am using Peewee in this example, but you are free to use whatever you like.

Feels like more work needs to be done on the CookieLoginMiddleware to make it more secure.

### How middlewares work, and how to create new ones

Peewee and CookieLogin use Varmkorv's middleware functionality.

Let's create our own:

```python
from varmkorv import Controller, App
from werkzeug import Request, Response

class First(Controller):
    def __call__(self, request: Request):
        print('Hello, world!')
        return Response('Hello, world!')

app = App(First())

def my_middleware(next):
    def handle(request: Request, *args, **kwargs):
        print('This is me, doing things on the request!')
        response = next(request, *args, **kwargs)
        print('And here I am again, doing things on the response!')
        return response
    return handle

app.add_middleware(my_middleware)

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

If you point your browser to `http://localhost:8080/` and go back to the terminal where you are running the application server, you will see the following:

```
This is me, doing things on the request!
Hello, world!
And here I am again, doing things on the response!
```

That's a lot of shouting.

### The order of the middlewares

Now we are going to add two middlewares to our application and see what happens:

```python
from varmkorv import Controller, App
from werkzeug import Request, Response

class First(Controller):
    def __call__(self, request: Request):
        print('Hello, world!')
        return Response('Hello, world!')

app = App(First())

def my_first_middleware(next):
    def handle(request: Request, *args, **kwargs):
        print('Request: first middleware')
        response = next(request, *args, **kwargs)
        print('Response: first middleware')
        return response
    return handle

def my_second_middleware(next):
    def handle(request: Request, *args, **kwargs):
        print('Request: second middleware')
        response = next(request, *args, **kwargs)
        print('Response: second middleware')
        return response
    return handle

app.add_middleware(my_first_middleware)
app.add_middleware(my_second_middleware)

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

And again, refresh your browser and go back to the terminal. You will see this:

```
Request: first middleware
Request: second middleware
Hello, world!
Response: second middleware
Response: first middleware
```

This is quite important: _The middleware you add first is the one being included first_. We added `my_first_middleware` first, and `Request: first middleware` is what we see first in the terminal.

To put it differently: one shall add the middleware of highest priority first. That's why we in the CookieLogin example added `PeeweeMiddleware` before `CookieLoginMiddleware`, because `CookieLoginMiddleware` needs the database connection provided by `PeeweeMiddleware`.

I chose this order because I think it's the most intuitive. At least in my brain that makes the most sense, and if I am more tired than usual one day, hopefully I will add wrappers in the correct order without the need to think.

### Middleware on controllers

This example is a bit lenghty, but here we go:

```python
from varmkorv import Controller, App
from werkzeug import Request, Response

def my_app_middleware(next):
    def handle(request: Request, *args, **kwargs):
        print('Request: app middleware')
        response = next(request, *args, **kwargs)
        print('Response: app middleware')
        return response
    return handle

def my_food_controller_middleware(next):
    def handle(request: Request, *args, **kwargs):
        print('Request: food controller middleware')
        response = next(request, *args, **kwargs)
        print('Response: food controller middleware')
        return response
    return handle

class Food(Controller):
    def __init__(self):
        Controller.__init__(self)
        self.add_middleware(my_food_controller_middleware)  # Adding on controller level

    def __call__(self, request: Request):
        print('Hello, food!')
        return Response('Hello, food!')

class First(Controller):
    def __init__(self):
        Controller.__init__(self)
        self.food = Food()  # Attaching the food sub-controller

    def __call__(self, request: Request):
        print('Hello, first!')
        return Response('Hello, first!')

app = App(First())

app.add_middleware(my_app_middleware) # Adding on app level

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

I feel like I need to excuse myself for this long example. Just to be clear. in this example we have:

* The `my_app_middlewarer` being attached to the application.
* The `Food` controller being attached as a sub-controller to `First`
* The `my_food_controller_middleware` being attached to the `Food` controller.

If we point the browser to `http://localhost:8080/` we will see the following in the terminal:

```
Request: app middleware
Hello, first!
Response: app middleware
```

And if we point the point the browser to `http://localhost:8080/food` we will see the following in the terminal:

```
Request: app middleware
Request: food controller middleware
Hello, food!
Response: food controller middleware
Response: app middleware
```

There are two things worth noticing here:

* The middleware of the `Food` controller are only going to be included if the `Food` controller is used.
* The middleware of the parents has higher priority than the sub-controller. In other words: each sub-controller's middleware are included _after_ the middleware its parents' middleware.

All the parent controller's middleware are going to be included. That means that you can for example have an "admin" controller where you limit who has access, and that will be reflected on all of its sub-controllers.

### Middleware on actions

```python
from varmkorv import Controller, App, add_middleware
from werkzeug import Request, Response

def my_action_middleware(next):
    def handle(request: Request, *args, **kwargs):
        print('Request: action middleware')
        response = next(request, *args, **kwargs)
        print('Response: action middleware')
        return response
    return handle

class First(Controller):
    @add_middleware(my_action_middleware)
    def __call__(self, request: Request):
        print('Hello, first!')
        return Response('Hello, first!')

app = App(First())

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

We are using the `add_middleware` decorator here. This decorator works just as ordinary decorators. The middleware will be called, and the function will be wrapped. That means it will work well if you want to mix with other decorators. Make sure to always wrap the function in the decorator using functools if you are writing decorators, otherwise Varmkorv will not be able to find the proper definition of the function.

The `add_middleware` decorator also works for controllers:

```python
from varmkorv import Controller, App, add_middleware
from werkzeug import Request, Response

def my_controller_middleware(next):
    def handle(request: Request, *args, **kwargs):
        print('Request: controller middleware')
        response = next(request, *args, **kwargs)
        print('Response: controller middleware')
        return response
    return handle

def my_action_middleware(next):
    def handle(request: Request, *args, **kwargs):
        print('Request: action middleware')
        response = next(request, *args, **kwargs)
        print('Response: action middleware')
        return response
    return handle

@add_middleware(my_controller_middleware)
class First(Controller):
    @add_middleware(my_action_middleware)
    def __call__(self, request: Request):
        print('Hello, first!')
        return Response('Hello, first!')

app = App(First())

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

## Static files

You can use the [SharedDataMiddleware](https://werkzeug.palletsprojects.com/en/2.0.x/middleware/shared_data/) from Werkzeug to serve static files. Here's an example:

```python
import os
from varmkorv import Controller, App
from werkzeug import Request, Response
from werkzeug.middleware.shared_data import SharedDataMiddleware

class First(Controller):
    def __call__(self, request: Request):
        return Response('Hello, world!')

app = App(First())

app = SharedDataMiddleware(app, {
    '/static': os.path.join(os.path.dirname(__file__), 'static')
})

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

This example will expose the "static" folder located in the same directory as the current file.

When running on production you might want to serve your static files from a web server (like NGINX, Apache or Caddy to name a few). That will serve the files faster, put less stress on your application, and these servers can also utilize cache and other cool features. Of course you can also choose to stick with SharedDataMiddleware too.

## Templates

Varmkorv does not ship with any template engine, but I am going to show you examples on how to use [Jinja](https://jinja.palletsprojects.com/) and [Mako](https://www.makotemplates.org/).

### Jinja

```python
from varmkorv import Controller, App
from werkzeug import Request, Response
from jinja2 import Environment, FileSystemLoader, select_autoescape

jinja = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape()
)


class First(Controller):
    def __call__(self, request: Request):
        return Response(
            jinja.get_template('index.html.j2') \
                .render(name='World')
        )


app = App(First())

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

And in `templates/index.html.j2`:

```
Hello, {{ name }}!
```

### Mako

```python
import os
from varmkorv import Controller, App
from werkzeug import Request, Response
from mako.lookup import TemplateLookup

mako = TemplateLookup(
    directories=[
        os.path.join(os.path.dirname(__file__), 'templates')
    ],
    module_directory='/tmp/mako_modules'
)


class First(Controller):
    def __call__(self, request: Request):
        return Response(
            mako.get_template('index.html.mako') \
                .render(name='World')
        )


app = App(First())

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

And in `templates/index.html.mako`:

```
Hello, ${name}!
```

## 404 handling

To create a custom 404 page, pass a custom function to the `handle_404` property of the `App` object:

```python
from varmkorv import Controller, App
from werkzeug import Request, Response

class First(Controller):
    def __call__(self, request: Request):
        return Response("Hello, first!")

app = App(First())

def handle_404(request: Request, ex: Exception) -> Response:
    print("Could not be found because:", str(ex))
    return Response(
        request.url + " cannot be found.",
        status=404
    )

app.handle_404 = handle_404

from werkzeug.serving import run_simple
run_simple("localhost", 8080, app, use_reloader=True)
```

The exception passed is the reason why the page could not be found. It might be that there's no route for the URI, or maybe because a URL parameter was passed as a string when only an integer is accepted.

## WSGI

Varmkorv is a WSGI application framework. You can for example run it using Meinheld:

```python
from varmkorv import Controller, App
from werkzeug import Request, Response

class First(Controller):
    def __call__(self, request: Request):
        return Response('Hello, world!')

app = App(First())

from meinheld import server
server.listen(('0.0.0.0', 8080))
server.set_access_logger(None)
server.run(app)
```

Varmkorv will run under any WSGI server. The `run_simple` server that ships with Werkzeug is only meant to be used during development. When running on production you would need something more robust and with higher performance.

## Things that are missing

As I said earlier, it feels like the LoginManager could get more secure.

There's no configuration layer. I quite like Viper for Go. Not sure a built-in configuration layer is really needed though.

There are missing doc strings.

There are no unit tests.

PyPI structure and publish.
