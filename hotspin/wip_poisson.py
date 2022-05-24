import math

import numpy as np

from scipy.spatial.distance import pdist
from typing import Callable




class SequentialPoissonDiskSampling:
    neighbourhood = [
        [0, 0],   [0, -1],  [-1, 0],
        [1, 0],   [0, 1],   [-1, -1],
        [1, -1],  [-1, 1],  [1, 1],
        [0, -2],  [-2, 0],  [2, 0],
        [0, 2],   [-1, -2], [1, -2],
        [-2, -1], [2, -1],  [-2, 1],
        [2, 1],   [-1, 2],  [1, 2]
    ]
    neighbourhoodLength = len(neighbourhood)

    def __init__(self, width: int, height: int, radius: float, tries: int = 30, rng: Callable = None):
        ''' Class to implement poisson disk sampling. Code inspired by the Javascript version from
            https://github.com/kchapelier/fast-2d-poisson-disk-sampling/blob/master/src/fast-poisson-disk-sampling.js,
            adapted to our own requirements (e.g. integer positions, PBC)
            @param width, height [int]: shape of the space
            @param radius [float]: minimum distance between separate points
            @param tries [int] (30): number of times the algorithm will try to place a point in the neighbourhood of other points
            @param rng [function] (np.random.random): RNG function between 0 to 1
        '''
        epsilon = 2e-14

        self.width = width
        self.height = height
        self.radius = radius
        self.maxTries = max(3, math.ceil(tries))
        self.rng = np.random.random if rng is None else rng

        self.squaredRadius = self.radius*self.radius
        self.radiusPlusEpsilon = self.radius + epsilon
        self.cellSize = self.radius/math.sqrt(2)

        self.angleIncrement = math.pi*2/self.maxTries
        self.angleIncrementOnSuccess = np.pi/3 + epsilon
        self.triesIncrementOnSuccess = math.ceil(self.angleIncrementOnSuccess/self.angleIncrement)

        self.processList = []
        self.samplePoints = []

        # cache grid
        self.gridShape = [math.ceil(self.width/self.cellSize), math.ceil(self.height/self.cellSize)]
        self.grid = np.zeros(self.gridShape, dtype=int) # will store references to samplePoints

    def addRandomPoint(self):
        ''' Add a totally random point in the grid
            @return [list(2)]: the point added to the grid
        '''
        return self.directAddPoint([
            int(self.rng()*self.width),
            int(self.rng()*self.height),
            self.rng()*math.pi*2,
            0
        ])

    def addPoint(self, point):
        ''' Add a given point to the grid
            @param point [list(2)]: point as [x, y]
            @return [list(4)|None]: (if valid) the point added to the grid represented as [x, y, angle, tries]
        '''
        valid = (len(point) == 2)
        
        return self.directAddPoint([
            point[0] % self.width,
            point[1] % self.height,
            self.rng()*math.pi*2,
            0
        ]) if valid else None

    def directAddPoint(self, point):
        ''' Add a given point to the grid, without any check
            @param point [list(4)]: point represented as [x, y, angle, tries]
            @return [list(2)]: the point added to the grid as [x, y]
        '''
        coordsOnly = [point[0], point[1]]
        self.processList.append(point)
        self.samplePoints.append(coordsOnly)

        self.grid[int(point[0]/self.cellSize), int(point[1]/self.cellSize)] = len(self.samplePoints) # store the point reference
        return coordsOnly

    def inNeighbourhood(self, point):
        ''' Check whether a given point is in the neighbourhood of existing points
            @param point [list(4)]: point represented as [x, y, angle, tries]
            @return [bool]: whether the point is in the neighbourhood of another point
        '''
        pointpos = [int(point[0]/self.cellSize) | 0, int(point[1]/self.cellSize) | 0]
        for neighbourIndex in range(self.neighbourhoodLength):
            gridIndex = [0, 0]
            for dimension in range(2):
                currentDimensionValue = pointpos[dimension] + self.neighbourhood[neighbourIndex][dimension]
                gridIndex[dimension] = currentDimensionValue % self.gridShape[dimension]
            gridIndex = tuple(gridIndex)

            if self.grid[gridIndex] != 0: # i.e. it is occupied
                positions = np.asarray([[point[0], point[1]], self.samplePoints[self.grid[gridIndex] - 1]]) # point, and already existing point
                # Determine with PBC (in 2D) if these two are too close or not: (adapted from https://yangyushi.github.io/science/2020/11/02/pbc_py.html)
                box = [self.width, self.height]
                dist_nd_sq = 0  # to match the result of pdist
                for dim in range(2):
                    dist_1d = pdist(positions[:, dim][:, np.newaxis])
                    dist_1d[dist_1d > box[dim]*0.5] -= box[dim]
                    dist_nd_sq += dist_1d**2 # d^2 = dx^2 + dy^2

                if dist_nd_sq < self.squaredRadius:
                    return True
        return False

    def next(self):
        ''' Try to generate a new point in the grid.
            @return [list(2)|None]: the added point [x, y] or None
        '''
        while len(self.processList) > 0:
            index = int(len(self.processList)*self.rng()) | 0

            currentPoint = self.processList[index]
            currentAngle = currentPoint[2]
            tries = currentPoint[3]

            if tries == 0: currentAngle += (self.rng() - .5)*np.pi/3*4

            for tries in range(tries, self.maxTries):
                newPoint = [
                    int(currentPoint[0] + math.cos(currentAngle)*self.radiusPlusEpsilon*(1 + self.rng())) % self.width,
                    int(currentPoint[1] + math.sin(currentAngle)*self.radiusPlusEpsilon*(1 + self.rng())) % self.height,
                    currentAngle,
                    0
                ]

                if not self.inNeighbourhood(newPoint):
                    currentPoint[2] = currentAngle + self.angleIncrementOnSuccess + self.rng()*self.angleIncrement
                    currentPoint[3] = tries + self.triesIncrementOnSuccess
                    return self.directAddPoint(newPoint)
                
                currentAngle = currentAngle + self.angleIncrement

            if tries >= self.maxTries - 1:
                r = self.processList.pop()
                if index < len(self.processList): self.processList[index] = r
        
        return None

    def fill(self):
        ''' Automatically fill the grid, adding a random point to start the process if needed.
            @return [list(N,2)]: N sample points
        '''
        if len(self.samplePoints) == 0: self.addRandomPoint()
        while self.next(): pass
        return self.samplePoints

    def getAllPoints(self):
        ''' Get all the points in the grid.
            @return [list(N,2)]: all N sample points
        '''
        return self.samplePoints

    def reset(self):
        ''' Reinitialize the grid as well as the internal state. '''
        self.grid = np.zeros_like(self.grid)
        self.samplePoints = []
        self.processList = []

if __name__ == "__main__":
    p = SequentialPoissonDiskSampling(1000, 1000, 16, tries=3) # 3 (or 2) tries is optimal in terms of points/second
    points = np.asarray(p.fill())
    print(len(points))

    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')
    for x, y in points:
        ax.add_artist(Circle(xy=(x, y), radius=p.radius/2))
    ax.set_xlim([0, p.width])
    ax.set_ylim([0, p.height])
    plt.show()