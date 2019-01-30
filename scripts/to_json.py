import sys
from pathlib import Path
from bs4 import BeautifulSoup
import datetime
import json


import pprint
pp = pprint.PrettyPrinter(indent=4)


def parse_keywords_list(path_to_file):
	keywords_dict = {}
	with path_to_file.open(mode='r') as keywords_file:
			keywords_soup = BeautifulSoup(keywords_file, 'lxml-xml')
			for keywords_list in keywords_soup.find_all("list"):
				keywords_dict[keywords_list['type']] = {}
				for item in keywords_list.find_all("item"):
					keywords_dict[keywords_list['type']][item['xml:id']] = item.text

			return keywords_dict

def main():
	dep_base_dir = Path(sys.argv[1])

	Path('./converted_json').mkdir(exist_ok=True) 
	converted_files_path = Path('./converted_json')
	
	keywords_dict = parse_keywords_list(dep_base_dir / 'keywords.xml')

	xml = dep_base_dir.glob("**/dep_8*.xml")

	depositions_parsed = []

	for xml_path in sorted(list(xml)):
		print(xml_path)
		with xml_path.open(mode='r') as xml_file:
			tei_soup = BeautifulSoup(xml_file, 'lxml-xml')
			
			deposition_dict = {}

			deposition_dict['filename'] = str(xml_path.resolve().stem + '.xml')


			title_node = tei_soup.find('title')
			if title_node and len(title_node.contents[0].strip()) > 0:
				deposition_dict['title'] = title_node.contents[0]
			
			creation_node = tei_soup.find('creation')
			
			if creation_node.date.has_attr('when'):
				deposition_dict['creation_date'] = creation_node.date['when'].replace('_','-').strip()

			place_dict = {}

			for j in creation_node.placeName.find_all(recursive=False):
				# print(j.name, j.contents)
				place_dict[j.name] = " ".join(j.contents)
			
			deposition_dict['creation_place'] = place_dict

			for keywords_node in tei_soup.find_all('keywords'):
				list_node = keywords_node.list
				keywords_list = []
				list_type = list_node['type']
				for include_node in list_node.find_all('xi:include'):
					if include_node['xpointer'] in keywords_dict[list_type]:
						keywords_list.append(keywords_dict[list_type][include_node['xpointer']])
				if len(keywords_list) > 0:
					deposition_dict[list_type] = keywords_list


			people_list = []
			list_person_node = tei_soup.find('listPerson')
			for person_node in list_person_node.find_all('person'):
				person_dict = {}
				person_dict['role'] = person_node.roleName['type']
				if person_node.forename and len(person_node.forename.contents) > 0:
					person_dict['forename'] = person_node.forename.contents[0]
				if person_node.surname and len(person_node.surname.contents) > 0:
					person_dict['surname'] = person_node.surname.contents[0]
				if person_node.occupation and len(person_node.occupation.contents) > 0:
					person_dict['occupation'] = person_node.occupation.contents[0]
				person_dict['sex'] = person_node['sex']

				if person_node.residence:
					residence_dict = {}
					for j in person_node.residence.find_all(recursive=False):
						residence_dict[j.name] = " ".join(j.contents)
					person_dict['residence'] = residence_dict

				people_list.append(person_dict)

			deposition_dict['people_list'] = people_list
			deposition_dict['participants_number'] = len(people_list)

			signed_list = []
			for signed_node in tei_soup.find_all('signed'):
				signed_dict = {}
				signed_dict['role'] = signed_node.roleName['type']
				signed_dict['name'] = signed_node.find('name').string
				signed_list.append(signed_dict)

			if len(signed_list) > 0:
				deposition_dict['signed_by'] = signed_list

			with (converted_files_path / (xml_path.resolve().stem + '.json')).open(mode='w') as outfile:
				json.dump(deposition_dict, outfile)


			depositions_parsed.append(deposition_dict)

	
	with (converted_files_path / 'all_depositions.json').open(mode='w') as outfile:
		json.dump(depositions_parsed, outfile)
			





if __name__ == "__main__":
	if len(sys.argv) < 2: 
		print('Invalid number of arguments. Please provide the path to the root folder of the 1641 Depositions XML')
		exit(0)
	else:
		main()