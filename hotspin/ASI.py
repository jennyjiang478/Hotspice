import math

import cupy as cp

from .core import Magnets


class OOP_ASI(Magnets):
    ''' Generic abstract class for out-of-plane ASI. '''
    # Example of __init__ method for out-of-plane ASI:
    # def __init__(self, n: int, a: float, *, nx: int = None, ny: int = None, **kwargs):
    #     self.a = a # [m] Some sort of lattice constant representative for the ASI
    #     self.nx, self.ny = nx or n, ny or n # Use nx/ny if they are passed as an argument, otherwise use n
    #     self.dx, self.dy = kwargs.pop('dx', a), kwargs.pop('dy', a)
    #     super().__init__(self.nx, self.ny, self.dx, self.dy, in_plane=False, **kwargs)

    def _get_angles(self):
        # This abstract method is irrelevant for OOP ASI, so just return NaNs.
        return cp.nan*cp.zeros_like(self.ixx)


class IP_ASI(Magnets):
    ''' Generic abstract class for in-plane ASI. '''
    # Example of __init__ method for in-plane ASI:
    # def __init__(self, n: int, a: float, *, nx: int = None, ny: int = None, **kwargs):
    #     self.a = a # [m] Some sort of lattice constant representative for the ASI
    #     self.nx, self.ny = nx or n, ny or n # Use nx/ny if they are passed as an argument, otherwise use n
    #     self.dx, self.dy = kwargs.pop('dx', a), kwargs.pop('dy', a)
    #     super().__init__(self.nx, self.ny, self.dx, self.dy, in_plane=True, **kwargs)


class OOP_Square(OOP_ASI):
    def __init__(self, n: int, a: float, *, nx: int = None, ny: int = None, **kwargs):
        ''' Out-of-plane ASI in a square arrangement. '''
        self.a = a # [m] The distance between two nearest neighboring spins
        self.nx, self.ny = nx or n, ny or n
        self.dx, self.dy = kwargs.pop('dx', a), kwargs.pop('dy', a)
        super().__init__(self.nx, self.ny, self.dx, self.dy, in_plane=False, **kwargs)

    def _set_m(self, pattern: str):
        match str(pattern).strip().lower():
            case 'afm':
                self.m = ((self.ixx - self.iyy) % 2)*2 - 1
            case str(unknown_pattern):
                super()._set_m(pattern=unknown_pattern)

    def _get_occupation(self):
        return cp.ones_like(self.xx)

    def _get_appropriate_avg(self):
        return 'point'

    def _get_AFMmask(self):
        return cp.array([[0, -1], [-1, 2]], dtype='float')/4 # Possible situations: ▚/▞ -> 1, ▀▀/▄▄/█ / █ -> 0.5, ██ -> 0 

    def _get_nearest_neighbors(self):
        return cp.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])

    def _get_groundstate(self):
        return 'afm'


class IP_Ising(IP_ASI):
    def __init__(self, n: int, a: float, *, nx: int = None, ny: int = None, **kwargs):
        ''' In-plane ASI with all spins on a square grid, all pointing in the same direction. '''
        self.a = a # [m] The distance between two nearest neighboring spins
        self.nx, self.ny = nx or n, ny or n
        self.dx, self.dy = kwargs.pop('dx', a), kwargs.pop('dy', a)
        super().__init__(self.nx, self.ny, self.dx, self.dy, in_plane=True, **kwargs)

    def _set_m(self, pattern: str):
        match str(pattern).strip().lower():
            case 'afm':
                self.m = (self.iyy % 2)*2 - 1
            case str(unknown_pattern):
                super()._set_m(pattern=unknown_pattern)

    def _get_angles(self):
        return cp.zeros_like(self.xx)

    def _get_occupation(self):
        return cp.ones_like(self.xx)

    def _get_appropriate_avg(self):
        return 'point'

    def _get_AFMmask(self):
        return cp.array([[1, 1], [-1, -1]])/4

    def _get_nearest_neighbors(self):
        return cp.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])

    def _get_groundstate(self):
        return 'uniform'


class IP_Square(IP_ASI):
    def __init__(self, n: int, a: float, *, nx: int = None, ny: int = None, **kwargs):
        ''' In-plane ASI with the spins placed on, and oriented along, the edges of squares. '''
        self.a = a # [m] The side length of the squares (i.e. side length of a unit cell)
        self.nx, self.ny = nx or n, ny or n
        self.dx, self.dy = kwargs.pop('dx', a/2), kwargs.pop('dy', a/2)
        super().__init__(self.nx, self.ny, self.dx, self.dy, in_plane=True, **kwargs)

    def _set_m(self, pattern: str):
        match str(pattern).strip().lower():
            case 'afm':
                self.m = ((self.ixx - self.iyy)//2 % 2)*2 - 1
            case str(unknown_pattern):
                super()._set_m(pattern=unknown_pattern)

    def _get_angles(self):
        angles = cp.zeros_like(self.xx)
        angles[self.iyy % 2 == 1] = math.pi/2
        return angles

    def _get_occupation(self):
        return (self.ixx + self.iyy) % 2 == 1

    def _get_appropriate_avg(self):
        return 'cross'

    def _get_AFMmask(self):
        return cp.array([[1, 0, -1], [0, 0, 0], [-1, 0, 1]], dtype='float')/4

    def _get_nearest_neighbors(self):
        return cp.array([[1, 0, 1], [0, 0, 0], [1, 0, 1]])

    def _get_groundstate(self):
        return 'afm'


class IP_Pinwheel(IP_Square):
    def __init__(self, n: int, a: float, *, nx: int = None, ny: int = None, **kwargs):
        ''' In-plane ASI similar to IP_Square, but all spins rotated by 45°, hence forming a pinwheel geometry. '''
        kwargs['angle'] = kwargs.get('angle', 0) - math.pi/4
        super().__init__(n, a, nx=nx, ny=ny, **kwargs)

    def _get_groundstate(self):
        return 'uniform' if self.PBC else 'vortex'


class IP_Kagome(IP_ASI):
    def __init__(self, n: int, a: float, *, nx: int = None, ny: int = None, **kwargs):
        ''' In-plane ASI with all spins placed on, and oriented along, the edges of hexagons. '''
        self.a = a # [m] The distance between opposing sides of a hexagon
        self.nx = nx or n
        if ny is None:
            self.ny = int(self.nx/math.sqrt(3))//4*4 # Try to make the domain reasonably square-shaped
            if not kwargs.get('PBC', False): self.ny -= 1 # Remove dangling spins if no PBC
        else:
            self.ny = ny
        self.dx = kwargs.pop('dx', a/4)
        self.dy = kwargs.pop('dy', math.sqrt(3)*self.dx)
        super().__init__(self.nx, self.ny, self.dx, self.dy, in_plane=True, **kwargs)

    def _set_m(self, pattern: str, angle=None):
        match str(pattern).strip().lower():
            case 'afm':
                self.m = cp.ones_like(self.ixx)
                self.m[(self.ixx + self.iyy) % 4 == 3] *= -1
            case str(unknown_pattern):
                super()._set_m(pattern=unknown_pattern)

    def _get_angles(self):
        angles = cp.ones_like(self.xx)*math.pi/2
        angles[((self.ixx - self.iyy) % 4 == 1) & (self.ixx % 2 == 1)] = -math.pi/6
        angles[((self.ixx + self.iyy) % 4 == 3) & (self.ixx % 2 == 1)] = math.pi/6
        return angles

    def _get_occupation(self):
        occupation = cp.zeros_like(self.xx)
        occupation[(self.ixx + self.iyy) % 4 == 1] = 1 # One bunch of diagonals \
        occupation[(self.ixx - self.iyy) % 4 == 3] = 1 # Other bunch of diagonals /
        return occupation

    def _get_appropriate_avg(self):
        return 'hexagon'

    def _get_AFMmask(self):
        return cp.array([[1, 0, -1], [0, 0, 0], [-1, 0, 1]], dtype='float')/4

    def _get_nearest_neighbors(self):
        return cp.array([[0, 1, 0, 1, 0], [1, 0, 0, 0, 1], [0, 1, 0, 1, 0]])

    def _get_groundstate(self):
        return 'uniform'


class IP_Triangle(IP_Kagome):
    def __init__(self, n: int, a: float, *, nx: int = None, ny: int = None, **kwargs):
        ''' In-plane ASI with all spins placed on, and oriented along, the edges of triangles. '''
        kwargs['angle'] = kwargs.get('angle', 0) - math.pi/2
        super().__init__(n, a, nx=nx, ny=ny, **kwargs)

    def _get_appropriate_avg(self):
        return 'triangle'

    def _get_groundstate(self):
        return 'afm'
