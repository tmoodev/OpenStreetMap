import xml.etree.cElementTree as ET
import pprint

dataset = "map.osm"

def count_tags(filename):
    tag_dict = {}
    for event, elem in ET.iterparse(filename):
        if elem.tag not in tag_dict:
            tag_dict[elem.tag] = 1
        else:
            tag_dict[elem.tag] += 1

    return tag_dict

print(count_tags(dataset))

import re

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


def key_type(element, keys):
    """
    Takes in an XML element (<node />, <way />) and a dictionary of keys.
    If the element is a <tag />, its ['k'] attribute is analyzed,
    the dictionary keys and lists are incremented accordingly,
    - lower: valid tags that only contain lowercase letters
    - lower_colon: valid tags that contain lowercase letter with one or more colons in their name
    - problemchars: tags with problematic characters
    - other: tags that don't fall in the previous three categories
    """
    
    if element.tag == 'tag':
        if lower.search(element.attrib['k']):
            keys['lower'] +=1
        elif lower_colon.search(element.attrib['k']):
            keys['lower_colon'] += 1
        elif problemchars.search(element.attrib['k']):
            keys['problemchars'] += 1
        else:
            keys['other'] += 1
    return keys


def process_tags(filename):
    """
    Takes in a dataset in XML format, parses it, and executes the function key_type() for each element.
    Returns a dictionary with the count of different types of keys.
    """
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys

tag_type_dict = process_tags(dataset)
print (tag_type_dict)

def get_problemkeys(filename):
    problemchars_list = []
    for _, element in ET.iterparse(filename):
        if element.tag == 'tag':
            if problemchars.search(element.attrib['k']):
                problemchars_list.append(element.attrib['k'])
    return problemchars_list

print(get_problemkeys(dataset))

from collections import defaultdict

street_type_re = re.compile(r'\S+\.?$', re.IGNORECASE)
street_types = defaultdict(int)

def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        street_types[street_type] += 1

def print_sorted_dict(d, expression):
    keys = d.keys()
    keys = sorted(keys, key=lambda s: s.lower())
    for k in keys:
        v = d[k]
        print (expression % (k, v))

def is_street_name(elem):
    return (elem.tag == "tag") and (elem.attrib['k'] == "addr:street")

def audit(filename):
    for event, elem in ET.iterparse(filename):
        if is_street_name(elem):
            audit_street_type(street_types, elem.attrib['v'])
    print(street_types, "%s: %d")
    return(street_types)

all_types = audit(dataset)
all_types

expected = ['Artery', 'Alley', 'Avenue', 'Boulevard', 'Broadway', 'Commons', 'Court', 'Drive', 'Lane', 'Park', 'Parkway',
            'Place', 'Road', 'Square', 'Street', 'Terrace', 'Trail', 'Turnpike', 'Wharf',
            'Yard']

abbr_mapping = { 'Ave': 'Avenue',
                  'Ave.': 'Avenue',
                  'AVENUE': 'Avenue',
                  'ave': 'Avenue',
                  'avenue': 'Avenue',
                  'St': 'Street',
                  'BLVD': 'Boulevard',
                  'Blvd': 'Boulevard',
                  'Blvd.': 'Boulevard',
                  'Rd': 'Road',
                  'S': 'South',                  
                  'N': 'North'
                }

typo_full_names = {}

def audit_street_name(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if (all_types[street_type] < 20) and (street_type not in expected) and (street_type not in abbr_mapping):
            if street_type in typo_full_names:
                typo_full_names[street_type].append(street_name)
            else:
                typo_full_names.update({ street_type:[street_name] })

def audit_name(filename):
    for event, elem in ET.iterparse(filename):
        if is_street_name(elem):
            audit_street_name(street_types, elem.attrib['v'])    
    # print_sorted_dict(street_types)
    return typo_full_names

audit_name(dataset)

expected.extend(['Alley', 'West', 'East', 'Way'])

typo_mapping = { 'Broadway A': 'Broadway',
                 'Dea': 'Deaderick Street',
                 'Davidson': 'Davidson Street',
                 'Seaboard Ln Ste E106': {'Seaboard Lane': 'Suite E106'},
                 'Village at Vandy': 'Village at Vandy Square',
                 'Nolensville': 'Nolensville Pike',
                 "Children's Way": 'Childrens Way'
                
               }

numbers_mapping = {'#118': {'4th Avenue South': 'Suite 118'},
                    '1305': {''},
                    '263': {'Houston Street': 'Suite 263'}
                  }

expected = sorted(expected)
expected

name_problem_chars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\t\r\n]')

def get_problem_names(filename):
    problemchars_list = []
    for _, element in ET.iterparse(filename):
        if is_street_name(element):
            if name_problem_chars.search(element.attrib['v']):
                problemchars_list.append(element.attrib['v'])
    return problemchars_list

print(get_problem_names(dataset))
problemchars_list = []

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

OSM_PATH = "map.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node':
        node_attribs['id'] = element.attrib['id']
        node_attribs['user'] = element.attrib['user']
        node_attribs['uid'] = element.attrib['uid']
        node_attribs['version'] = element.attrib['version']
        node_attribs['lat'] = element.attrib['lat']
        node_attribs['lon'] = element.attrib['lon']
        node_attribs['timestamp'] = element.attrib['timestamp']
        node_attribs['changeset'] = element.attrib['changeset']
        
        for node in element:
            tag_dict = {}
            tag_dict['id'] = element.attrib['id']
            if ':' in node.attrib['k']:
                tag_dict['type'] = node.attrib['k'].split(':', 1)[0]
                tag_dict['key'] = node.attrib['k'].split(':', 1)[-1]
                tag_dict['value'] = node.attrib['v'].split(':', 1)[0]
            else:
                tag_dict['type'] = 'regular'
                tag_dict['key'] = node.attrib['k']
                tag_dict['value'] = node.attrib['v']
            tags.append(tag_dict)
            
    elif element.tag == 'way':
        way_attribs['id'] = element.attrib['id']
        way_attribs['user'] = element.attrib['user']
        way_attribs['uid'] = element.attrib['uid']
        way_attribs['version'] = element.attrib['version']
        way_attribs['timestamp'] = element.attrib['timestamp']
        way_attribs['changeset'] = element.attrib['changeset']
        n = 0
        for node in element:
            if node.tag == 'nd':
                way_dict = {}
                way_dict['id'] = element.attrib['id']
                way_dict['node_id'] = node.attrib['ref']
                way_dict['position'] = n
                n += 1
                way_nodes.append(way_dict)
            if node.tag == 'tag':
                tag_dict = {}
                tag_dict['id'] = element.attrib['id']
                if ':' in node.attrib['k']:
                    tag_dict['type'] = node.attrib['k'].split(':', 1)[0]
                    tag_dict['key'] = node.attrib['k'].split(':', 1)[-1]
                    tag_dict['value'] = node.attrib['v'].split(':', 1)[0]
                else:
                    tag_dict['type'] = 'regular'
                    tag_dict['key'] = node.attrib['k']
                    tag_dict['value'] = node.attrib['v']
                tags.append(tag_dict)

    if element.tag == 'node':
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)
    
    import sqlite3

# Creating database on disk
sqlite_file = 'nashville.db'
conn = sqlite3.connect(sqlite_file)
conn.text_factory = str
c = conn.cursor()

c.execute('''DROP TABLE IF EXISTS nodes''')
c.execute('''DROP TABLE IF EXISTS nodes_tags''')
c.execute('''DROP TABLE IF EXISTS ways''')
c.execute('''DROP TABLE IF EXISTS ways_tags''')
c.execute('''DROP TABLE IF EXISTS ways_nodes''')
conn.commit()

QUERY_NODES = """
CREATE TABLE nodes (
    id INTEGER NOT NULL,
    lat REAL,
    lon REAL,
    user TEXT,
    uid INTEGER,
    version INTEGER,
    changeset INTEGER,
    timestamp TEXT
);
"""

QUERY_NODES_TAGS = """
CREATE TABLE nodes_tags (
    id INTEGER,
    key TEXT,
    value TEXT,
    type TEXT,
    FOREIGN KEY (id) REFERENCES nodes(id)
);
"""

QUERY_WAYS = """
CREATE TABLE ways (
    id INTEGER NOT NULL,
    user TEXT,
    uid INTEGER,
    version INTEGER,
    changeset INTEGER,
    timestamp TEXT
);
"""

QUERY_WAYS_TAGS = """
CREATE TABLE ways_tags (
    id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    type TEXT,
    FOREIGN KEY (id) REFERENCES ways(id)
);
"""

QUERY_WAYS_NODES = """
CREATE TABLE ways_nodes (
    id INTEGER NOT NULL,
    node_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    FOREIGN KEY (id) REFERENCES ways(id),
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);
"""



c.execute(QUERY_NODES)
c.execute(QUERY_NODES_TAGS)
c.execute(QUERY_WAYS)
c.execute(QUERY_WAYS_TAGS)
c.execute(QUERY_WAYS_NODES)

conn.commit()

with open('nodes.csv','rt') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db1 = [(i['id'], i['lat'], i['lon'], i['user'], i['uid'], i['version'], i['changeset'], i['timestamp']) for i in dr]
    
with open('nodes_tags.csv','rt') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db2 = [(i['id'], i['key'], i['value'], i['type']) for i in dr]
    
with open('ways.csv','rt') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db3 = [(i['id'], i['user'], i['uid'], i['version'], i['changeset'], i['timestamp']) for i in dr]
    
with open('ways_tags.csv','rt') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db4 = [(i['id'], i['key'], i['value'], i['type']) for i in dr]
    
with open('ways_nodes.csv','rt') as fin:
    dr = csv.DictReader(fin) # comma is default delimiter
    to_db5 = [(i['id'], i['node_id'], i['position']) for i in dr]
    
c.executemany("INSERT INTO nodes(id, lat, lon, user, uid, version, changeset, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?);", to_db1)
c.executemany("INSERT INTO nodes_tags(id, key, value, type) VALUES (?, ?, ?, ?);", to_db2)
c.executemany("INSERT INTO ways(id, user, uid, version, changeset, timestamp) VALUES (?, ?, ?, ?, ?, ?);", to_db3)
c.executemany("INSERT INTO ways_tags(id, key, value, type) VALUES (?, ?, ?, ?);", to_db4)
c.executemany("INSERT INTO ways_nodes(id, node_id, position) VALUES (?, ?, ?);", to_db5)
conn.commit()

c.execute('SELECT COUNT(*) FROM nodes')
all_rows = c.fetchall()
print(all_rows)

c.execute('SELECT COUNT(*) FROM ways')
all_rows = c.fetchall()
print(all_rows)

QUERY = '''
SELECT ways_tags.value, COUNT(*)
FROM ways_tags
WHERE ways_tags.key = 'name'
AND ways_tags.type = 'regular'
GROUP BY ways_tags.value
ORDER BY COUNT(*) DESC
LIMIT 10;
'''

c.execute(QUERY)
all_rows = c.fetchall()
print(all_rows)

QUERY = '''
SELECT AVG(Count)
FROM
    (SELECT COUNT(*) as Count
    FROM ways
    JOIN ways_nodes
    ON ways.id = ways_nodes.id
    GROUP BY ways.id);
'''

c.execute(QUERY)
all_rows = c.fetchall()
print(all_rows)

QUERY = '''
SELECT value, COUNT(*) as Count
FROM nodes_tags
WHERE key='amenity'
GROUP BY value
ORDER BY Count DESC
LIMIT 10;
'''

c.execute(QUERY)
all_rows = c.fetchall()
print(all_rows)

QUERY = '''
SELECT COUNT(*) FROM nodes;
'''

c.execute(QUERY)
all_rows = c.fetchall()
print(all_rows)

QUERY = '''
SELECT COUNT(*) FROM ways;
'''

c.execute(QUERY)
all_rows = c.fetchall()
print(all_rows)

QUERY = '''
SELECT COUNT(DISTINCT(e.uid))
FROM (SELECT uid FROM nodes UNION ALL SELECT uid FROM ways) e;
'''

c.execute(QUERY)
all_rows = c.fetchall()
print(all_rows)

QUERY = '''
SELECT e.user, COUNT(*) as num
FROM (SELECT user FROM nodes UNION ALL SELECT user FROM ways) e
GROUP BY e.user
ORDER BY num DESC
LIMIT 10;
'''

c.execute(QUERY)
all_rows = c.fetchall()
print(all_rows)
