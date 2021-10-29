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