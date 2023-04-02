class BaseClientError(Exception):
    
    def __init__(self, message, code):
        self.message = message
        self.code = code


class BadRequestError(BaseClientError):

    def __init__(self, message='Invalid Request', code='ER_INVALID_REQUEST'):
        super(BadRequestError, self).__init__(message, code)
        self.status_code = 400


class NotFoundError(BaseClientError):

    def __init__(self, message='Not found', code='ER_NOT_FOUND'):
        super(NotFoundError, self).__init__(message, code)
        self.status_code = 404


class PermissionDeniedError(BaseClientError):

    def __init__(self, message='Permission Denied', code='ER_PERMISSION_DENIED'):
        super(PermissionDeniedError, self).__init__(message, code)
        self.status_code = 403
