'''
Created on 05.08.2013

@author: Max
'''

connectionString = "dbname=postgres user=game password=Abatta"

templateName = '<p class="heroname" onclick="getHero(%(id)s)">%(name)s</p>'
templateHero = '''<li class="heroname" onclick="selectHero(%(id)s)">%(name)s</li>'''
templatePositive = '<p class="positive">%s</p>'
templateNegative = '<p class="negative">%s</p>'
templateNeutral = '<p class="neutral">%s</p>'



# Hero constnts
heroGoPercent = 20
heroGetInfoPercent = 60