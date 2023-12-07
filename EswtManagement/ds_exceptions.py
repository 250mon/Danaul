

class BaseInvalidIdError(IndexError):
    pass


class NonExistentItemIdError(BaseInvalidIdError):
    pass


class NonExistentPatientIdError(BaseInvalidIdError):
    pass


class InactiveItemIdError(BaseInvalidIdError):
    pass


class BaseValueError(ValueError):
    pass


class InvalidPasswordError(BaseValueError):
    pass


class DuplicatePatientEmrId(BaseValueError):
    pass
