from typing import Union, Optional
from datetime import timedelta, datetime
from abc import ABC, abstractmethod
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

    def logout_user(self):
        self.session["user_id"] = None
        del self.user


class CookieLoginMiddleware:
    def __init__(
        self,
        secret_key,
        load_user,
        cookie_name="session",
        max_age: Union[timedelta, int, None] = None,
        expires: Union[str, datetime, int, float, None] = None,
        path: Optional[str] = "/",
        domain: Optional[str] = None,
        samesate: Optional[str] = None,
        httponly=True,
    ):
        self.secret_key = secret_key
        self.load_user = load_user
        self.cookie_name = cookie_name
        self.max_age = max_age
        self.expires = expires
        self.path = path
        self.domain = domain
        self.httponly = httponly
        self.samesite = samesate

    def __call__(self, next):
        def handle(request, *args, **kwargs):
            setattr(request, "login", CookieLoginInstance(request, self))
            response = next(request, *args, **kwargs)
            if getattr(request, "login").session.should_save:
                session_data = getattr(request, "login").session.serialize()
                response.set_cookie(
                    self.cookie_name,
                    session_data,
                    max_age=self.max_age,
                    expires=self.expires,
                    path=self.path,
                    domain=self.domain,
                    httponly=self.httponly,
                    samesite=self.samesite,
                )
            return response

        return handle


class AdvancedCookieLoginInstance:
    def __init__(self, request: Request, login: "AdvancedCookieLoginMiddleware"):
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
            token = self.session["token"]
        except KeyError:
            return None
        if not user_id or not token:
            return None
        return self._login.store.get(user_id, token, self._request)

    def login_user(self, user):
        token = self._login.store.new(user, self._request)
        self.session["user_id"] = user.get_id()
        self.session["token"] = token
        del self.user

    def logout_user(self):
        user = self.user
        token = self.session.get("token")
        self.session["user_id"] = None
        self.session["token"] = None
        del self.user
        if not user or not token:
            return None
        self._login.store.remove(user, token, self._request)


class AdvancedCookieLoginMiddlewareAbstractStore(ABC):
    @abstractmethod
    def new(self, user, request) -> str:
        pass

    @abstractmethod
    def get(self, user_id, token, request):
        pass

    @abstractmethod
    def remove(self, user, token, request) -> None:
        pass


class AdvancedCookieLoginMiddleware:
    def __init__(
        self,
        secret_key,
        store: AdvancedCookieLoginMiddlewareAbstractStore,
        cookie_name="session",
        max_age: Union[timedelta, int, None] = None,
        expires: Union[str, datetime, int, float, None] = None,
        path: Optional[str] = "/",
        domain: Optional[str] = None,
        samesate: Optional[str] = None,
        httponly=True,
    ):
        self.secret_key = secret_key
        self.store = store
        self.cookie_name = cookie_name
        self.max_age = max_age
        self.expires = expires
        self.path = path
        self.domain = domain
        self.httponly = httponly
        self.samesite = samesate

    def __call__(self, next):
        def handle(request, *args, **kwargs):
            setattr(request, "login", AdvancedCookieLoginInstance(request, self))
            response = next(request, *args, **kwargs)
            if getattr(request, "login").session.should_save:
                session_data = getattr(request, "login").session.serialize()
                response.set_cookie(
                    self.cookie_name,
                    session_data,
                    max_age=self.max_age,
                    expires=self.expires,
                    path=self.path,
                    domain=self.domain,
                    httponly=self.httponly,
                    samesite=self.samesite,
                )
            return response

        return handle