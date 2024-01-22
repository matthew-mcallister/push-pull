class ErrorBase(Exception):
    status_code: int = 500

class NoSuchResource(ErrorBase):
    status_code = 404
