# Open StreetMap Data Case Study

## Map Area
### Nashville, TN, United States

#### https://www.openstreetmap.org/#map=13/36.1154/-86.8430

##### I am interested in wrangling and cleaning OpenStreetMap data. Nashville, TN is my hometown and this neighborhood is of a particular interest to me. I explored the dataset, cleaned the XML data, exported it to a CSV file and loaded it into a SQL database.

## Exploring the Data

#### I parsed through the Nashville dataset with ElementTree to discover the number of unique element types.


```python
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
```

    {'node': 226056, 'member': 19394, 'nd': 283605, 'tag': 116507, 'bounds': 1, 'note': 1, 'meta': 1, 'relation': 453, 'way': 32604, 'osm': 1}


## Problems with the Data

#### The data we acquired the OpenStreetMap is crowd-sourced, so there are some inconsistencies we need to account for. All elements won't share the same formatting (e.g. upper-case, lower-case) and some characters will cause problems with code syntax (e.g. colons). Here, I compare elements to a dictionary of keys. If the element is tagged, then its attribute 'k' is analyzed to look for these problem characters. It will then show us how many potential issues will have in each category.


```python
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
```

    {'problemchars': 1, 'lower': 82683, 'other': 2148, 'lower_colon': 31675}


#### There is one potential tag that has problematic characters. Below is a function that will return our problematic key.


```python
def get_problemkeys(filename):
    problemchars_list = []
    for _, element in ET.iterparse(filename):
        if element.tag == 'tag':
            if problemchars.search(element.attrib['k']):
                problemchars_list.append(element.attrib['k'])
    return problemchars_list

print(get_problemkeys(dataset))
```

    ['The Stahlman']


#### No concerns with one space.

## Auditing the Data

#### Now, let's take a look at the data to see what unique street types it contains.


```python
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
```

    (defaultdict(<type 'int'>, {'1305': 1, 'Boulevard': 10, 'Court': 15, 'West': 1, 'Rd': 2, 'Way': 1, '#118': 1, 'BLVD': 2, 'ave': 1, 'East': 1, 'AVENUE': 3, 'Davidson': 1, 'North': 71, 'avenue': 1, 'E106': 1, 'Vandy': 1, 'South': 131, 'A': 1, 'Pike': 27, 'Lane': 33, 'Drive': 36, 'St': 1, '263': 1, 'S': 3, 'Place': 23, 'Ave': 1, 'Dea': 1, 'Parkway': 4, 'N': 3, 'Road': 11, 'Blvd.': 1, 'Nolensville': 1, 'Alley': 4, 'Street': 164, 'Blvd': 1, 'Broadway': 36, 'Avenue': 128}), '%s: %d')





    defaultdict(int,
                {'#118': 1,
                 '1305': 1,
                 '263': 1,
                 'A': 1,
                 'AVENUE': 3,
                 'Alley': 4,
                 'Ave': 1,
                 'Avenue': 128,
                 'BLVD': 2,
                 'Blvd': 1,
                 'Blvd.': 1,
                 'Boulevard': 10,
                 'Broadway': 36,
                 'Court': 15,
                 'Davidson': 1,
                 'Dea': 1,
                 'Drive': 36,
                 'E106': 1,
                 'East': 1,
                 'Lane': 33,
                 'N': 3,
                 'Nolensville': 1,
                 'North': 71,
                 'Parkway': 4,
                 'Pike': 27,
                 'Place': 23,
                 'Rd': 2,
                 'Road': 11,
                 'S': 3,
                 'South': 131,
                 'St': 1,
                 'Street': 164,
                 'Vandy': 1,
                 'Way': 1,
                 'West': 1,
                 'ave': 1,
                 'avenue': 1})



### Items to Address
- Abbreviations
- Suites
- Misspelled street names

### Addressing Abbreviations

#### Below is the definition of a dictionary of valid street types and corrections to implement.


```python
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
```

#### Below, i will print some of the problematic names.


```python
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
```




    {'#118': ['4th Ave S #118'],
     '1305': ['1305'],
     '263': ['Houston Street, Suite 263'],
     'A': ['Broadway A'],
     'Davidson': ['Davidson'],
     'Dea': ['Dea'],
     'E106': ['Seaboard Ln Ste E106'],
     'East': ['Music Square East'],
     'Nolensville': ['Nolensville'],
     'Vandy': ['Village at Vandy'],
     'Way': ["Children's Way"],
     'West': ['Music Square West']}



- Way needs to be added to the dictionary of expected street endings.
- Suite numbers need to be addressed.
- Davidson is the name of a street.
- 'Dea' is an abbreviation for Deadrick Street
- 'Village at Vandy' is on the Vanderbilt campus
- Music Square East and West are actual street names
- Nolensville should be Nolensville Pike

### Addressing Suites and Other Updates


```python
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
```




    ['Alley',
     'Alley',
     'Artery',
     'Avenue',
     'Boulevard',
     'Broadway',
     'Commons',
     'Court',
     'Drive',
     'East',
     'Lane',
     'Park',
     'Parkway',
     'Place',
     'Road',
     'Square',
     'Street',
     'Terrace',
     'Trail',
     'Turnpike',
     'Way',
     'West',
     'Wharf',
     'Yard']



#### Below are street names that may contain problematic characters:


```python
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
```

    ["Children's Way", '4th Ave S #118', 'Houston Street, Suite 263']


## Using the provisional data.py file to parse and create csv files for our SQL database


```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
After auditing is complete the next step is to prepare the data to be inserted into a SQL database.
To do so you will parse the elements in the OSM XML file, transforming them from document format to
tabular format, thus making it possible to write to .csv files.  These csv files can then easily be
imported to a SQL database as tables.

The process for this transformation is as follows:
- Use iterparse to iteratively step through each top level element in the XML
- Shape each element into several data structures using a custom function
- Utilize a schema and validation library to ensure the transformed data is in the correct format
- Write each data structure to the appropriate .csv files

We've already provided the code needed to load the data, perform iterative parsing and write the
output to csv files. Your task is to complete the shape_element function that will transform each
element into the correct format. To make this process easier we've already defined a schema (see
the schema.py file in the last code tab) for the .csv files and the eventual tables. Using the 
cerberus library we can validate the output against this schema to ensure it is correct.

## Shape Element Function
The function should take as input an iterparse Element object and return a dictionary.

### If the element top level tag is "node":
The dictionary returned should have the format {"node": .., "node_tags": ...}

The "node" field should hold a dictionary of the following top level node attributes:
- id
- user
- uid
- version
- lat
- lon
- timestamp
- changeset
All other attributes can be ignored

The "node_tags" field should hold a list of dictionaries, one per secondary tag. Secondary tags are
child tags of node which have the tag name/type: "tag". Each dictionary should have the following
fields from the secondary tag attributes:
- id: the top level node id attribute value
- key: the full tag "k" attribute value if no colon is present or the characters after the colon if one is.
- value: the tag "v" attribute value
- type: either the characters before the colon in the tag "k" value or "regular" if a colon
        is not present.

Additionally,

- if the tag "k" value contains problematic characters, the tag should be ignored
- if the tag "k" value contains a ":" the characters before the ":" should be set as the tag type
  and characters after the ":" should be set as the tag key
- if there are additional ":" in the "k" value they and they should be ignored and kept as part of
  the tag key. For example:

  <tag k="addr:street:name" v="Lincoln"/>
  should be turned into
  {'id': 12345, 'key': 'street:name', 'value': 'Lincoln', 'type': 'addr'}

- If a node has no secondary tags then the "node_tags" field should just contain an empty list.

The final return value for a "node" element should look something like:

{'node': {'id': 757860928,
          'user': 'uboot',
          'uid': 26299,
       'version': '2',
          'lat': 41.9747374,
          'lon': -87.6920102,
          'timestamp': '2010-07-22T16:16:51Z',
      'changeset': 5288876},
 'node_tags': [{'id': 757860928,
                'key': 'amenity',
                'value': 'fast_food',
                'type': 'regular'},
               {'id': 757860928,
                'key': 'cuisine',
                'value': 'sausage',
                'type': 'regular'},
               {'id': 757860928,
                'key': 'name',
                'value': "Shelly's Tasty Freeze",
                'type': 'regular'}]}

### If the element top level tag is "way":
The dictionary should have the format {"way": ..., "way_tags": ..., "way_nodes": ...}

The "way" field should hold a dictionary of the following top level way attributes:
- id
-  user
- uid
- version
- timestamp
- changeset

All other attributes can be ignored

The "way_tags" field should again hold a list of dictionaries, following the exact same rules as
for "node_tags".

Additionally, the dictionary should have a field "way_nodes". "way_nodes" should hold a list of
dictionaries, one for each nd child tag.  Each dictionary should have the fields:
- id: the top level element (way) id
- node_id: the ref attribute value of the nd tag
- position: the index starting at 0 of the nd tag i.e. what order the nd tag appears within
            the way element

The final return value for a "way" element should look something like:

{'way': {'id': 209809850,
         'user': 'chicago-buildings',
         'uid': 674454,
         'version': '1',
         'timestamp': '2013-03-13T15:58:04Z',
         'changeset': 15353317},
 'way_nodes': [{'id': 209809850, 'node_id': 2199822281, 'position': 0},
               {'id': 209809850, 'node_id': 2199822390, 'position': 1},
               {'id': 209809850, 'node_id': 2199822392, 'position': 2},
               {'id': 209809850, 'node_id': 2199822369, 'position': 3},
               {'id': 209809850, 'node_id': 2199822370, 'position': 4},
               {'id': 209809850, 'node_id': 2199822284, 'position': 5},
               {'id': 209809850, 'node_id': 2199822281, 'position': 6}],
 'way_tags': [{'id': 209809850,
               'key': 'housenumber',
               'type': 'addr',
               'value': '1412'},
              {'id': 209809850,
               'key': 'street',
               'type': 'addr',
               'value': 'West Lexington St.'},
              {'id': 209809850,
               'key': 'street:name',
               'type': 'addr',
               'value': 'Lexington'},
              {'id': '209809850',
               'key': 'street:prefix',
               'type': 'addr',
               'value': 'West'},
              {'id': 209809850,
               'key': 'street:type',
               'type': 'addr',
               'value': 'Street'},
              {'id': 209809850,
               'key': 'building',
               'type': 'regular',
               'value': 'yes'},
              {'id': 209809850,
               'key': 'levels',
               'type': 'building',
               'value': '1'},
              {'id': 209809850,
               'key': 'building_id',
               'type': 'chicago',
               'value': '366409'}]}
"""

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

```


```python
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
```


```python
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
```


```python
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
```


```python
c.executemany("INSERT INTO nodes(id, lat, lon, user, uid, version, changeset, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?);", to_db1)
c.executemany("INSERT INTO nodes_tags(id, key, value, type) VALUES (?, ?, ?, ?);", to_db2)
c.executemany("INSERT INTO ways(id, user, uid, version, changeset, timestamp) VALUES (?, ?, ?, ?, ?, ?);", to_db3)
c.executemany("INSERT INTO ways_tags(id, key, value, type) VALUES (?, ?, ?, ?);", to_db4)
c.executemany("INSERT INTO ways_nodes(id, node_id, position) VALUES (?, ?, ?);", to_db5)
conn.commit()
```

## Verify insertion into the database

#### At the beginning of the project, the osm file contained {'node': 226056, 'member': 19394, 'nd': 283605, 'tag': 116507, 'bounds': 1, 'note': 1, 'meta': 1, 'relation': 453, 'way': 32604, 'osm': 1}. Below is a SQL query that verifies that our database cooresponds to the original file.



```python
c.execute('SELECT COUNT(*) FROM nodes')
all_rows = c.fetchall()
print(all_rows)

c.execute('SELECT COUNT(*) FROM ways')
all_rows = c.fetchall()
print(all_rows)
```

    [(226056,)]
    [(32604,)]


### What are the top 10 streets that contain the most nodes?


```python
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
```

    [('Nashville Terminal Subdivision', 56), ('Rosa L Parks Boulevard', 45), ('Charlotte Avenue', 34), ('Four-Forty Parkway', 33), ('James Robertson Parkway', 31), ('4th Avenue South', 27), ('8th Avenue South', 25), ('West End Avenue', 23), ('Richland Creek Greenway', 21), ('Lafayette Street', 21)]


### What is the average number of nodes contained in a way?


```python
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
```

    [(8.698472580051527,)]


### What are the top 10 amenities in Nashville?


```python
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
```

    [('place_of_worship', 346), ('restaurant', 126), ('school', 79), ('bench', 60), ('fast_food', 52), ('bar', 51), ('cafe', 32), ('fuel', 25), ('parking_entrance', 21), ('parking', 17)]


### Number of Nodes


```python
QUERY = '''
SELECT COUNT(*) FROM nodes;
'''

c.execute(QUERY)
all_rows = c.fetchall()
print(all_rows)
```

    [(226056,)]


### Number of Ways


```python
QUERY = '''
SELECT COUNT(*) FROM ways;
'''

c.execute(QUERY)
all_rows = c.fetchall()
print(all_rows)
```

    [(32604,)]


### Number of Unique Users


```python
QUERY = '''
SELECT COUNT(DISTINCT(e.uid))
FROM (SELECT uid FROM nodes UNION ALL SELECT uid FROM ways) e;
'''

c.execute(QUERY)
all_rows = c.fetchall()
print(all_rows)
```

    [(877,)]


### Top 10 Contibutors


```python
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
```

    [('Gedwards724', 101230), ('wward', 44154), ('woodpeck_fixbot', 6743), ('ChesterKiwi', 5319), ('greggerm', 4813), ('JessAk71', 2840), ('Adam Martin', 2753), ('MikeGabrys', 2330), ('42429', 2276), ('Rub21', 2122)]


## Review of Project

- I wrangled OpenStreetMap data for Nashville, TN as a json/osm file.
- I cleaned the data of any problematic characters, resolved abbreviations, and other typographical errors in the data.
- I used the provided data.py file to export the data into CSVs.
- I used those csvs to create a SQL database.
- I queried the data to answer questions about Nashville.
- I provided an overview of the data and additional ideas for exploring the data.

## Additional Ideas

- Use the data to identify popular areas for food and entertainment.
- Additional cleaning could be done regarding zipcodes, other misplaced information, etc.


```python

```
