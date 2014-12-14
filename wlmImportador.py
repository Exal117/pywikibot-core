#!/usr/bin/python
# -*- coding: utf-8 -*-
import pwb
import pywikibot
import sys
import codecs
import json
import re

dictDataString = dict([('commonscat', 'P373'), ('lloc', 'P969'), ('idurl', 'P1600'), ('id', 'P808'), ('lat', 'P625'), ('prot', 'P1586')]) #enllaça a un string 
dicDataItem = dict([('municipi', 'P131'), ('estil', 'P149'), ('arquitecte', 'P84')]) #enllaça a un item
##TO DO:
    #  ('imatge', 'P18')
	#(u'època', 'P571')]
	#(fer P131 = Catalunya i P131 = comarca) # ens cal comarca
	# Altres noms: eliminar "o " (en altres noms)
	
def tractamentDades(repo, item, literal, propietatNom, propietatNumero, monument):
	print "entro"
	if propietatNom == u'id':
		if literal.find("RI") == -1:
			literal = ""
	if propietatNom == u'prot':
		if literal == u'BCIN':
			literal = monument[u'idprot']
		else:
			literal = ""
			print 'Camp prot amb un element no controlat: %s' % (literal)
	if propietatNom == u'lat':
		lon = monument[u'lon']
		if lon:
			literal = literal + ' ' + lon
		else:
			print 'Tenim camp lat pero no camp lon'
	if propietatNom == u'estil':
		literal = re.split(',', literal)
		if len(literal) == 1:
			literal = literal[0]
			if literal == u'Obra popular' or literal == u'obra popular':
				literal = u'Arquitectura popular'
			return literal
		else:
			for index in range(0,len(literal)): #[:-1]:
				lit = literal[index].strip()
				if lit == u'Obra popular' or lit == u'obra popular':
					print "entrosssssss"
					lit = u'Arquitectura popular'
				if not (index == len(literal)-1):
					trySetDataItem(repo, item, lit, propietatNom, propietatNumero)
				else:
					"darrer element"
					literal = lit
	print literal
	return literal
		
	
def SetDataString(repo, item, literal, propietatNom, propietatNumero):
	claim = pywikibot.Claim(repo, propietatNumero) #commonscat
	imported = pywikibot.Claim(repo, u'P143') # importat de
	source = pywikibot.ItemPage(repo, u'Q199693') #wikipedia in catalan
	if source.exists():
		imported.setTarget(source)
		claim.setTarget(literal)
		item.addClaim(claim)
		claim.addSources([imported])

def SetDataItem(repo, item, literal, propietatNom, propietatNumero):
	#if municipi al acabar salta a posar comarca i Catalunya recursiu :D
	claim = pywikibot.Claim(repo, propietatNumero) #commonscat
	imported = pywikibot.Claim(repo, u'P143') # importat de
	source = pywikibot.ItemPage(repo, u'Q199693') #wikipedia in catalan
	if source.exists():
		source.get()
		imported.setTarget(source)
		site = pywikibot.Site("ca", "wikipedia")
		print literal
		page = pywikibot.Page(site, literal)
		if page.exists():
			print page
			itemdesti = pywikibot.ItemPage.fromPage(page) #article
			if itemdesti.exists():
				itemdesti.get()
				claim.setTarget(itemdesti)
				item.addClaim(claim)
				claim.addSources([imported])
			else:
				print "No existeix article %d" % (literal)
			
def trySetDataItem(repo, item, literal, propietatNom, propietatNumero):
	if item.claims: #Si no tens dades al Claims
		if propietatNumero in item.claims:
			trobat = False
			for iterador in item.claims[propietatNumero]:
				it = iterador.getTarget()
				it = it.get()
				if it.get('labels').get('ca') == literal:
					trobat = True
			if not trobat:
				SetDataItem(repo, item, literal, propietatNom, propietatNumero)
			else:
				print u"El %s: %s ja hi és al sistema" % (propietatNom, literal)
		else:
			SetDataItem(repo, item, literal, propietatNom, propietatNumero)
	else:
		SetDataItem(repo, item, literal, propietatNom, propietatNumero)
			
def trySetDataString(repo, item, literal, propietatNom, propietatNumero):
	if item.claims: #Si no tens dades al Claims
		if propietatNumero in item.claims:
			if not (propietatNom == u'lat'):
				trobat = False
				for iterador in item.claims[propietatNumero]:
					if iterador.getTarget() == literal:
						trobat = True
				if not trobat:
					SetDataString(repo, item, literal, propietatNom, propietatNumero)
				else:
					print u"Element %s: %s ja hi és al sistema" % (propietatNom, literal)
			else:
				print u"Element %s: ja hi és al sistema" % (propietatNom)
		else:
			SetDataString(repo, item, literal, propietatNom, propietatNumero)
	else:
		SetDataString(repo, item, literal, propietatNom, propietatNumero)

def ompleItemDades(repo, item, monument):
	for a in monument:
		print "Afegir item %s" % (a)
		if dictDataString.get(a):
			literal = tractamentDades(repo, item, monument[a], a, dictDataString.get(a), monument)
			if literal:
				trySetDataString(repo, item, literal, a, dictDataString.get(a))
		elif dicDataItem.get(a):
			literal = tractamentDades(repo, item, monument[a], a, dicDataItem.get(a), monument)
			if literal:
				trySetDataItem(repo, item, literal, a, dicDataItem.get(a))
		elif a == u'Altresnoms':
			print "Encara no se tractar els altres noms"
		else:
			print "Camp desconegut: %s" % (a)
					
def importarDadesItems(llistatdades):
	site = pywikibot.Site("ca", "wikipedia")
	repo = site.data_repository()
	for monument in llistatdades['llista']:
		page = pywikibot.Page(site, monument['nom']) #desti
		print page
		item = pywikibot.ItemPage.fromPage(page)
		if item.exists():
			print "El monument %s existeix" % monument['nom']
			ompleItemDades(repo, item, monument)
		else:
			print "No existeix el monument %s " % monument['nom']
			item.createitem('Creating item %s [[Wikidata:Notability]]' % (monument['nom']))
			#item.get()
			#print item
			ompleItemDades(repo, item, monument)

def getDades():
	#Cal llegir doc amb els monuments amb f.codecs
	#arxiu = raw_input('Introdueix un arxiu:')
	arxiu = "LlistademonumentsdeSantPerePescador.json"
	try:
		f = codecs.open(arxiu, 'r', 'utf8')
	except (OSError, IOError) as e:
		print u'Problemes per obrir l\'arxiu %s' % arxiu
		exit(0) 
	txt = f.read()
	f.close()
	jsonObject = json.loads(txt)
	return jsonObject
	
def main():
	llistatdades = getDades()
	importarDadesItems(llistatdades)

if __name__ == '__main__':
    main()
