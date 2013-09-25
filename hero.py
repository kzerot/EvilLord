'''
Created on 05.08.2013

@author: Max
'''
from constants import templateNeutral, templateNegative, templatePositive, heroGoPercent, templateHero,\
    heroGetInfoPercent
from psycopg2.extras import Json
from SimpleObjects import SimpleItem
from random import randint
class Hero(object):
    def __init__(self, data=None, row=None, name=None, id=None):
        print('hero from data: ', row, name, id)
        self.updatedFields = []
        self.data = data
        self.name = ''
        self.merits_flaws = []   
        self.id = -1
        self.isFemale = True
        self.questData = None
        self.memory = { 'itemsKnow': [] }
        self.action = None
        self.locationId = -1
        self.backpack = {'simple_items':{}}
        self.__loc = None
        self.isInFight = False
        self.level = -1
        self.intellect =0 
        self.strength =0
        self.morality =0 
        self.lordId = None
        if row:
            self.level = row['level']
            self.hp = row['hp']
            self.intellect = row['intellect']
            self.strength = row['strength']
            self.morality = row['morality']
            self.name = row['name']
            self.merits_flaws = row['merits_flaws']     
            self.id = row['id']
            self.isFemale = row['is_woman']
            self.questData = row['quest_data']
            self.memory = row['memory']
            if not self.memory: self.memory = { 'itemsKnow': [] }
            self.action = row['action']
            self.locationId = row['location_id']
            self.backpack = row['backpack']
            self.lordId = row['lord_id']
            
        elif name and id:
            self.name = name
            self.id = id
        self.monster = None

    @property
    def hp(self):
        return self._hp  
    
    @hp.setter
    def hp(self, value):
        if value <= 100:
            self._hp = value
        else: self._hp = 100
    
    def addHp(self, hp):
        self.hp = self._hp + hp;
        self.toUpdate('hp')
    
    @property
    def simpleItems(self):
        si = self.backpack['simple_items']
        return {SimpleItem.dic[sid]:si[sid] for sid in si}
    
    def countItem(self, iType, iId):
        i=0
        if iType == 'simple_items':
            if str(iId) in self.backpack['simple_items']:
                return self.backpack['simple_items'][str(iId)]
        return i
    
    def putItem(self, iType, iId):
        if iType == 'simple_items':
            self.heroSay('Снял с тела монстра %s! Отличное приобретение.' \
                         % self.data.getSimpleItemById(iId).name)
            if iId in self.backpack['simple_items']:
                self.backpack['simple_items'][iId] += 1
            else:
                self.backpack['simple_items'][iId] = 1
    
    @property
    def lines(self):
        lines = []
        name = 'name'
        if self.isFemale:
            name = 'name2'
        for mf in self.merits_flaws:
            if mf['weight'] == 0:
                lines.append(templateNeutral % mf[name])
            elif mf['weight'] > 0:
                lines.append(templatePositive % mf[name])
            elif mf['weight'] < 0:
                lines.append(templateNegative % mf[name])              
        return lines

    @property
    def caption(self):
        return self.name
               
    @property
    def html(self):
        return templateHero % { 'id': self.id, 'name': self.name }
    
    @property
    def location(self):
        if not self.__loc or self.__loc.id != self.locationId:
            self.__loc = self.data.getLocationById(self.locationId)
        return self.__loc
        
    def __str__(self):
        return self.name

    def updateHero(self):
        row = self.data.getHeroData(self.id)
        self.level = row['level']
        self.hp = row['hp']
        self.intellect = row['intellect']
        self.strength = row['strength']
        self.morality = row['morality']
        self.name = row['name']
        self.merits_flaws = row['merits_flaws']     
        self.id = row['id']
        self.isFemale = row['is_woman']
        self.questData = row['quest_data']
        self.memory = row['memory']
        if not self.memory: self.memory = { 'itemsKnow': [] }
        self.action = row['action']
        self.locationId = row['location_id']
        self.backpack = row['backpack']
        self.lordId = row['lord_id']
        self.toUpdate('updated')
        
        
    def toUpdate(self, *args):
        for string in args:
            if string not in self.updatedFields:
                self.updatedFields.append(string)
            
    def heroSay(self, string):
        if not self.lordId: return
        self.data.cur.execute('select messages from game.heroes where id = %s', (self.id,))
        serverMessages = self.data.cur.fetchone()[0]
        if len(serverMessages) > 0 and string == serverMessages[-1]:
            return
        
        toMessage = ''
        query = ''
        if len(serverMessages) > 19: 
            toMessage = serverMessages[1:]+[string]
            query = ''''update game.heroes set messages = %s  where id = %s'''
        else:
            query = '''update game.heroes set messages = messages || %s  where id = %s'''
            toMessage = [string]
        self.data.cur.execute(query, (toMessage, self.id))
        
    def think(self):
        #Every turn hero gain hp
        #=======================================================================
        # print('Thinking for hero ', self.name)
        # print('Action ', self.action)
        # print('Quest', self.questData)
        #=======================================================================
        
        if self.hp <= 50 and (not self.action or self.action['type'] != 'heal'): #Want to rest
            print('HEAL')
            self.action = {'type':'heal', 'progress': 0}
            
        elif not self.action and ( not self.questData or len(self.questData)) == 0:
            print('REST')
            self.heroSay('Отдых - любимая часть задания!')
            
        elif self.action:
            print('ACTION OK')
            #print ('His progress:', self.action['progress'])
            'Герой что-то делает, пусть продолжает'
            actionType = self.action['type']
            if actionType == 'heal':
                print('ACTION HEAL')
                self.heroSay('Лечу раны. Пью настойки.')
                self.addHp(10)
                if self.hp >= 90: self.action = None
                
            elif actionType == 'go':
                print('ACTION GO')
                coordinate = self.action['xy']
                self.action['progress'] 
                self.action['progress'] += heroGoPercent * self.location.type.slow
                if self.action['progress'] >= 100:
                    loc = self.location
                    x, y = coordinate
                    dx = dy = 0
                    if x != loc.x: 
                        dx = (x - loc.x) / abs(x - loc.x)
                    if y != loc.y and dx == 0:
                        dy = (y - loc.y) / abs(y - loc.y)
                    newloc = self.data.getLocByCoor(loc.x + dx, loc.y + dy)
                    self.locationId = newloc.id
                    self.action = None
                    #print('Hero go to new loc, ', loc.x + dx, loc.y + dy)
                    self.toUpdate('location_id')
                    self.heroSay('Вижу где-то вдалеке %(name)s, цель пути стала еще немного ближе!' % {'name' : self.location.type.name})
                else: 
                    self.heroSay('Иду-бреду по %(name3)s, на птичек смотрю. Хорошо тут.' % {'name3' : self.location.type.name3})
            elif actionType == 'getinfo':
                
                print('ACTION GETINFO')
                self.action['progress'] += heroGetInfoPercent
                if self.action['itemType']=='simple_items':
                    if self.action['progress'] >= 100:
                        'Ask tavernman where can he find this item. After this action,'
                        'hero can find this item himself if only this item is not rare'
                        self.memory['itemsKnow'].append(self.action['itemId'])
                        self.toUpdate('memory')
                        self.heroSay('Отлично! Я все-таки узнал, где искать %s!' % \
                                     self.data.getSimpleItemById(self.action['itemId']))
                        self.action = None
                    else:
                        self.heroSay('Пытаюсь узнать, где искать %s!' % \
                                     self.data.getSimpleItemById(self.action['itemId']))
                    
        elif self.questData and len(self.questData) > 0 and not self.action:
            'Герой закончил что-то делать'
            curData = self.questData[0]
            if curData['task'] == 'find':
                print('QUEST FIND')
                if curData['itemId'] not in self.memory['itemsKnow']:
                    
                    print('QUEST DON\'T KNOW')
                    'Герой не знает, где искать данный итем'
                    'Нужно пойти в таверну'
                    newTarget = self.data.findNearTavernLoc(self.locationId)
                    if newTarget.id != self.locationId:
                        coordinate = [ newTarget.x, newTarget.y ]
                        self.action = { 'type':'go', 'xy':coordinate, 'progress':0 }
                    else:
                        'hero already in town with tavern'
                        self.action = {'type':'getinfo', 'itemType': 'simple_items', 'itemId':curData['itemId'], 'progress':0 }
                    
                elif curData['itemId'] in self.memory['itemsKnow'] and \
                        curData['count'] > self.countItem('simple_items', curData['itemId']):
                    print('QUEST GO TO KILL, NOT ENOUGH', curData['count'], self.countItem('simple_items', curData['itemId']))
                    'Hero knows where he can find item (usually he need kill somebody)'
                    'He need go and kill monster and save loot'
                    neededLoc = self.data.getLocForItem(curData['itemId'], self.location)
                    if neededLoc.id != self.locationId:
                        self.action = { 'type':'go', 'xy': [neededLoc.x,neededLoc.y], 'progress':0 }
                    elif curData['count'] > self.countItem('simple_items', curData['itemId']):
                        self.action = None
                        self.startFarm('simple_items', curData['itemId'])
                        self.toUpdate('is_in_fight')
                        
                elif curData['count'] <= self.countItem('simple_items', curData['itemId']):
                    print('Hero found items! Back to town!')
                    print('Need', curData['count'], 'have', self.countItem('simple_items', curData['itemId']))
                    print('QUEST GO HOME')
                    newTarget = self.data.getLordTownLoc(curData['lordId'])
                    if newTarget.id != self.locationId:
                        coordinate = [ newTarget.x, newTarget.y ]
                        self.action = { 'type':'go', 'xy':coordinate, 'progress':0 }
                    else:
                        'hero already in town - can complite quest'
                        self.action = None
                        self.data.completeQuest(curData)
                        
                        self.backpack['simple_items'][str(curData['itemId'])] -= curData['count']
                        self.heroSay('Так, квест завершил. Можно расслабиться немного.')
                        if len(self.questData) > 1:
                            self.questData = self.questData[1:]
                        else:
                            self.questData = []
                        self.toUpdate('quest_data', 'backpack')
                            
        self.toUpdate('action', 'hp')
        self.save()
        
    def startFarm(self, type, id):
        'first, detect with who we will fight'
        enemyId = -1
        if type == 'simple_items':
            enemyId = self.data.getEnemyForFarmSI(id, self.location)
        
        if enemyId < 0:
            self.heroSay('Хм. Хотел убить монстра - а монстр куда-то делся...')
            self.isInFight = False
            return
        self.monster = self.data.getMob(enemyId)
        self.isInFight = True
        self.heroSay('Ну держись, монстрюга... Я погублю твое тело и присвою себе твой лут!')
        
    def fight(self):
        'process fight'
        if self.monster:
            self.monster.hp -= self.strength / 10
            self.hp -= self.monster.strength / 10
            
            if self.monster.hp <= 0:
                'Win!'
                winitem = self.monster.loot[randint(0, len(self.monster.loot)-1)]
                self.putItem('simple_items', winitem)
                self.monster = None
                self.isInFight = False
                self.toUpdate('backpack')
                self.heroSay('Ура, еще один чертяка повержен!')
            elif self.hp <= 0:
                'Fail!'
                self.isInFight = False
                self.heroSay('Кажется, я немного умер. ')
            else:
                'Continue'
                self.heroSay('И мы пиздили друг друг так цинично и жестоко...')
            self.toUpdate('action', 'hp', 'is_in_fight')
            self.save()
        else:
            self.isInFight = False
        

    def save(self):
        dic = { 'name':self.name,
            'merits_flaws' :self.merits_flaws,
            'id': self.id,
            'is_woman': self.isFemale,
            'quest_data': Json(self.questData),
            'memory': Json(self.memory),
            'action': Json(self.action),
            'location_id': self.locationId,
            'is_in_fight': self.isInFight,
            'hp': int(self.hp),
            'lord_id': self.lordId,
            'backpack': Json(self.backpack),
            'updated': False,
            }
        query = 'update game.heroes set '
        for field in self.updatedFields:
            query += field + '=' + "%(" + field + ")s, "
            
        query = query[:-2] + ' where id = %(id)s'
        self.data.cur.execute(query, dic)
            

