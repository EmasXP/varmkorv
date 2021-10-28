from werkzeug.wrappers import Request
from werkzeug.utils import cached_property
from secure_cookie.cookie import SecureCookie


class CookieLoginInstance:
    def __init__(self, request: Request, login: "CookieLoginMiddleware"):
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


class CookieLoginMiddleware:
    def __init__(self, secret_key, load_user, cookie_name="session", httponly=True):
        self.secret_key = secret_key
        self.load_user = load_user
        self.cookie_name = cookie_name
        self.httponly = httponly

    def __call__(self, next):
        def handle(request, *args, **kwargs):
            setattr(request, "login", CookieLoginInstance(request, self))
            response = next(request, *args, **kwargs)
            if getattr(request, "login").session.should_save:
                session_data = getattr(request, "login").session.serialize()
                response.set_cookie(
                    self.cookie_name, session_data, httponly=self.httponly
                )
            return response

        return handle


class PeeweeMiddleware:
    def __init__(self, db):
        self.db = db

    def __call__(self, next):
        def handle(request, *args, **kwargs):
            self.db.connect(reuse_if_open=True)
            response = next(request, *args, **kwargs)

            def close_db():
                if not self.db.is_closed():
                    self.db.close()

            response.call_on_close(close_db)
            return response

        return handle