'''
Created on 05.08.2013

@author: Max
'''
import psycopg2  
from psycopg2.extras import Json
from datetime import datetime
from constants import *
from hero import Hero 
from SimpleObjects import *

class DBConnector(object):
    def __init__(self):
        self.conn = psycopg2.connect(connectionString)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        LocType.Load(self.getLocTypesDt())
        SimpleItem.load(self.getSimpleItemsDt())
        
# Locations commands        
    def findNearTavernLoc(self, locId):
        query = ''' with towns as ( select loc_id, unnest(buildings) b from game.towns), 
townsWithBuild as (select loc_id from towns t join game.buildings b on t.b = b.id where b.code = 'tavern'),
oldloc as (select x,y from game.locations where id = %(id)s) 
select l.*
from townsWithBuild twb join game.locations l on l.id = loc_id cross join oldloc
order by abs(l.x - oldloc.x) + abs(l.y - oldloc.y) 
        '''
        self.cur.execute(query, {'id':locId})
        return Location(self.cur.fetchone())
        
    def getLocations(self):
        query = '''select * from game.locations'''
        self.cur.execute(query)
        return self.cur.fetchall()

    def getLocationById(self, lId):
        query = '''select * from game.locations where id = %s'''
        self.cur.execute(query, (lId,))
        return Location(self.cur.fetchone())

    def getLocByCoor(self, x, y):
        query = '''select * from game.locations where x = %s and y = %s'''
        self.cur.execute(query, (x, y))
        return Location(self.cur.fetchone())
        
    def getLocTypesDt(self):
        query = '''select * from game.loc_types'''
        self.cur.execute(query)
        return self.cur.fetchall()

    def getEnemyForFarmSI(self, siId, loc):
        query = '''select m.id from game.monster_types m
                   join game.locations loc on m.id = ANY(loc.monsters)
                   where loc.id = %(locId)s and %(itemId)s = ANY (m.loot)
                   ORDER BY RANDOM() LIMIT 1'''
        self.cur.execute(query, {'locId':loc.id,'itemId':siId})
        return self.cur.fetchone()['id']
    
    def getLocForItem(self, itemId, fromLoc):
        query = '''select loc.*
            from game.locations loc 
            join game.monster_types m on m.id = ANY(loc.monsters)
            where %(iId)s = ANY(m.loot) and loc.id not in (select loc_id from game.towns)
            order by abs( loc.x - %(x)s) + abs( loc.y - %(y)s)
            limit 1'''
        self.cur.execute(query, {'x':fromLoc.x, 'y':fromLoc.y, 'iId': itemId})
        return Location(self.cur.fetchone())

#Mob
    def getMob(self, mId):
        query = '''select * from game.monster_types where id = %s'''
        self.cur.execute(query, (mId,))
        return Mob(self.cur.fetchone())        

#Items command
    def getSimpleItemsDt(self):
        query = '''select * from game.simple_items'''
        self.cur.execute(query)
        return self.cur.fetchall()        

    def getSimpleItemById(self, siId):
        query = '''select * from game.simple_items where id = %s'''
        self.cur.execute(query, (siId,))
        return SimpleItem(self.cur.fetchone())

    
    def getResponse(self, word):
        query = '''SELECT id, machine, answer
                  FROM game.responses t
                  where t.machine=%s
                  ORDER BY RANDOM()
                  LIMIT 1'''
        self.cur.execute(query, (word,))
        result = self.cur.fetchone()
        if result:
            return result['answer'] 
        return 'Даже не знаю, что и ответить!'
        
    def getFlawMerits(self, ids):    
        query = '''select * from merit_flaw where id in (%s) order by weight desc''' % \
                        ', '.join(str(i) for i in ids)
        self.cur.execute(query)
        return self.cur.fetchall()
        
    def getPhraseResponse(self, finresult, phrase, lord, names, forwho='town'):
        if (phrase == 'hire' and len(names) == 0) or phrase == 'hirelist':
            query = '''select h.*
                       from game.heroes h
                       join game.towns t 
                       on  t.loc_id = h.location_id
                       where t.lord_id = %(lordId)s
                       and h.lord_id is null
                        '''
            self.cur.execute(query, {'lordId':lord['id']})
            result = self.cur.fetchall()
            if result:
                response = 'В таверне Вашего города сидят и ждут, чтобы их наняли следующие герои: '
                for hero in result:
                    response += templateName % {'id': hero['id'], 'name': hero['name']}
            else:
                response = 'Сейчас в Вашем городе нет героев!'
            
            finresult.append(Resp('answer' , response))
                
        elif (phrase == 'hire' and len(names) > 0):
            if len(names) == 1:  # All is ok
                finresult.append(Resp('answer' , self.hire(names[0], lord['id'])))
                finresult.append(Resp('update' , 'hero'))
            elif len(names) > 1:
                return finresult.append(Resp('answer' , 'Определитесь, какого героя хотите нанять!'))
                          
    def getLastHero(self):
        query = '''select h.*
                   from game.heroes h
                   order by id desc
                   limit 1
                    '''
        self.cur.execute(query)
        data = self.cur.fetchone()
        data['merits_flaws'] = self.getFlawMerits(data['merits_flaws'])
        return Hero(self, data)  

    def getHero(self, hid):
        query = '''select h.*
                   from game.heroes h
                   where id = %s
                    '''
        self.cur.execute(query, (hid,))
        data = self.cur.fetchone()
        data['merits_flaws'] = self.getFlawMerits(data['merits_flaws'])
        return Hero(self, data)        
    
    def getHeroForUpdate(self):
        query = '''select h.id
                   from game.heroes h
                   where updated = True
                    '''
        self.cur.execute(query)
        data = self.cur.fetchall()
        return [r['id'] for r in data]         
    
    def getHeroData(self, hid):
            query = '''select h.*
                       from game.heroes h
                       where id = %s
                        '''
            self.cur.execute(query, (hid,))
            data = self.cur.fetchone()
            data['merits_flaws'] = self.getFlawMerits(data['merits_flaws'])  
            return data
              
    'Command for misc'
    def getLocTile(self, x, y, width=16):
        
        query = '''select lt.id, image,loc.x, loc.y
                    from game.locations loc 
                    join game.loc_types lt on loc.type = lt.id
                    where loc.x between %(x1)s and %(x2)s 
                      and loc.y between %(y1)s and %(y2)s 
                    order by loc.x, loc.y
                '''
        x2 = x + width
        y2 = y + width
        result = self.cur.execute(query, {'x1':x, 'x2':x2, 'y1':y, 'y2':y2})
        arr = []
        oldY = None
        for row in result:
            if oldY != row['y']:
                oldY = row['y']
                arr.append([])
            arr[-1].append({ 'id': row['id'], 'img': row['image'], 'x': row['x'], 'y': row['y'] })
        return arr
    
    def updateDBLoc(self, loc):
        query = ''' update game.locations 
                    set type = %(type)s
                    where x = %(x)s and y = %(y)s'''
        self.cur.execute(query, {'x':loc.x, \
                                 'y':loc.y, \
                                 'type': loc.type.id})
        
        
    def createDBLoc(self, loc):
        query = ''' insert into game.locations (x,y,type)
                    values( %(x)s,%(y)s, %(type)s)'''
        self.cur.execute(query, {'x':loc.x, \
                                 'y':loc.y, \
                                 'type': loc.type.id})        
    
    def commit(self):
        self.conn.commit()
        
    'Common comands'
    def hire(self, name, lordId):
        query = '''select h.lord_id = %s as is_your, h.* from game.heroes h 
                   join game.towns t on t.loc_id = h.location_id
                   where h.name = %s and t.lord_id = %s'''
        self.cur.execute(query, (lordId, name, lordId))
        result = self.cur.fetchall()
        if len(result) == 1:  # ok
            if result[0]['is_your']:
                return 'Герой %s уже служит вам.' % result[0]['name']
            query = '''update game.heroes
                        set lord_id = %s
                        where name = %s'''
            self.cur.execute(query, (lordId, name))
            self.conn.commit()
            return 'Герой, известный как "%s", теперь служит Вам, мой господин!' % result[0]['name']
        elif len(result) > 1:
            return 'Слишком много героев с именем, похожим на это.' \
                    ' Пожайлуйста, напишите имя предельно точно!'
        else:
            return 'Нет героев с таким именем в вашем городе, уж извините!'

    def setPhase(self, heroId, phaseType, paramDict):
        pass
    
    def messageTolord(self, lordId, msg):
        try:
            self.cur.callproc("game.add_message", (lordId, msg))
        except:
            self.restartConnection()
                
    def completeQuest(self, data, heroId=None):
        lordId = data['lordId']
        
        if data['task'] == 'find':
            lordItems = self.getLordById(lordId)['simple_items']
            print(lordItems)
            if not lordItems:
                lordItems = { str(data['itemId']) : data['count'] }
            elif data['itemId'] in lordItems:
                lordItems[str(data['itemId'])] =  lordItems[str(data['itemId'])] + data['count']
            else:
                lordItems[str(data['itemId'])] = data['count']

            self.messageTolord(lordId, 'Квест завершен, и герой вам что-то принес!')
            self.messageTolord(lordId, 'update_items')
            query ='''update game.lords 
                      set simple_items = %s
                      where id = %s'''
            self.cur.execute(query, (Json(lordItems), lordId))
            self.commit()
            query = ''
    
    def setQuest(self, lordId, heroId, type, paramDict):
        if type == 'find':
            if len(paramDict) == 0:
                return ['answer', 'Не могу понять, что надо искать!']
            hero = self.getHero(heroId)
            if not hero.questData:
                hero.questData = []
            # First, our hero need more info    
            for item in paramDict:
                hero.questData.append({'task': 'find', 'itemId':item['itemId'], 'lordId':lordId, 'count': item['count']})

            query = 'update game.heroes set quest_data = %s where id = %s'
            self.cur.execute(query, (Json(hero.questData), hero.id))
            self.conn.commit()
            return ['answer', 'Приказ понял, выполняю!']

    def build(self, building, lord):
        isInProg = self.isInProgress(lord['id'])
        if (isInProg):
            return ['error', isInProg]
        lordBuildings = self.getLordBuilding(lord['id'], building)
        level = 0
        query = '''INSERT INTO game.build_in_progress(
                    town_id, building_id, old_building_id, build_at)
                    VALUES (%s, %s, %s, %s)'''
        oldId = None
        if lordBuildings:
            level = lordBuildings['level'] + 1
            oldId = lordBuildings['id']
        newBuilding = self.getBuilding(building, level)
        print('Available building: ', newBuilding, level)
        if newBuilding:
            if newBuilding['gold'] <= lord['gold'] and \
               newBuilding['mana'] <= lord['mana'] and \
               newBuilding['beer'] <= lord['beer'] and \
               newBuilding['luxory'] <= lord['luxory'] and \
               newBuilding['food'] <= lord['food']:
                self.cur.execute(query, (lord['town_id'], newBuilding['id'],
                                         oldId, newBuilding['build_time'] + datetime.now()))
                self.cur.execute('''update game.lords 
                                    set gold = gold - %s,
                                        mana = mana - %s,
                                        beer = beer - %s,
                                        luxory = luxory - %s,
                                        food = food - %s
                                    where id = %s
                                 ''', (newBuilding['gold'],
                                     newBuilding['mana'],
                                     newBuilding['beer'],
                                     newBuilding['luxory'],
                                     newBuilding['food'], lord['id']))
                self.conn.commit()
                return ['ok', '']
            else:
                return ['error', 'Недостаточно денег, что поделать!']
        elif lordBuildings:
            return ['error', 'Это здание уже не улучшить и не достроить!']
        else:
            return ['error', 'Нет такого здания!']
    
    #Lord Queries
    def getHeroMessages(self, lord):
        finresult = {}
        for hId in self.getLordHeroIds(lord):
            self.cur.callproc("game.get_hero_messages", (hId,))
            result = self.cur.fetchone()
            self.conn.commit()
            if result[0]:
                finresult[hId] = result[0]
        return finresult       
    
    def getMessages(self, lord):
        self.cur.callproc("game.get_messages", (lord,))
        result = self.cur.fetchone()
        self.conn.commit()
        if result[0]:
            return result[0]
        return []    
    
    def getLordTownLoc(self, lordId):
        self.cur.execute('''select l.*  
                  from game.towns u
                  join game.locations l on l.id = u.loc_id
                  where u.lord_id = %s''', (lordId,))
        return Location(self.cur.fetchone())
        
    def getLordIdByName(self, lord_name):
        self.cur.execute('''select u.id 
                  from game.lords u
                  where u.name = %s''', (lord_name,))
        return self.cur.fetchone()['id']
    
    def getLord(self, lord_name):
        self.cur.execute('''select u.*, t.id as town_id, t.name as town_name,
                          u.cyrname as name, mana, gold, beer, luxory, food, simple_items
                          from game.lords u
                          join game.towns t on u.id = t.lord_id
                          where u.name = %s''', (lord_name,))
        return self.cur.fetchone()

    def getLordById(self, lordId):
        self.cur.execute('''select u.*, t.id as town_id, t.name as town_name,
                          u.cyrname as name, mana, gold, beer, luxory, food, simple_items
                          from game.lords u
                          join game.towns t on u.id = t.lord_id
                          where u.id = %s''', (lordId,))
        return self.cur.fetchone() 
    
    def getBuilding(self, building, level):
        query = '''SELECT id, name, description, code, level, 
                          gold, mana, beer, luxory, 
                          food, build_time
                   FROM game.buildings
                   where code = %s and level = %s'''
        self.cur.execute(query, (building, level))
        return self.cur.fetchone()     
        
    def getLordBuilding(self, lordId, building):
        query = '''with t as (
                SELECT unnest(buildings)  building, id
                FROM game.towns 
                where lord_id = %s) 
                select t.id as town_id, b.code, b.level, b.id from t
                join game.buildings b on t.building = b.id
                where code = %s'''
  
        self.cur.execute(query, (lordId, building))
        return self.cur.fetchone()

    def getLordBuildings(self, lordName):
        lordId = self.getLordIdByName(lordName)
        query = '''with t as (
                SELECT unnest(buildings)  building
                FROM game.towns 
                where lord_id = %s) 
                select b.name, b.level from t
                join game.buildings b on t.building = b.id'''
  
        self.cur.execute(query, (lordId,))
        result = self.cur.fetchall()
        print('List of buildngs')
        return [Building({'name' : row['name'], 'level' : row['level']}) for row in result]

    def getLordBuildingIds(self, lordId):
        '''Get buildings id's for selected lord'''
        query = '''with t as (
                SELECT unnest(buildings)  building
                FROM game.towns 
                where lord_id = %s) 
                select b.id from t
                join game.buildings b on t.building = b.id'''
  
        self.cur.execute(query, (lordId,))
        result = [b[0] for b in self.cur]
        return result     

    def getLordHeroIds(self, lordName='', lordId=-1):
        if lordName and lordName != '':
            lordId = self.getLordIdByName(lordName)
        query = '''select id from game.heroes where lord_id = %s'''
        self.cur.execute(query, (lordId,))
        result = self.cur.fetchall()
        return [row['id'] for row in result]

    def getLordHeroes(self, lordName):
        lordId = self.getLordIdByName(lordName)
        query = '''select *
                   from game.heroes where lord_id = %s'''
        self.cur.execute(query, (lordId,))
        result = self.cur.fetchall()
        return [ Hero(self, {'name' : row['name'],
                  'id' : row['id'],
                  'merits_flaws': self.getFlawMerits(row['merits_flaws']),
                  'is_woman': row['is_woman'],
                  'quest_data': row['quest_data'],
                  'action': row['action'],
                  'location_id': row['location_id'],
                  'memory': row['memory'],
                  'messages': row['messages'],
                  'backpack':row['backpack'],
                  'level':row['level'],
                  'hp':row['hp'],
                  'intellect':row['intellect'],
                  'strength':row['strength'],
                  'morality':row['morality'],
                  'lord_id': row['lord_id'],
                   }) for row in result]
        
    def isInProgress(self, lordId):
        query = '''select build_at, b.name, b.level
                   from game.build_in_progress bip
                   join game.buildings b on b.id = bip.building_id
                   join game.towns t on t.id = bip.town_id
                   where lord_id = %s'''
        self.cur.execute(query, (lordId,))
        data = self.cur.fetchone()
        if not data:
            return False
        else:
            return 'Сейчас уже строится здание %s уровня %s! Подождите до %s' % \
                (data['name'], data['level'], data['build_at'].strftime('%d/%m/%y %H:%M:%S'))         
        
        
