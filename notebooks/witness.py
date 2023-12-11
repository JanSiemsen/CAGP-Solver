from pyvispoly import Point

class Witness:

    def __init__(self, id: str, position: Point) -> None:
        self._id = id
        self._position = position

    @property
    def id(self):
        return self._id
    
    @property
    def position(self):
        return self._position
    