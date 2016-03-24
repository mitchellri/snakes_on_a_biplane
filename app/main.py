import bottle
import os

import json
import heapq
import random
import copy


# we lost because there was a wall between the outer edge and a snake smaller
# than us managed to block us in.  This was possible because we didn't obstruct
# the heads of snakes smaller than us.  This allows us to eat smaller snakes, 
# but we got trapped in a corner without realizing what could happen

################################################################################
# Taunts                                                                       #
################################################################################

tList = ['Feel the power of the mongoose!',
		 'Look at my BICEPS!!',
		 'my E-peen is growing',
		 'You wanna go bruh? Wanna go? HUH?',
		 'Staying alive! Staying alive!',
		 'Pretty good eh?',
		 'Do you fear death?',
		 'Let of some ssssssteam...',
		 'PURGEEEEEEEE',
		 'Come on, kill meeee!',
		 'You require more pylons!',
		 'Fear the power of the force...']

lenTList = len(tList)-1

################################################################################
# Constants                                                                    #
################################################################################
snakeid = 'd1ed0f87-8a13-445f-a9ed-b7064f7858e0'
directions = {
    (-1, 0): 'west',
    (1, 0): 'east',
    (0, -1): 'north',
    (0, 1): 'south'
}
trapSamples = 20
idlePathSamples = 20

################################################################################
# Classes                                                                      #
################################################################################

##
# Basic priority queue, minimum value at top
#
class PriorityQueue:
    def __init__(self):
        self.elements = []
    
    def empty(self):
        return len(self.elements) == 0
    
    def enqueue(self, element, priority):
        heapq.heappush(self.elements, (priority, element))
    
    def dequeue(self):
        return heapq.heappop(self.elements)[1]

##
# Used for converting backwards path returned by A* to forwards, also finding
# direction to move
#

def pathCameFrom(cameFrom, goal):
    goTo = { goal: None }
    start = goal
    while cameFrom[start]:
        goTo[cameFrom[start]] = start
        start = cameFrom[start]
    return Path(goTo, start)

class Path:
    def __init__(self, goTo, start):
        self.goTo = goTo
        self.start = start

    def direction(self):
        nxt = self.goTo[self.start]
        return (nxt[0] - self.start[0], nxt[1] - self.start[1])

##
# Grid to use for pathfinding, has obstructions to be navigated around
#
class Grid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cells = [ [ 0 for y in range(height) ] for x in range(width) ]
    
    # Finds a random, unobstructed cell on the grid
    def random(self):
        cell = None
        while cell == None or self.obstructed(cell):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            cell = (x, y)
        return cell

    # Checks if the grid contains a cell
    def contains(self, cell):
        return (cell[0] >= 0
            and cell[1] >= 0
            and cell[0] < self.width
            and cell[1] < self.height)

    # Obstructs a cell on the grid
    def obstruct(self, cell):
        if self.contains(cell):
            self.cells[cell[0]][cell[1]] = 1
        
    # Checks if a cell on the grid is obstructed
    def obstructed(self, cell):
        return self.cells[cell[0]][cell[1]] == 1

    # Heuristic for pathfinding, not currently used for anything
    # most likely use it to represent risk
    def heuristic(self, cell):
        return self.cells[cell[0]][cell[1]]

    # Finds neighbours to a cell on the grid
    def neighbours(self, cell):
        neighbours = []
        for direction in directions:
            neighbour = (cell[0] + direction[0], cell[1] + direction[1])
            
            # Check if on grid, and not obstructed
            if self.contains(neighbour) and not self.obstructed(neighbour):
                neighbours.append(neighbour)
        
        return neighbours

################################################################################
# Functions                                                                    #
################################################################################

# xDist + yDist
def manDist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# A* search, uses grid's heuristic
def aStar(grid, start, goal):
    frontier = PriorityQueue()
    frontier.enqueue(start, 0)
    cameFrom = { start: None }
    costSoFar = { start: 0 }

    while not frontier.empty():
        current = frontier.dequeue()
        if current == goal:
            return pathCameFrom(cameFrom, goal)

        for neighbour in grid.neighbours(current):
            cost = costSoFar[current] + grid.heuristic(neighbour)

            if neighbour not in costSoFar or cost < costSoFar[neighbour]:
                costSoFar[neighbour] = cost
                priority = cost + manDist(neighbour, goal)
                frontier.enqueue(neighbour, priority)
                cameFrom[neighbour] = current
    return False

def isPositionBetter(grid, snake, current, pathTo, to):
    # Passes
    currentPasses = 0
    toPasses = 0
    
    # New grid
    toGrid = copy.deepcopy(grid)
    
    # Loop over path and count
    curr = current
    count = 0
    while pathTo.goTo[curr]:		#
        curr = pathTo.goTo[curr]
        count += 1

    x = len(snake['coords']) - count
    while x > 0:
        toGrid.obstruct(snake['coords'][x - 1])
        x -= 1

    if len(snake['coords']) >= count:
        curr = current
        curr = pathTo.goTo[curr]
        while curr:
            toGrid.obstruct(curr)
            curr = pathTo.goTo[curr]
    else:
        curr = current
        curr = pathTo.goTo[curr]
        index = 0
        while curr:
            if index >= count - len(snake['coords']):
                toGrid.obstruct(curr)
            curr = pathTo.goTo[curr]
            index += 1
        
    for _ in range(trapSamples):
        goal = grid.random()
        if aStar(grid, current, goal):
            currentPasses += 1
        if aStar(toGrid, to, goal):
            toPasses += 1
    return toPasses < currentPasses


################################################################################
# Server                                                                       #
################################################################################
#===== INIT STATIC ============================
@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, root='static/')
#===== INIT ===================================
@bottle.get('/')
def index():
    head_url = '%s://%s/static/mongoose.png' % (
        bottle.request.urlparts.scheme,
        bottle.request.urlparts.netloc
    )
    return {
        'color': '#4B1000',
        'head': head_url
    }
#===== START DATA ===================================
@bottle.post('/start')
def start():
    data = bottle.request.json

    # TODO: Do things with data: (BELOW)
    # {
    #     "game": "hairy-cheese",
    #     "mode": "advanced",
    #     "turn": 0,
    #     "height": 20,
    #     "width": 30,
    #     "snakes": [
    #         <Snake Object>, <Snake Object>, ...
    #     ],
    #     "food": [],
    #     "walls": [],  // Advanced Only
    #     "gold": []    // Advanced Only
    # }
    
    return {
        'taunt': 'GET OFF MY PLANE!!'
    }

#===== MAKE MOVE ===================================
@bottle.post('/move')
def move():
    data = bottle.request.json
    mode = data['mode']
    move = None
    ourSnake = None
    
    # GET OUR SNAKE
    for snake in data['snakes']:
        if snake['id'] == snakeid:
            ourSnake = snake
            break
            
    #ESTABLISH OUTER GRID
    grid = Grid(data['width'], data['height'])
    
    #Get info on other snakes
    for snake in data['snakes']:
        #obstruct all snakes
        for coord in snake['coords']:
            grid.obstruct(tuple(coord))
        #obstruct all snake movement locations if bigger or equal than us
        if snake['id'] != snakeid:
            for direction in directions:
                if len(snake['coords']) >= len(ourSnake['coords']):
                    head = snake['coords'][0]
                    movement = (head[0] + direction[0], head[1] + direction[1])
                    grid.obstruct(movement)
    
    #ADVANCED: AVOID WALLS
    if mode == 'advanced':
        for wall in data['walls']:
            grid.obstruct(tuple(wall))
        
    
    idle = False
    #============= COINS ==============
    getcoin = False
    #GET COIN possible without dying
    if mode == 'advanced':
        # print "CHECKING FOR COINS"
        possibleCoins = []
        for coin in data['gold']:
            dist = manDist(tuple(ourSnake['coords'][0]), tuple(coin))  #snake not defined?
            skip = False
            #avoid snakes closer to the coin!
            for snake in data['snakes']:
                if snake['id'] != snakeid and manDist(tuple(snake['coords'][0]), tuple(coin)) <= dist:
                    skip = True
                    break
            if not skip:
                possibleCoins.append(tuple(coin))
                    
        #Go to closest COIN
        closestCoinDist = 0
        closestCoin = None
        for coin in possibleCoins:
            d = manDist(tuple(ourSnake['coords'][0]), coin)
            if d < closestCoinDist or closestCoin == None:
                closestCoin = coin
                closestCoinDist = d
        getcoin = False
        
        if closestCoin != None:
            path = aStar(grid, tuple(ourSnake['coords'][0]), closestCoin)
            if path != False and not isPositionBetter(grid, ourSnake, tuple(ourSnake['coords'][0]), path, closestCoin): #not position better? whaaa
                move = directions[path.direction()]
                # print "Coin>> " + move
                getcoin = True
        
    #============= FOODS ==============
    #GET FOODS possible without dying
    if not getcoin:
        # print "CHEKCING FOR FOOD"
        # print data['food']
        possibleFoods = []
        for food in data['food']:
            dist = manDist(tuple(ourSnake['coords'][0]), tuple(food))  #snake not defined?
            skip = False
            #avoid snakes closer to the food
            for snake in data['snakes']:
                if snake['id'] != snakeid and (manDist(tuple(snake['coords'][0]), tuple(food)) <= dist):
                    skip = True
                    break
            if not skip:
                possibleFoods.append(tuple(food))
                    
        #Go to closest food
        closestFoodDist = 0
        closestFood = None
        for food in possibleFoods:
            d = manDist(tuple(ourSnake['coords'][0]), food)
            if d < closestFoodDist or closestFood == None:
                closestFood = food
                closestFoodDist = d
        idle = False
        
        if closestFood != None:
            path = aStar(grid, tuple(ourSnake['coords'][0]), closestFood)
            if path != False and not isPositionBetter(grid, ourSnake, tuple(ourSnake['coords'][0]), path, closestFood): #not position better? whaaa
                move = directions[path.direction()]
                # print "Food>> " + move
            else:
                idle = True
        else:
            idle = True
    
    # IDLE ACTIONS
    simpleMovements = False
    if idle:
        # print "IDLING"
        path = False
        ind = 0
        # get random possible locations and paths
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # CHANGE TO LOOK AT ALL LOCATIONS?!
        while not path and ind < idlePathSamples:
            goal = grid.random()
            tmpPath = aStar(grid, tuple(ourSnake['coords'][0]), goal)
            if tmpPath != False and not isPositionBetter(grid, ourSnake, tuple(ourSnake['coords'][0]), tmpPath, goal):
                path = tmpPath
            ind += 1
        if path:
            move = directions[path.direction()]
            # print "Idle>> " + move
        else:
            simpleMovements = True
    
    ## base case
    if simpleMovements:
        # print "SIMPLE MOVEMENTS"
        bGrid = Grid(data['width'], data['height'])
        for snake in data['snakes']:								
            for coord in snake['coords']:							
                bGrid.obstruct(tuple(coord))
            bbb = snake['coords'][-1]
            bGrid.cells[bbb[0]][bbb[1]] = 0
        #ADVANCED: AVOID WALLS
        if mode == 'advanced':
            for wall in data['walls']:
                bGrid.obstruct(tuple(wall))
        
        path = False
        ind = 0
        while not path and ind < idlePathSamples:
            goal = bGrid.random()
            tmpPath = aStar(bGrid, tuple(ourSnake['coords'][0]), goal)
            if tmpPath != False and not isPositionBetter(bGrid, ourSnake, tuple(ourSnake['coords'][0]), tmpPath, goal):
                path = tmpPath
            ind += 1
        if path:
            move = directions[path.direction()]
            # print("Simple>> " + move)

    
    #------DIRECTION CHECK ***FAILSAFE***
    if not move:
        move = 'west'
        # print "failsafe... rip"
    # print "FINAL>> " + move
    
    curdir = None
    for direction in directions:
        if move == directions[direction]:
            curdir = direction
            break
    
    curpos = tuple(ourSnake['coords'][0])
    transpos = (curpos[0] + curdir[0], curpos[1] + curdir[1])
    
    #not sure
    if not grid.contains(transpos) or grid.obstructed(transpos):
        cGrid = Grid(data['width'], data['height'])
        for snake in data['snakes']:		
            for coord in snake['coords']:			
                cGrid.obstruct(tuple(coord))
            bbb = snake['coords'][-1]
            cGrid.cells[bbb[0]][bbb[1]] = 0
            
        #ADVANCED: AVOID WALLS
        if mode == 'advanced':
            for wall in data['walls']:
                cGrid.obstruct(tuple(wall))
            
        for direction in directions:
            if direction == curdir:
                continue
            newpos = (curpos[0] + direction[0], curpos[1] + direction[1])
    
            if cGrid.contains(newpos) and not cGrid.obstructed(newpos):
                move = directions[direction]
                break

    return {
        'move': move,
        'taunt': tList[random.randint(0,lenTList)]
    }

#===== ENDGAME ===================================
@bottle.post('/end')
def end():
    data = bottle.request.json
    # Do nothing, end of game! RIP
    return {}

# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()
if __name__ == '__main__':
    bottle.run(application, host=os.getenv('IP', '0.0.0.0'), port=os.getenv('PORT', '8080'))
