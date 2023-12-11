from pyvispoly import Point, PolygonWithHoles

class Guard:

    def __init__(self, id: str, position: Point, visibility: PolygonWithHoles) -> None:
        self._id = id
        self._position = position
        self._visibility = visibility

    @property
    def id(self):
        return self._id
    
    @property
    def position(self):
        return self._position
    
    @property
    def visibility(self):
        return self._visibility