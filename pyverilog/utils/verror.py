class PyvError(Exception):
    pass


class ImplementationError(PyvError):
    pass


class FormatError(PyvError):
    pass


class DefinitionError(PyvError):
    pass
