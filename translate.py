'''
Created on 24.06.2013

@author: Max
'''
import re

import psycopg2
import psycopg2.extras

connectionString = "dbname=postgres user=game password=Abatta"

class Translator(object):
    '''
    classdocs
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.conn = psycopg2.connect(connectionString)
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        self.dots = (',','.','!',':',';', '?')
        self.prepositions = ('без', 'ради', 'к', 'в', 'за', 'о', 'близ', 'по', 
                             'за', 'между', 'на', 'вне', 'среди', 'на', 'над', 
                             'в', 'для', 'у', 'о', 'перед', 'по', 'до', 'из-под', 
                             'под', 'под', 'при', 'из', 'из-за', 'про', 'кроме', 
                             'по', 'между', 'сквозь', 'от', 'через')
        self.names = {}
        self.surnames = {}
        #self.prefixes = ('', 'по', 'под', 'за')
        #self.suffixes = ('а','и','о','у','е','ё', '-ка')
        self.endings = ('а','и','о','у','е','ё', 'я', 'ю', 'э', 'ы', 'й', 'ь')
        self.templateEndings = '($|[' + ''.join(self.endings) + '])'
        
        self.getNames() #их не так много, можно хранить в памяти
     
    def getNames(self):
        query = '''select * from game.names'''
        names = {}
        surnames = {}
        self.cur.execute(query)
        for nameDict in self.cur.fetchall():
            name = nameDict['name'].lower()
            if len(name.split(' ')) > 0:
                name = name.split(' ')[-1]
            if name[-1:] in self.endings:
                name = name[:-1]
            name = '^(' + name + ')' + self.templateEndings
            if nameDict['is_surname']:
                surnames[name] = nameDict['name']                 
            else:
                names[name] = nameDict['name']
        self.names = names
        self.surnames = surnames
        
    def translate(self, sentence):
        #remove not necessary things
        #Try to read whole phrase
        sentence = sentence.lower()
        machine_sentence = []
            
        for word in self.dots:
            sentence=sentence.replace('%s' % word, ' ')
        for word in self.prepositions:
            sentence=sentence.replace(' %s ' % word, ' ') 
        sentence = re.sub(' +',' ', sentence)
        
        phrases = []
        #Проверяем совпадения по фразам
        sentence = self.getSomething('phrases', 'phrase', sentence, phrases)

        items = []
        #Проверяем совпадения по итемам (они могут быть построены также, как фразы)
        sentence = self.getSomething('simple_items', 'name_template', sentence, items, True)

        buildings = []

        #Проверяем совпадения по итемам (они могут быть построены также, как фразы)
        sentence = self.getSomething('buildings', 'name_template', sentence, buildings)

        names = []
        surnames = []
        for word in sentence.split(' '):
            #First stage
            word = word.lower()
            print(word)
            self.cur.execute('select * from game.words where %s like word', (word,))
            result = self.cur.fetchone()
            if result:# and not hasPhrase:
                machine_sentence.append(result)
            #namesearch
            for name in self.names.keys():
                if re.match(name, word):
                    print('OK!')
                    names.append(self.names[name])
            for surname in self.surnames.keys():
                print('Test surname ', word, 'with template', surname)
                if re.match(surname, word):
                    print('OK!')
                    surnames.append(self.surnames[surname])
                    
        for name in names:
            for surname in surnames:
                fname = '%s %s' % (name, surname)
                machine_sentence.append({ 'word' : fname,
                                          'machine': fname,
                                          'type': 'name' 
                                         })
                
        for phrase in phrases:
            machine_sentence.append({ 'word' : phrase['phrase'],
                                      'machine': phrase['machine'],
                                      'type': phrase['type']
                                     })
        for item in items:
            machine_sentence.append({ 'word' : item['name'],
                                      'machine': item['id'],
                                      'type': 'item',
                                      'count': int(item['count'])
                                     })

        added = [] #Избавляемся от дубликатов (Таверна, хорошая таверна, к примеру)            
        for building in buildings:
            if building['code'] not in added:
                machine_sentence.append({ 'word' : building['name'],
                                          'machine': building['code'],
                                          'type': 'building'
                                         })     
                added.append(building['code'])                   
            

        print('lexical result: ', machine_sentence)
        return machine_sentence
                        
    def getSomething(self, table, field, sentence, container, needCount=False):
        query = ''
        if needCount:
            query = '''select  COALESCE(substring(%(sentence)s, '(\d+)'||' '||name_template), '1') as count,* from game.''' + table + \
                    ''' where %(sentence)s ~ ''' + field
        else:
            query = '''select * from game.''' + table + \
                    ''' where %(sentence)s ~ ''' + field
        
        print(query  % { 'sentence' : sentence })            
        self.cur.execute(query,{ 'sentence' : sentence })
        result = self.cur.fetchall()
        if result:
            for row in result:
                container.append(row)
                #Избавляемся от названия итема, чтобы не мешала дальнейшему разбору
                sentence = re.sub(row[field], '', sentence)
        return sentence

