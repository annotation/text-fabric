import os
import sys
import subprocess
import collections

from .mylib import *

class Etcbc:
    ''' Knows the ETCBC data format.

    All ETCBC knowledge is stored in a file that describes objects, features and values.
    These are many items, and we divide them in parts and subparts.
    We have a parts for monads, sections and linguistic objects.
    When we generate LAF files, they may become unwieldy in size.
    That is why we also divide parts in subparts.
    Parts correspond to sets of objects and their features.
    Subparts correspond to subsets of objects and or subsets of features.
    N.B. It is "either or": 
    either 

    * a part consists of only one object type, and the subparts
      divide the features of that object type

    or

    * a part consists of multiple object types, and the subparts
      divide the object types of that part. If an object type belongs to
      a subpart, all its features belong to that subpart too.

    In our case, the part 'monad' has the single object type word, and its features
    are divided over subparts.
    The part 'lingo' has object types sentence, sentence_atom, clause, clause_atom,
    phrase, phrase_atom, subphrase, word. Its subparts are a partition of these object
    types in several subsets.
    The part 'section' does not have subparts.
    Note that an object type may occur in multiple parts: consider 'word'.
    However, 'word' in part 'monad' has all non-relational word features, but 'word' in part 'lingo'
    has only relational features, i.e.features that relate words to other objects.

    The Etcbc object stores the complete information found in the Etcbc config file
    in a bunch of data structures, and defines accessor functions for it.

    The feature information is stored in the following dictionaries:

    (Ia) part_info[part][subpart][object_type] = set of feature_names
        NB: object_types may occur in multiple parts.

    (Ib) part_object[part] = set of object_types
    
    (Ic) part_feature[part][object_type] = set of feature_names
    
    (Id) object_subpart[part][object_type] = subpart
    
        Stores the subpart in which each object type occurs, per part

    (II) object_info[object_type] = [attributes]
    
        Stores the information on objects, except their features and values.

    (III) feature_info[object_type][feature_name] = [attributes]
    
        Stores the information on features, except their values.

    (IV) value_info[object_type][feature_name][feature_value] = [attributes]
    
        Stores the feature value information

    (V) reference_feature[feature_name] = True | False
    
        Stores the names of features that reference other object. 
        The feature 'self' is an example. But we skip this feature. 
        'self' will get the value False, other features, such as mother and parents get True

    (VI) annotation_files[part][subpart] = (ftype, medium, location, requires, annotations, is_region)
    
        Stores information of the files that are generated as the resulting LAF resource
    
    The files are organized by part and subpart.
    Header files and primary data files are in part ''.
    Other files may or may not contain annotations. If not, they only contain regions. Then is_region is True.

      ftype
        the file identifier to be used in header files
      medium
        text or xml
      location
        the last part of the file name.
        All file names can be obtained by appending location after the absolute path followed by a common prefix.
      requires
        the identifier of a file that is required by the current file
      annotations
        the annotation labels to be declared for this file
    
    The feature information file contains lines with tab-delimited fields (only the starred ones are used):
      0*           1*            2*          3*          4*             5*          6          7*           8            9           10    11*   12*
      object_type, feature_name, defined_on, etcbc_type, feature_value, isocat_key, isocat_id, isocat_name, isocat_type, isocat_def, note, part, subpart
      0            1             2           3           4              5                      6                                           7     8
    
    '''
    settings = None

    object_info = {}
    feature_info = {}
    value_info = {}
    part_info = {}
    object_subpart = collections.defaultdict(lambda: {})
    part_object = collections.defaultdict(lambda: set())
    part_feature = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
    reference_feature = {}

    def __init__(self, settings):
        ''' Initialization is: reading the excel sheet with feature information.

        The sheet should be in the form of a tab-delimited text file.

        There are columns with:
            ETCBC information:
                object_type, feature_name, also_defined_on, type, value.
            ISOcat information
                key, id, name, type, definition, note
            LAF sectioning
                part, subpart

        See the list of columns above.
                
        So the file gives essential information to map objects/features/values to ISOcat data categories.
        It indicates how the LAF output can be chunked in parts and subparts.
        '''
        self.settings = settings
        self.simple = False
        self.plain = False
        file_handle = None
        fpfile = settings.env['feature_plain_info']
        ffile = settings.env['feature_info']
        ofile = settings.env['object_info']
        if os.path.exists(ffile):
            file_handle = open(ffile, encoding = 'utf-8')
        else:
            file_handle = open(ofile, encoding = 'utf-8')
            self.simple = True
            if os.path.exists(fpfile):
                self.plain = True

        if self.simple:
            for line in file_handle:
                all_fields = fillup(3, '', line.rstrip().split())
                (object_type, part, subpart) = all_fields
                self.object_info[object_type] = ('', '')
                self.object_subpart[part][object_type] = subpart
                self.part_object[part].add(object_type)
                this_info = self.part_info
                if part not in this_info: this_info[part] = {}
                this_info = this_info[part]
                if subpart not in this_info: this_info[subpart] = {}
                this_info = this_info[subpart]
                if object_type not in this_info: this_info[object_type] = set()
                this_info = self.value_info
                if object_type not in this_info: this_info[object_type] = {}
                this_info = self.feature_info
                if object_type not in this_info: this_info[object_type] = {}
                for lbytes in self.mql('select features from object type [{}]\ngo'.format(object_type)):
                    l = str(lbytes, encoding='utf8')
                    if l.startswith(('-', '+')) or ':' in l: continue
                    (fname, ftype, fdef, fcomp) = [f.strip() for f in l[1:-2].split('|')]
                    ftype = 'reference' if ftype == 'id_d' else 'string' if ftype.endswith('_e') else ftype 
                    self.part_info[part][subpart][object_type].add(fname)
                    self.part_feature[part][object_type].add(fname)
                    self.value_info[object_type][fname] = {}
                    self.feature_info[object_type][fname] = ('', object_type, '', '')
                    if ftype == 'reference':
                        self.reference_feature[fname] = fname not in settings.annotation_skip 
        else:
# the following fields are hierarchical : part, subpart, object_type, feature_name, etcbc_type
# they may inherit from one line to the next, and when one field changes, others have to be reset
# For each input line, we collect them in the list this_fields, and we maintain current values in cur_fields

            line_number = 0
            (cur_part, cur_subpart, cur_object_type, cur_feature_name, cur_etcbc_type) = ('', '', '', '', '')

            for line in file_handle:
                line_number += 1
# The first two lines in the feature info file are header lines. We skip them
                if line_number <= 2: continue

                all_fields = fillup(13, '', line.rstrip().split("\t"))
                used_fields = all_fields[0:6] + all_fields[7:8] + all_fields[11:13]
                (object_type, feature_name, defined_on, etcbc_type, feature_value, isocat_key, isocat_name, part, subpart) = used_fields
                o_atts = (isocat_key, isocat_name)
                f_atts = (defined_on, etcbc_type, isocat_key, isocat_name)
                v_atts = (etcbc_type, isocat_key, isocat_name)
                this_fields = (part, subpart, object_type, feature_name, etcbc_type)
# Reset parts of cur_fields when a hierarchically higher part changes
                if object_type != '':
                    cur_feature_name = ''; 
                    cur_etcbc_type = ''; 
                if feature_name != '': cur_etcbc_type = ''; 
                if part != '': cur_subpart = ''; 
                cur_fields = (cur_part, cur_subpart, cur_object_type, cur_feature_name, cur_etcbc_type)
# For fields that are empty on the current line, use the value saved in cur_fields
                (cur_part, cur_subpart, cur_object_type, cur_feature_name, cur_etcbc_type) = map(lambda c,t: t if t != '' else c, cur_fields, this_fields) 
# Identify the reference features
                if cur_etcbc_type == 'reference':
                    self.reference_feature[cur_feature_name] = cur_feature_name not in settings.annotation_skip 
# Add features to the (sub)part structure
                self.part_object[cur_part].add(cur_object_type)
                if cur_feature_name != '':
                    if cur_object_type not in self.part_feature[cur_part]:
                        self.part_feature[cur_part][cur_object_type] = set()
                    self.part_feature[cur_part][cur_object_type].add(cur_feature_name)

                this_info = self.part_info
                if cur_part not in this_info: this_info[cur_part] = {}
                this_info = this_info[cur_part]
                if cur_subpart not in this_info: this_info[cur_subpart] = {}
                this_info = this_info[cur_subpart]
                if cur_object_type not in this_info: this_info[cur_object_type] = set()
                if cur_feature_name != '':
                    this_info = this_info[cur_object_type]
                    if cur_feature_name not in this_info: this_info.add(cur_feature_name)

                self.object_subpart[cur_part][cur_object_type] = cur_subpart
# Add object info
                this_info = self.object_info
                if cur_object_type not in this_info: this_info[cur_object_type] = o_atts
# Add feature info
                this_info = self.feature_info
                if cur_object_type not in this_info: this_info[cur_object_type] = {}
                if cur_feature_name != '':
                    this_info = this_info[cur_object_type]
                    if cur_feature_name not in this_info: this_info[cur_feature_name] = f_atts
# Add value info
                this_info = self.value_info
                if cur_object_type not in this_info: this_info[cur_object_type] = {}
                if cur_feature_name != '':
                    this_info = this_info[cur_object_type]
                    if cur_feature_name not in this_info: this_info[cur_feature_name] = {}

                    if feature_value != '':
                        this_info = this_info[cur_feature_name]
                        if feature_value not in this_info: this_info[feature_value] = v_atts
        file_handle.close()

# create directories and queries if we have to query the EMDROS database for data
        if settings.flag('raw'):
            run('mkdir -p ' + settings.env['raw_emdros_dir'])
            run('mkdir -p ' + settings.env['query_dst_dir'])

    def check_raw_files(self, part):
        if not self.settings.flag('raw'): return
        print("INFO: BEGIN Generate raw MQL output from EMDROS")
        self.run_mql(self.make_query_file(part), self.raw_file(part))
        print("INFO: END Generate raw MQL output from EMDROS")

    def make_query_file(self, part):
        template = 'GET OBJECTS HAVING MONADS IN ALL\n[{object} {features}]\nGO\n'
        query_text = ''
        for object_type in self.object_list_part(part):
            features = ",\n\t\t".join(self._feature_list_part(part, object_type))
            copy = template.format(
                object = object_type,
                features = ("GET " if features else '') + features,
            )
            query_text += copy
        return self.make_mql("{}.mql".format(part), query_text)

    def run_mql(self, query_file, result_file):
        run('mql -b s3 -d {source} --console {query} > {result}'.format(
                source = self.settings.env['source_data'],
                query = query_file,
                result = result_file,
            ), dyld=True)

    def make_mql(self, name, query):
        query_file = '{}/{}'.format(self.settings.env['query_dst_dir'], name)
        file_handle = open(query_file, "w", encoding = 'utf-8')
        file_handle.write(query)
        file_handle.close()
        return query_file

    def mql(self, query):
        mql_opts = ['--console', '-b', 's3', '-d']
        proc = subprocess.Popen(
            ['mql'] + mql_opts + [self.settings.env['source_data']],
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )
        proc.stdin.write(bytes(query, encoding='utf8'))
        proc.stdin.close()
        result = proc.stdout.readlines()
        proc.stdout.close()
        return result

    def part_list(self): return sorted(self.part_info.keys())
    def subpart_list(self, part): return sorted(self.part_info[part].keys())
    def object_list_part(self, part): return sorted(self.part_object[part])
    def the_subpart(self, part, object_type): return self.object_subpart[part][object_type]
    def object_list(self, part, subpart): return sorted(self.part_info[part][subpart].keys())
    def feature_list(self, object_type): return sorted(self.feature_info[object_type].keys())
    def _feature_list_part(self, part, object_type):
        return sorted(x for x in self.part_feature[part][object_type] if x not in self.settings.annotation_skip)
    def feature_list_subpart(self, part, subpart, object_type):
        return sorted(x for x in self.part_info[part][subpart][object_type] if x not in self.settings.annotation_skip)
    def value_list(self, object_type, feature_name): return sorted(self.value_info[object_type][feature_name].keys())
    def object_atts(self, object_type): return self.object_info[object_type]
    def feature_atts(self, object_type, feature_name): return self.feature_info[object_type][feature_name]
    def value_atts(self, object_type, feature_name, feature_value): return self.value_info[object_type][feature_name][feature_value]
    def list_ref_noskip(self): return sorted(x for x in self.reference_feature if self.reference_feature[x])
    def is_ref_skip(self, feature_name): return feature_name in self.reference_feature and not self.reference_feature[feature_name]
    def raw_file(self, part): return self.settings.parts[part]['raw_text']
