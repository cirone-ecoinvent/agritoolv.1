from enum import Enum

class HeavyMetalType(Enum):
        cd=0
        cu=1
        zn=2
        pb=3
        ni=4
        cr=5
        hg=6
        
class SoilTexture(Enum):
        unknown=0,
        coarse=1,
        medium=2,
        medium_fine=3
        fine=4
        very_fine=5
        