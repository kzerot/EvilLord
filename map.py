'''
Created on 11.07.2013

@author: Max
'''
from commandprocessor import CommandProcessor
from random import randint, random, seed
import math
from datetime import datetime
colors = { "desert": "#FAE457",  # 'grass_small.png',
            "water": "#0800FF",  # 'grass_small.png',
            "wood": "#165700",  # 'grass_small.png',
            "mountain" : "#7D827C",  # 'grass_small.png',
            "field": "#73E84D"  # 'grass_small.png'
            }

randomStr = 0.4

stability = { "desert": 1.1,
            "water":1,
            "wood": 1.1,
            "mountain": 1.1,
            "field":1.2
            }

class Location(object):
    def __init__(self, data=None):
        self.id = data['id']
        self.description = data['description']
        self.x = data['x']
        self.y = data['y']
        self.type = LocType.dicId[data['type']]
    def __str__(self, *args, **kwargs):
        if self.type:
            return '%d:%d %s' % (self.x, self.y, self.type.name) 
        return '%d:%d %s' % (self.x, self.y, 'Не определено') 
    
class LocType(object): 
    dic = {}
    avaibleTypes = []
    dicId = {}
    
    @staticmethod
    def Add(locType):
        if locType.baseType in LocType.dic.keys() and locType not in LocType.dic[locType.baseType]:
            LocType.dic[locType.baseType].append(locType)
        elif locType.name not in LocType.dic.keys():
            LocType.dic[locType.baseType] = [locType, ]
        LocType.dicId[locType.id] = locType
        LocType.avaibleTypes.append(locType)
    
    @staticmethod
    def getRandomLocType(baseType=None, ltype=None):
        if not baseType:
            return LocType.avaibleTypes[randint(0, len(LocType.avaibleTypes) - 1)]
        elif not ltype:
            arr = LocType.dic[baseType]
            return arr[randint(0, len(arr) - 1)]
        else:
            res = []
            arr = LocType.dic[baseType]
            for a in arr:
                if a.type == ltype:
                    res.append(a)
            return res[randint(0, len(res) - 1)]
    
    @staticmethod     
    def Load(dataTable):
        for row in dataTable:
            LocType(row)
                    
    def __init__(self, data):
        self.id = data['id']
        self.type = data['type']
        self.name = data['name']
        names = data['name2'].split('|')
        self.name2 = self.name3 = data['name2']
        if (len(names) > 1):
            self.name2, self.name3 = names
        self.slow = data['slow']
        self.baseType = data['base_type']
        LocType.Add(self)

class Map(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.template = '%d-%d'
        self.cp = CommandProcessor()
        LocType.Load(self.cp.getLocTypes())
        self.locs = {}
        self.locsByCoor = []
        self.rangire = 0
        
    def load(self):
        for loc in self.cp.getLocations():
            self.locs[self.template % (loc['x'], loc['y'])] = Location(loc)
        count = len(self.locs)
        self.rangire = int((math.sqrt(count) - 1) / 2)
    
    def wipe(self, fromRadius=0, maxRadius=50):
        for loc in self.locs.values():
            if ((abs(loc.x) <= maxRadius and abs(loc.x) > fromRadius) or \
                (abs(loc.y) <= maxRadius and abs(loc.y) > fromRadius)):
                loc.type = None
            
    def getLocByCoor(self, x, y):
        if self.template % (x, y) in self.locs.keys():
            return self.locs[self.template % (x, y)]
        return None

    def getNeighs(self, x, y, useDiagonal=True):
        dxs = None
        if useDiagonal:
            dxs = ((x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y), (x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1))
        else:
            dxs = ((x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y))
        neighs = []
        for dxy in dxs:
            dx = dxy[0]
            dy = dxy[1]
            if dx < -self.rangire:
                dx += self.rangire * 2 + 1
            elif dx > self.rangire:
                dx -= self.rangire * 2 + 1
            if dy < -self.rangire:
                dy += self.rangire * 2 + 1
            elif dy > self.rangire:
                dy -= self.rangire * 2 + 1  
            
            neighs.append(self.locs[self.template % (dx, dy)])   
        return  neighs
    
    def getNewLocType(self, x, y):
        
        potencialLocTypes = {}
        for dxy in ((x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)):
            dx = dxy[0]
            dy = dxy[1]
            if dx < -self.rangire:
                dx += self.rangire * 2 + 1
            elif dx > self.rangire:
                dx -= self.rangire * 2 + 1
            if dy < -self.rangire:
                dy += self.rangire * 2 + 1
            elif dy > self.rangire:
                dy -= self.rangire * 2 + 1  
                
            neigh = self.getLocByCoor(dx, dy)
            if neigh and neigh.type:
                if neigh.type.type == neigh.type.baseType:
                    potencialLocTypes[neigh.type] = random() * stability[neigh.type.baseType]
                else:
                    locType = LocType.getRandomLocType(neigh.type.baseType)
                    potencialLocTypes[locType] = random() * 0.9 * stability[locType.baseType]
        randLocType = LocType.getRandomLocType()
        potencialLocTypes[randLocType] = random() * randomStr * stability[randLocType.baseType]

        result = sorted(potencialLocTypes, key=lambda t: potencialLocTypes[t], reverse=True)[0]
        # print('Get new type', (datetime.now()-time).total_seconds())
        return result
    
    def generateMap(self, fromRadius=0, maxRadius=50):
        i = -1
        seed(datetime.now())
        self.rangire = maxRadius
        data = {'id':self.locs[self.template % (-maxRadius, -maxRadius)].id,
            'description':self.locs[self.template % (-maxRadius, -maxRadius)].description,
            'x':-maxRadius,
            'y':-maxRadius,
            'type': LocType.getRandomLocType('field').id
            }
        loc = Location(data)
        self.locs[self.template % (loc.x, loc.y)] = loc        
        for x in range(-maxRadius, maxRadius + 1):
            i *= -1
            for y in range(-maxRadius, maxRadius + 1):
                y *= i
                if (x > fromRadius or y > fromRadius) or\
                   (x < -fromRadius or y < -fromRadius):
                    data = {'id': self.locs[self.template % (loc.x, loc.y)].id,
                        'description': self.locs[self.template % (loc.x, loc.y)].description,
                        'x': x,
                        'y': y,
                        'type': self.getNewLocType(x, y).id
                        }
                    loc = Location(data)
                    # print('Gen new loc', (datetime.now()-time).total_seconds())
                    self.locs[self.template % (loc.x, loc.y)] = loc

    def htmlMap(self):
        body = ''
#        count = len(self.locs)
#        predel = int((math.sqrt(count) - 1) / 2 )
#        print(predel)
        predel = self.rangire
        for x in range(-predel, predel + 1):
            for y in range(-predel, predel + 1):
                loc = self.getLocByCoor(x, y)
                htmlTemplate = '''<div id='%s' style="float:left;margin:0px;width:10px; height:10px; background-color:%s;background-position: -4px -4px;"></div>'''
                body += htmlTemplate % ('%d-%d' % (x, y), colors[loc.type.baseType])
            body += '<div style="width:10px;height:10px;"></div>'

        with open('tmp.html', 'w') as f:
            f.write(body)
            
    def saveMap(self):
        for loc in self.locs.values():
            if loc.id:
                self.cp.updateDBLoc(loc)
            else:
                self.cp.createDBLoc(loc)
        self.cp.commit()
    
    def smoothMap(self, fromRadius=0, maxRadius=50, strengh=4):
        for loc in self.locs.values():
            if ((abs(loc.x) <= maxRadius and abs(loc.x) > fromRadius) or \
                (abs(loc.y) <= maxRadius and abs(loc.y) > fromRadius)):
                waters = 0
                woods = 0
                fields = 0
                similar = 0
                neighs = self.getNeighs(loc.x, loc.y)
                
                
                for neigh in neighs:
                    if neigh.type.type == loc.type.type and \
                        neigh.type.baseType == loc.type.baseType:
                        similar += 1
                    elif neigh.type.type == 'water':
                        waters += 1
                    elif neigh.type.type == 'field':
                        fields += 1
                    elif neigh.type.type == 'wood':
                        woods += 1
                        
                if similar > 0 and waters < strengh and fields < strengh + 1 and woods < strengh + 1:
                    continue
                
                if waters >= strengh:
                    loc.type = LocType.getRandomLocType(baseType='water', ltype='water')    
                elif fields >= strengh + 1:
                    loc.type = LocType.getRandomLocType(baseType='field', ltype='field')
                elif woods >= strengh + 1:
                    loc.type = LocType.getRandomLocType(baseType='wood', ltype='wood')
                    
                elif waters >= fields and waters >= woods:
                    loc.type = LocType.getRandomLocType(baseType='water', ltype='water')    
                elif fields > woods:
                    loc.type = LocType.getRandomLocType(baseType='field', ltype='field')      
                else:
                    loc.type = LocType.getRandomLocType(baseType='wood', ltype='wood')  
                    

                     
                
        
if __name__ == '__main__':
    seed(datetime.now())
    print('start')
    map1 = Map()
    print('loading')
    map1.load()
    # map1.wipe(0,100)
    print('generating')
    # map1.generateMap(0,100)
    # map1.smoothMap(0,100, 4)
    print('to html')
    map1.htmlMap()
    print('saving')
    # map1.saveMap()
    print('end')
