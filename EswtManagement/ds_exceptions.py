

class BaseInvalidIdError(IndexError):
    pass


class NonExistenttreatments.dError(BaseInvalidIdError):
    pass


class NonExistentSkuIdError(BaseInvalidIdError):
    pass


class Inactivetreatments.dError(BaseInvalidIdError):
    pass


class InactiveSkuIdError(BaseInvalidIdError):
    pass


class BaseValueError(ValueError):
    pass


class InvalidTrTypeError(BaseValueError):
    pass
