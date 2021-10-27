# Varmkorv

Varmkorv is a CherryPy inspired micro framework using Werkzeug.

This is just a proof of concept. You are free to use it if you like, or find inspiration from it, or copy bits and pieces of it.

You might wonder if the world really need another Python web framework, and the answer is probably: no. I created this framework out of curiosity. The routes are "complied" (and recompiled if changed during runtime), and it does not contain much fluff at all. That makes this framework really speedy - way speedier than CherryPy (and Flask too for that matter).

I have implemented support for Authentication and Peewee. That is what I need for my personal projects, and might not suit all.


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

Point your browser to `http://localhost:8080/` and feel welcomed.


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
        return Response('You got to eat')

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

    def food(self, request: Request, food: Food):
        return Response(food.value + ' sounds good')

app = App(First())

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

* `http://localhost:8080/food/kebab` - Says "kebab sounds good"
* `http://localhost:8080/food/human` - Gives 404


## Peewee

```python
from varmkorv import Controller, App, PeeweeWrapper
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

app.wrap(PeeweeWrapper(db))

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```


## LoginManager

```python
from varmkorv import Controller, App, PeeweeWrapper, LoginManager
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
app.wrap(PeeweeWrapper(db))

def load_user(user_id):
    return User.get_or_none(User.id == user_id)

login = LoginManager('secret', load_user)
app.wrap(app)
```

I am using Peewee in this example, but you are free to use whatever you like.

Feels like more work needs to be done on the LoginManager to make it more secure.

## Wrappers / middlewares

Peewee and LoginManager use Varmkorv's wrapping functionality. 

Let's create our own wrapper:

```python
from varmkorv import Controller, App
from werkzeug import Request, Response

class First(Controller):
    def __call__(self, request: Request):
        print('Hello, world!')
        return Response('Hello, world!')

app = App(First())

def my_wrapper(next):
    def handle(request: Request, *args, **kwargs):
        print('This is me, doing things on the request!')
        response = next(request, *args, **kwargs)
        print('And here I am again, doing things on the response!')
        return response
    return handle

app.wrap(my_wrapper)

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

If you point your browser to `http://localhost:8080/` and go back to the terminal where you are running the application server, you will see the following:

```
This is me, doing things on the request!
Hello, world!
And here I am again, doing things on the response!
```

### The order of the wrappers

Now we are going to add two wrappers to our application and see what happens:

```python
from varmkorv import Controller, App
from werkzeug import Request, Response

class First(Controller):
    def __call__(self, request: Request):
        print('Hello, world!')
        return Response('Hello, world!')

app = App(First())

def my_first_wrapper(next):
    def handle(request: Request, *args, **kwargs):
        print('Request: first wrapper')
        response = next(request, *args, **kwargs)
        print('Response: first wrapper')
        return response
    return handle

def my_second_wrapper(next):
    def handle(request: Request, *args, **kwargs):
        print('Request: second wrapper')
        response = next(request, *args, **kwargs)
        print('Response: second wrapper')
        return response
    return handle

app.wrap(my_first_wrapper)
app.wrap(my_second_wrapper)

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

And again, refresh your browser and go back to the terminal. You will see this:

```
Request: first wrapper
Request: second wrapper
Hello, world!
Response: second wrapper
Response: first wrapper
```

This is quite important: _The wrapper you add first is the one being included first_. We added `my_first_wrapper` first, and `Request: first wrapper` is what we see first in the terminal.

### Wrappers on controllers

The examples are starting to get a bit lenghty, but here we go:

```python
from varmkorv import Controller, App
from werkzeug import Request, Response

def my_app_wrapper(next):
    def handle(request: Request, *args, **kwargs):
        print('Request: app wrapper')
        response = next(request, *args, **kwargs)
        print('Response: app wrapper')
        return response
    return handle

def my_food_controller_wrapper(next):
    def handle(request: Request, *args, **kwargs):
        print('Request: food controller wrapper')
        response = next(request, *args, **kwargs)
        print('Response: food controller wrapper')
        return response
    return handle

class Food(Controller):
    def __init__(self):
        Controller.__init__(self)
        self.wrap(my_food_controller_wrapper)  # Wrapping on controller level

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

app.wrap(my_app_wrapper) # Wrapping on app level

from werkzeug.serving import run_simple
run_simple('localhost', 8080, app, use_reloader=True)
```

I feel like I need to excuse myself for this long example. Just to be clear. in this example we have:

* The `my_app_wrapper` being attached to the application.
* The `Food` controller being attached as a sub-controller to `First`
* The `my_food_controller_wrapper` being attached to the `Food` controller.

If we point the browser to `http://localhost:8080/` we will see the following in the terminal:

```
Request: app wrapper
Hello, first!
Response: app wrapper
```

And if we point the point the browser to `http://localhost:8080/food` we will see the following in the terminal:

```
Request: app wrapper
Request: food controller wrapper
Hello, food!
Response: food controller wrapper
Response: app wrapper
```

There are two things worth noticing here:

* The wrappers of the `Food` controller are only going to be included if the `Food` controller is used.
* The wrappers of the parents has higher priority than the sub-controller. In other words: each sub-controller's wrappers are included _after_ the wrappers its parents' wrappers. 

All the parent controller's wrappers are going to be included. That means that you can for example have an "admin" controller where you limit who has access, and that will be reflected on all of its sub-controllers.

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
server.listen(("127.0.0.1", 8080))
server.set_access_logger(None)
server.run(app)
```

Varmkorv will run under any WSGI server. The `run_simple` server that ships with Werkzeug is only meant to be used during development. When running on production you would need something more robust and with higher performance.

## Things that are missing

As I said earlier, it feels like the LoginManager could get more secure.

There's no built in template engine, and I think it should stay like that. Maybe a wrapper for Jinja2 would be nice, though that probably works splendid stand alone (without a wrapper)

There's no configuration layer. I quite like Viper for Go. Not sure a built-in configuration layer is really needed though.

Better 404 handling. I think 404 exceptions should be raised instead. The developer can pass a 404 handler method to the application, and the exception and the current request can be passed to that method on 404. Of course a simple default 404 method needs to exist.

There's no proper file structure to the project. Needs to be added if this project is supposed to get used. There are also things like missing doc strings.

There are no unit tests.
