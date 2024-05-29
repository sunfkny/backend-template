class ValueErrorWithCode(ValueError):
    code: int = -1

    def __str__(self) -> str:
        s = super().__str__()
        if not s:
            s = f"Error: {self.code}"
        return s
