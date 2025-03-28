class NullInput(Exception):
    def __init__(self, message: str = "INPUT is EMPTY"):
        super().__init__(message)
