class ValueErrorWithCode(ValueError):
    def __init__(self, message: str, code: int):
        self.code = code
        self.message = message
        super().__init__(message)
