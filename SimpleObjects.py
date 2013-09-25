'''
Created on 09.08.2013

@author: Max
'''

class SimpleItem(object):
    dic = {}
    @staticmethod
    def add(sItem):
        if sItem.id not in SimpleItem.dic:
            SimpleItem.dic[sItem.id] = sItem
    
    @staticmethod
    def load(dt):
        for row in dt:
            SimpleItem(row)
            
    def __init__(self, row):
        self.id = row['id']
        self.name = row['name']
        self.value = row['value']
        SimpleItem.add(self)

class Resp(object):
    def __init__(self, type, text):
        self.type = type
        self.text = text
    def __str__(self, *args, **kwargs):
        return '%s: %s' % (self.type, self.text)
    
    
class Building(object):
    def __init__(self, data):
        self.name = data['name']
        self.level = data['level']
    @property
    def html(self):
        return  '<li title="Уровень здания: %(title)s">%(name)s</li>' % \
            {'title':self.level, 'name':self.name }

class Lord(object):
    def __init__(self, data):
            self.name, self.mana, self.gold, \
            self.beer, self.luxory, self.food, self.simpleItems = \
                data['name'], data['mana'], data['gold'], \
                data['beer'], data['luxory'], data['food'], data['simple_items']
            self.herocount = 0
            self.power = 0

class Location(object):
    def __init__(self, data=None):
        self.id = data['id']
        self.description = data['description']
        self.x = data['x']
        self.y = data['y']
        self.type = LocType.dic[data['type']]
    def __str__(self, *args, **kwargs):
        if self.type:
            return '%d:%d %s' % (self.x, self.y, self.type) 
        return '%d:%d %s' % (self.x, self.y, 'Не определено') 

class Mob(object):
    def __init__(self, row):
        self.id = row['id']
        self.hp = row['hp']
        self.strength = row['strength']
        self.name = row['name']
        names = row['name2'].split('|')
        self.name2 = self.name3 = row['name2']
        if (len(names) > 1):
            self.name2, self.name3 = names
        self.loot = row['loot']
        self.descr = row['descr']

class LocType(object): 
    dic = {}
    
    @staticmethod
    def Add(locType):
        LocType.dic[locType.id] = locType
    
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