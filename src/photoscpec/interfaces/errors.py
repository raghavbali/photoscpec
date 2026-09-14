from dataclasses import dataclass, field


@dataclass
class PhotoScpecError(Exception):
    code: str
    message: str
    details: dict = field(default_factory=dict)

    def __str__(self):
        return self.message
