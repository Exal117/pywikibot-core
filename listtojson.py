#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import re
import pywikibot
import json
import unicodedata

def getListsFromList(paginaLlistes):
	lists = re.findall(ur'\*{1,2}[:space:]{0,}(\[{2}Llista [a-zA-Z0-9 \:]+(.*?)\]{2})',paginaLlistes, re.S)
	for l in lists:
		if (len(l) > 0):
			var = l[0]
			var = re.sub(u'\[','',var)
			var = re.sub(u'\]','',var)
			
			getJSONfromPageList(var)
	#exit(0)
			
def getJSONfromPageList(pagename):
	site=pywikibot.Site('ca','wikipedia')
	page = pywikibot.Page(site, u"%s" % pagename)
	pagetext = page.get()
	match = re.search(u'(.*?)\={2} Vegeu també \={2}', pagetext, re.S)
	if (match == None):
		pagetext2 = pagetext
	else:
		pagetext2 = match.group(0)
	if not pagetext2:
		pagetext2 = pagetext
	templates = re.findall(u'\{{2}filera IPA(.*?)\}{2}',pagetext2, re.S)
	if (len(templates) > 0):
		jsonresult = '{"llista":['
		i = 1
		for template in templates:
			attributes = re.findall(u'\|(.*?)\n', template, re.S)
			more_names = ''
			monument_json_string = '{'
			j = 1
			for a in attributes:
				
				if "=" in a:
					key, value = a.split("=",1)
				else:
					key, value = a, ""
				
				key = key.strip()
				value = value.strip()
				
				if '<ref' in value:
					value=re.sub(ur'\<ref(.*?)\<\/ref\>','',value)
				if ('estil' == key):
					if ('<br' in value):
						estil_arquitecte = re.split(ur'\<br +\/\>',value)
						monument_json_string+=('"%s":"%s"') % (key, estil_arquitecte[0].strip())
						if (len(estil_arquitecte) == 2):
							arq = estil_arquitecte[1]
							if ('[' in arq):
								arq = arq.replace('[','')
								arq = arq.replace(']','')
								monument_json_string+=(',"arquitecte":"%s"') % (arq.strip())
					else:
						monument_json_string+=('"%s":"%s"') % (key,value)
				
				elif ('nom' == key):
					main_name = ''
					if (('[' in value) & (',' not in value)):
						# contemplem el cas: Església de [[Besalú]] (per exemple)
						value = re.sub(ur'\[','',value)
						value = re.sub(ur'\]','',value)
						if ('|' in value):
							allnames = re.split(ur'\|', value.strip())
							main_name = allnames[0]
							for index in range(1,len(allnames)):
								more_names+=allnames[index]
								more_names+=';'
						else:
							main_name = value
					else:
						amb_article = re.findall(r'\[{2}(.*?)\]{2}',value);
						if (len(amb_article) > 0):
							# he trobat el nom amb article (és el prioritari)
							if '|' in amb_article[0]:
								allnames = amb_article[0].split('|')#re.split(r'|',)
								main_name = allnames[0]
								for index in range(1,len(allnames)):
									altnames = re.split(ur',(?! [0-9]{1,3})',allnames[index])
									for it in altnames:
										more_names+=it.strip()
										more_names+=';'
										value = re.sub('%s' % it.strip, '',value)
										
							else:
								allnames = re.split(ur',(?! [0-9]{1,3})',value)
								main_name = amb_article[0]
								for index in range(1,len(allnames)):
									altnames = re.split(ur',(?! [0-9]{1,3})',allnames[index])
									for it in altnames:
										more_names+=it.strip()
										more_names+=';'
										value = re.sub('%s'%it.strip, '',value)								
							value = re.sub(ur'\[{2}(.*?)\]{2}','',value)
							
						alternative_names = re.split(ur',(?! [0-9]{1,3})',value)
						
						for ite in range(0,len(alternative_names)):
							attr = alternative_names[ite]
							attr = attr.strip(' ')
							if attr:
								if ('|' in attr):
									different_names = attr.split('|')
									if (main_name == ''):
										value = different_names[0]
									for d in range(1,len(different_names)):
										if (different_names[d] not in more_names):
											more_names+=different_names[d]
											more_names+=';'
								else:
									if (ite == 0):
										if not main_name:
											main_name = attr
										else:									
											if (attr not in more_names):
												more_names+=attr.strip()
												more_names+=';'
									else:
										if (attr not in more_names):
											more_names+=attr.strip()
											more_names+=';'

					monument_json_string+=('"%s":"%s"') % (key, main_name)
				elif ('lat' == key):
					if 'lon' in value:
						# Vol dir que tenim també en la mateixa linia la longitud
						coords = re.split(ur'\|',value)
						monument_json_string+=('"%s":"%s",') % (key, coords[0].strip())
						lon = coords[1].split('=')
						monument_json_string+=('"%s":"%s"') % (lon[0].strip(), lon[1].strip())
					else:
						monument_json_string+=('"%s":"%s"') % (key, value.strip())
					
				else:					
					monument_json_string+=('"%s":"%s"') % (key, value.strip())
				if (j < len(attributes)):
					monument_json_string+=','
					
				j+=1
				
			if more_names:
				monument_json_string+=(',"Altresnoms":"%s"') % (more_names)
			monument_json_string+='}'
			if (i < len(templates)):
				monument_json_string+=','
			jsonresult+=monument_json_string
			i+=1
		jsonresult+=']}'
		nom = pagename.replace(' ','')
		writeJSONintoFile(nom,jsonresult)
		return jsonresult
	else:
		getListsFromList(pagetext2)
		return ''
	
		
	
def writeJSONintoFile(name, jsonstring):
	no_espaces_name = '%s.json' % name.replace(' ','')
	f = open(no_espaces_name,'w')
	try:
		f.write(jsonstring.encode("utf-8"))
		#print 'guardat %s' % name
	except(OSError, IOError) as e:
		print 'Error writring json into file:'
		print e
		exit(0)
		
	f.close()

