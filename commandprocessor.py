'''
Created on 02.07.2013

@author: Max
'''
import psycopg2
import urllib.parse;
from translate import Translator
from datetime import datetime
from psycopg2.extras import Json
from constants import *
from data import *
                       
class CommandProcessor(object):
    def __init__(self):
        self.t = Translator();
        self.data = DBConnector()

    
    def getResponseHero(self, word):
        # hardcode: later I want to realize whis in database
        if word == 'build':
            return Resp('answer', 'Я вам не стройщик! Я герой, я геройствоват умею. Строить не умею, ваще никак!')
        else:
            return  Resp('answer', 'Чиво?')
        
    def processCommand(self, lord_name, text, forwho='town'):
        result = []
        translated = self.t.translate(text)
        verbs = []
        nouns = []
        misc = []
        phrases = []
        names = []
        buildings = []
        items = []
        
        for word in translated:
            if word['type'] == 'verb':
                verbs.append(word['machine'])
            elif word['type'] == 'noun':
                nouns.append(word['machine'])
            elif word['type'] == 'misc':
                misc.append(word['machine'])
            elif word['type'] == 'phra':
                phrases.append(word['machine'])
            elif word['type'] == 'name':
                names.append(word['machine'])
            elif word['type'] == 'building':
                buildings.append(word['machine'])
            elif word['type'] == 'item':
                items.append((word['machine'], word['count']))
                
        lord = self.data.getLord(lord_name)

            
        for miscword in misc:
            result.append(Resp('answer' , self.data.getResponse(miscword)))
            
        for phrase in phrases:
            self.data.getPhraseResponse(result, phrase, lord, names, forwho)
        
        for verb in verbs:
            if verb == 'build':
                answer = ''
                if forwho != 'town':
                    result.append(self.data.getResponseHero(verb))
                    continue  # Герои строить не умеют!
                for building in buildings:
                    answer = self.data.build(building, lord)
                    if answer[0] == 'ok':
                        result.append(Resp('answer' , self.data.getResponse(verb)))
                    elif answer[0] == 'error':
                        result.append(Resp('answer' , answer[1]))
                if answer == '':
                    result.append(Resp('answer' , 'А чего строить-то? Моя как-то так и не понимай!'))
                    
            elif verb == 'find':
                if forwho == 'town':
                    result.append(Resp('answer', 'Мне и не приказывайте искать - для этого герои есть!'))
                else:
                    answer = ''
                    itemsToSearch = []
                    for item in items:
                        count = item[1]
                        itemId = item[0]
                        itemsToSearch.append({'itemId':itemId, 'count':count})
                                              
                    answer = self.data.setQuest(lord['id'], forwho, 'find', itemsToSearch)
                    result.append(Resp(answer[0], answer[1]))
                
                    
            elif verb == 'hire':
                if len(names) == 1:  # All is ok
                    result.append(Resp('answer' , self.data.hire(names[0], lord['id'])))
                    result.append(Resp('update' , 'hero'))
                elif len(names) > 1:
                    print(names)
                    result.append(Resp('answer' , 'Определитесь, какого героя хотите нанять!'))
                else:
                    result.append(Resp('answer' , 'Кого-кого вы хотите нанять?'))
            
        if len(result) == 0:
            return [Resp('answer' , 'Господин, моя твоя не понимай, сколько уши не чисти')]
        else:
            if forwho != 'town':
                self.data.cur.execute('''update game.heroes set updated = True where id = %s''', (int(forwho),))
            return result
    


if __name__ == '__main__':
    cp = CommandProcessor()
    a = cp.createHero()
