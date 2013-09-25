'''
Created on 21.06.2013

@author: Max
'''
import psycopg2
import psycopg2.extras
from time import sleep
from datetime import datetime
from random import randint
from commandprocessor import Hero
from data import DBConnector
connectionString = "dbname=postgres user=game password=Abatta"

class World:
    def __init__(self):
        self.data = DBConnector()
        self.conn = self.data.conn
        self.cur = self.data.cur
        self.lords = []
        self.refreshlordList()
        self.heroes = []
        self.refreshHeroList()
    #-------------------------------------------------------------------------------#    
    def createHero(self, first=False, lord=None):
        # try:
            print('рожаем героя...')
            # hardcode
            limit = 6
            created = False;
            merit_flaw = {}
            flawWeight = 0
            if first:
                query = '''select * from
                            game.merit_flaw
                            where type = '%s' ''' % 'loyal'
                self.cur.execute(query)
                flaw = self.cur.fetchone()
                merit_flaw[flaw['id']] = flaw
                flawWeight = flaw['weight']
            
            meritWeight = 0
            neutrals = 0
            
            queryFlaw = '''select * from
                        game.merit_flaw
                        where weight > 0 
                        and (antipod_id not in (%s)
                            or antipod_id is null)
                        and id not in (%s)
                        order by random()
                        limit 1'''
            queryMerit = '''select * from
                        game.merit_flaw
                        where weight < 0 
                        and (antipod_id not in (%s)
                            or antipod_id is null)
                        and id not in (%s)
                        order by random()
                        limit 1'''
            neutral = '''select * from
                        game.merit_flaw
                        where weight = 0 
                        and (antipod_id not in (%s)
                            or antipod_id is null)
                        and id not in (%s)
                        order by random()
                        limit 1'''

            while not created:
                if flawWeight < limit:
                    keys = ', '.join(str(k) for k in merit_flaw.keys())
                    self.cur.execute(queryFlaw % (keys, keys))
                    flaw = self.cur.fetchone()
                    if flaw:
                        merit_flaw[flaw['id']] = flaw
                        flawWeight += flaw['weight']
                if meritWeight < limit:
                    keys = ', '.join(str(k) for k in merit_flaw.keys())
                    self.cur.execute(queryMerit % (keys, keys))                
                    merit = self.cur.fetchone()
                    if merit:
                        merit_flaw[merit['id']] = merit
                        meritWeight += -merit['weight']    
                        
                if neutrals < 1:
                    keys = ', '.join(str(k) for k in merit_flaw.keys())
                    self.cur.execute(neutral % (keys, keys))
                    neutr = self.cur.fetchone()
                    if neutr:
                        merit_flaw[neutr['id']] = neutr
                        neutrals += 1
                                             
                created = flawWeight >= limit and meritWeight >= limit
            
            print(merit_flaw)
            is_woman = bool(randint(0, 1))
            intellect = randint(5, 20)
            strength = 25 - intellect
            morality = randint(-10, 10)
            merits_flaws = [merit_flaw[m]['id'] for m in merit_flaw]
            location_id = 1  # WARNING! HARDCODE!
            if lord:
                query = '''select l.id from game.locations l
                        join game.towns t on t.loc_id = l.id
                        join game.lords u on u.id = t.lord_id
                        where u.id = %s'''
                print(lord)
                self.cur.execute(query, (lord,))
                location_id = self.cur.fetchone()["id"]
                print('Location - ', location_id)
            
            query = '''INSERT INTO game.heroes(
                                name,  level, intellect, strength, morality, merits_flaws, 
                                location_id, is_woman)
                        VALUES (game.get_new_name(%(is_woman)s),  0, %(intellect)s,
                            %(strength)s, %(morality)s,
                            %(merits_flaws)s, %(location_id)s, %(is_woman)s);'''
            
            self.cur.execute(query, {'intellect': intellect,
                                     'strength': strength,
                                     'morality': morality,
                                     'merits_flaws': merits_flaws,
                                     'location_id': location_id,
                                     'is_woman': is_woman,
                                     })

            self.heroes.append(self.data.getLastHero())
        #=======================================================================
        # except:
        #     print('Родить не удалось!')
        #     self.restartConnection()
        #=======================================================================
            
    #-------------------------------------------------------------------------------#        
    
    def refreshlordList(self):    
        try:
            self.cur.execute("select * from game.lords")
            result = self.cur.fetchall()
            if len(result) > 0:
                self.lords = result
        except:
            print('Reconnection...')
            sleep(5)
            self.restartConnection()
            self.refreshlordList()
            
    def refreshHeroList(self):
        #try:
            self.cur.execute("select * from game.heroes")
            result = self.cur.fetchall()
            if len(result) > 0:
                self.heroes = [Hero(self.data, h) for h in result]
        #except:
        #    print('Reconnection...')
        #    sleep(5)
         #   self.restartConnection()
        #    self.refreshHeroList()             
            
    #-------------------------------------------------------------------------------#                
    def restartConnection(self):
        self.cur.close()
        self.conn.close()
        self.conn = psycopg2.connect(connectionString)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 
            
    #-------------------------------------------------------------------------------# 
    def checkQuests(self):
        query = '''SELECT 
                      lord_quests.id as quest_id,
                      lord_quests.lord_id, 
                      quests.type, 
                      quests.count, 
                      quests.next_quest, 
                      quests.start_message, 
                      quests.progress_message, 
                      quests.end_message, 
                      quests.description, 
                      quests.item,
                      quests.result
                    FROM 
                      game.lord_quests, 
                      game.quests
                    WHERE 
                      lord_quests.quest_id = quests.id;
                    '''
        self.cur.execute(query)
        result = self.cur.fetchall()
        
        for row in result:
            questEnded = False
            if row['type'] == 'build':
                buildings = self.data.getLordBuildingIds(row['lord_id'])
                if row['item'] in buildings:
                    questEnded = True
                    
            if row['type'] == 'hire':
                count = row['count']
                lordId = row['lord_id']
                lordHeroCount = len(self.data.getLordHeroIds(lordId=lordId))
                if lordHeroCount >= count:
                    questEnded = True
                
            if row['type'] == 'find_si':
                lordId = row['lord_id']
                items = self.data.getLordById(lordId)['simple_items']
                if not items:
                    return
                itemToSearch = str(row['item'])
                count = row['count']
                if itemToSearch in items and items[itemToSearch] >= count:     
                    questEnded = True
                              
            if questEnded:
                self.data.messageTolord(row['lord_id'], row['end_message'])
                self.questEnd(row['lord_id'], row['result'])                
                if row['next_quest']:
                    newquest = self.getQuestDetails(row['next_quest'])
                    self.cur.execute('''update game.lord_quests set quest_id = %s where id = %s''',
                                     (row['next_quest'], row['quest_id']))
                    self.data.messageTolord(row['lord_id'], newquest['start_message'])
                else:
                    self.cur.execute('''delete from game.lord_quests where id = %s''',
                                     (row['quest_id'],))                
    
    def questEnd(self, lordId, data):
        if data:
            for res in data:
                result = dict((w.split(':')[0], w.split(':'))[1] for w in res.split(','))
                if result['type'] == 'spawn':
                    if result['item'] == 'hero':
                        i = 0
                        while i < int(result['count']):
                            i += 1
                            first = bool(result['first'])
                            self.createHero(first, lordId)
                            self.conn.commit()
    #-------------------------------------------------------------------------------#     
    def getQuestDetails(self, id):
        self.cur.execute("select * from game.quests where id = %s", (id,))
        return self.cur.fetchone()
        
    def getBuilding(self, id):    
        self.cur.execute("select * from game.buildings where id = %s", (id,))
        return self.cur.fetchone()
    #-------------------------------------------------------------------------------# 
    def buildBuildings(self):
        '''build new or replace old building'''
        query = '''select bip.id as bip_id, bip.building_id, 
                        bip.old_building_id, t.id as town_id,
                        t.name as town_name, u.id as lord_id, b1.name as building_name
                    from game.build_in_progress bip
                    join game.towns t on t.id= bip.town_id
                    join game.lords u on u.id = t.lord_id
                    join game.buildings b1 on bip.building_id = b1.id
                    where build_at <= %s'''
        self.cur.execute(query, (datetime.now(),))
        result = self.cur.fetchall()
        
        for res in result:
            lordId = res['lord_id']
            buildings = self.data.getLordBuildingIds(lordId)
            if res['old_building_id']:
                old = res['old_building_id']
                buildings.remove(old)
            new = res['building_id']
            buildings.append(new)
            query = '''update game.towns
                        set buildings = %s
                        where id = %s'''
            self.cur.execute(query, (buildings, res['town_id']))
            query = '''delete from game.build_in_progress
                        where id = %s'''
            self.cur.execute(query, (res['bip_id'],))
            
            self.data.messageTolord(lordId, 'Постройка здания "%s" в городе %s завершена с отличием!' % 
                                 (res['building_name'], res['town_name']))
            self.data.messageTolord(lordId, 'update_buildings')            
            
            
    #-------------------------------------------------------------------------------#          
    def start(self):
        print('start')
        counter = 0
        while 1:
            deepUpdate = counter == 300
            battleUpdate = (counter % 100 == 0)
            self.buildBuildings()
            self.checkQuests()
            if battleUpdate:
                self.processHeroes(deepUpdate)
            self.conn.commit()
            counter += 1
            if counter == 600:
                counter = 0

    def processHeroes(self, deep = True):
        toUpdate = self.data.getHeroForUpdate()
        
        for hero in self.heroes:
            if hero.id in toUpdate:
                hero.updateHero()
            if hero.isInFight:
                hero.fight()
            elif deep:
                hero.think()

                
if __name__ == '__main__':
    world = World()
    world.start()
    world.cur.close()
    world.conn.close()
