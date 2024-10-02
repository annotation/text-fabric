import sys
import re
import collections

# This module has a big loop (in process_lines) which iterates over more than a million lines.
# Quite a lot has to happen for each line, so it is important to keep that
# loop as efficient as possible. That's why we declare all regular expressions
# globally and compile them.

infoscan = re.compile(r'\[ (\w+) (\d+) \{ ([\d ,-]+) \}')
featurescan = re.compile(r'(\w+)="([^"]*)"')
uniscan = re.compile(r'(?:\\x..)+')
wordscan = re.compile(r'([&-]|00)((?:_[NSP])*)$')

class Transform:
    ''' Transforms ETCBC data into a LAF resource

    ETCBC knowledge comes from the Etcbc class
    LAF knowledge comes from the Laf class

    read data from raw MQL export
    and build the annotations files
    For part monad there are extra things:
    *  the primary data file will be built
    *  one of the annotations files only contains regions, and no annotations
    '''
    et = None
    lf = None
    settings = None
# remember the object types that have been encountered so far
# These types should be remembered across parts, in order to prevent repeated node
# generation if an object type occurs in multiple parts.

    def __init__(self, settings, et, lf):
        self.settings = settings
        self.et = et
        self.lf = lf

    def transform(self, part):
        self.lf.start_annot(part)
        if part == 'monad': self.lf.start_primary()
        self.et.check_raw_files(part)
        self.process_lines(part)
        self.lf.finish_annot(part)
        if part == 'monad': self.lf.finish_primary()

    def process_lines(self, part):
        ''' Data transformation for part. 
        Input: the lines of a raw emdros output file, which is processed line by line.
        Every line contains an object type, object identifier, monad indicator and list of features.
        This has to be translated to primary data and annotations.

        Efficiency is very important. It will not do to call functions or follow long chains of dereferencing.
        Yet a lot has to happen.
        That is why this is a lengthy loop, and we maintain quite a lot of information from elsewhere in the program
        in loop-global variables. Not doing so might increase the running time 10-fold.
        Currently the complete programs runs within 15 minutes (inclusing generating raw data and validating) on an
        MacBook Air mid 2012.
        '''
        monad_limit = self.settings.args.limit
        part_settings = self.settings.parts[part]
        region_handle = None
        plain_handle = None
        primary_handle = None
        do_primary = 'do_primary' in part_settings
# The objects in some parts will get a separate file in LAF for the nodes.
# This is triggered by the config setting separate_node_file.
# The other LAF files will be generated with both nodes and annotations in a single file.
        separate_node_file = 'separate_node_file' in part_settings
# we need an index that maps monad numbers to char positions in the primary data.
# This index is generated when doing part 'monad', and used when doing part 'section'.
# In part section we create new regions, corresponding to the books, chapters, verses and half-verses.
# Refererring to the regions that were created for words and white space and punctuation would be clumsy in LAF.
# Creation and use of the index is triggered by settings in the configuration file: make_index and use_index.
# The index data itself, once read in, is stored in the dictionary monad_chars.
        index_handle = None
        index_path = self.settings.env['monad_index']
        make_index = 'make_index' in part_settings
        use_index = 'use_index' in part_settings
        no_monad_nodes = 'no_monad_nodes' in part_settings
        monad_chars = {}
# The LAF object knows which annotation files we have to write. We get the file handles and store them in
# a local dictionary.
        sub_handles = self.lf.file_handles
# For part 'section' we have to do something special: we have to link half_verses to their containing verses
# to their containing chapters to their containing books. This is done on the basis of monad embedding.
# An object is embedded in another object if and only if the monads of the first object are a subset of the monads of the second object.
# For part 'section' we make an ordered list of section objects according to the embedding/before relationships.
# Based on this list we can efficiently construct the relations between the section objects. 
# In the list hierarchy we fetch the configuration setting that tells us which object types we should embed in which other ones.
# The process of creating the embedding is triggered by theconfig setting find_embedding
        sort_objects = []
        hierarchy = []
        find_embedding = 'find_embedding' in part_settings
# compute the embedding relationships that have to be generated, if needed
        if find_embedding:
            hierarchy_levels = part_settings['hierarchy'].split(" ")
            prev_level = ''
            for level in hierarchy_levels:
                if prev_level == '': prev_level = level
                else:
                    hierarchy.append((prev_level, level))
                    prev_level = level
# initialize generation of primary data if needed
        if do_primary:
            primary_handle = self.lf.primary_handle
            region_handle = self.lf.file_handles[self.settings.annotation_regions['name']][0]
            primary_feature = self.settings.meta['primary']
            trailer_feature = self.settings.meta['trailer']
            add_verse_newline = self.settings.meta['verse_newline'] == '1'
        if separate_node_file: plain_handle = self.lf.file_handles[''][0]
# create or use the monad char index if needed
        if make_index: index_handle = open(index_path, 'w')
        if use_index:
            gminmonad = None
            gmaxmonad = None
            index_handle = open(index_path, 'r')
            for line in index_handle:
                (m, start, end_word, end_trailer) = line.rstrip("\n").split("\t")
                monad_chars[m] = (start, end_word, end_trailer)
                if gminmonad == None or int(m) < int(gminmonad): gminmonad = m
                if gmaxmonad == None or int(m) > int(gmaxmonad): gmaxmonad = m
            index_handle.close()
            print("INFO: Monad-char index has {} items, from monad {} to monad {}".format(len(monad_chars), gminmonad, gmaxmonad))
# open the input file with raw data
        file_handle = open(self.et.raw_file(part), encoding = 'utf-8')
# initialize some counters
        n_line = 0          # number of current line in input file
        n_unmatched = 0     # number of illegal lines in input file that has been encountered
        n_nonword = 0       # number of non-word regions that has been generated (used to construct identifiers for such regions)
        n_af = 0            # numbber of feature annotations that has been created (used to construct identifiers for annotations)
        n_en = 0            # number of edges that has been created (used to construct identifiers for edges)
        n_f = 0             # total number of features <f> elements created
        n_n = 0             # total number of nodes
        n_a = 0             # total number of annotations
        n_e = 0             # total number of edges
        n_r = 0             # total number of regions
        n_m = 0             # total number of monads
        o = 0               # current output char position (used to create regions)
# fetch template info
        region_elem = self.lf.template['region_elem']
        region_types = self.settings.annotation_regions
        region_word = region_types['word']
        region_punct = region_types['punct']
        region_section = region_types['section']
        annotation_elem = self.lf.template['annotation_elem']
        node_elem = self.lf.template['node_elem']
        edge_elem = self.lf.template['edge_elem']
        edgenode_elem = self.lf.template['edgenode_elem']
        feature_elem = self.lf.template['feature_elem'].rstrip("\n")
# fetch object list, subparts
        object_types = self.et.object_list_part(part)
        subparts = sorted(self.lf.file_handles.keys())
# fetch additional information
        db_label = self.settings.annotation_label['db_label']
        annotation_label = self.settings.annotation_label[part + '_label']
        monad_type = self.settings.parts['monad']['object_type']
# set up a dictionary to collect statistics of annotation label usage
        stats = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
        statskind = stats[annotation_label]
        statsdb = stats[db_label]
# fetch additional feature info: what are the relational features?
        ref_features = set(self.et.list_ref_noskip())
# we must compute as little as possible in each iteration below
# That is why we maintain the list with features outside the loop
# Whenever a line switches to another object type, we will get the list of features for that object type
# But most of the time, the object type is the same as the one of the previous line
        prev_object_type = ''
        generate_nodes = True
        prev_features = {}
#####################################################
# HERE STARTS THE MAIN LOOP
#####################################################
        for line in file_handle:
# there are some non-informational lines in the input, they have a very small length, we skip them
            if len(line) <= 5: continue
# we maintain the line number, and ever so often we print the current line number to the terminal
# by way of progress indication
            n_line += 1
            if n_line % 1000 == 0: sys.stderr.write("\rINFO: " + str(n_line))
# Get all the information from the line
# do some sanity first: convert escaped raw byte codes to real utf and insert xml escapes
            line_norm = uniscan.sub(makeuni, line).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
# Get OBJECT IDENTIFIER
            match = infoscan.search(line_norm)
            if not match:
                print("ERROR: Unmatched line: {}: {}".format(n_line, line.rstrip("\n")))
                continue
            object_type, object_id, monads = match.group(1, 2, 3)
            if do_primary: stats[object_type][''] += 1
# Set up list of FEATURE NAMES per subpart
# but only when the object type has changed!
            do_get_features = False
            if prev_object_type != object_type:
                generate_nodes = (not no_monad_nodes) or object_type != monad_type
                prev_features = {}
                prev_object_type = object_type
                this_subpart = self.et.the_subpart(part, object_type)
                do_get_features = True
# Get FEATURES
            features = featurescan.findall(line_norm)
            feature_dict = dict(features)
# Get MONADS
            regions = []
            monad_num = -1
            minmonad = -1
            maxmonad = -1
            monads = monads.replace(' ','')
# When we know that there is a single monad do it quickly.
# This occurs when the object type is the monad type.
            if do_primary or object_type == monad_type:
                if not monads.isdigit():
                    print("ERROR: Multiple monad numbers {} on line {}".format(monads, n_line))
                    continue
                monad_num = int(monads)
                regions = [monad_num]
                minmonad = monad_num
                maxmonad = monad_num
            else:
# For other object types, we have to build a set of all monads specified by a comma separated list of ranges
                ranges = monads.split(",")
                for rng in ranges:
                    endpoints = rng.split("-")
                    br = endpoints[0]
                    er = br
                    if len(endpoints) == 2: er = endpoints[1]
                    regions += range(int(br), int(er) + 1)
                minmonad = str(min(regions))
                maxmonad = str(max(regions))
# Maybe we have to stop:
            if monad_limit and int(maxmonad) > monad_limit: break
# Begin PRIMARY DATA generation
# Get PRIMARY DATA
# first we extract the primary data from the features.
# That's a bit tricky, we defer it to a function
# What needs to come out of that function is a word, possible punctuation behind it,
# an indication of the spacing, and some other characters that must be appended
            if do_primary:
                if primary_feature:
                    text_xml = feature_dict[primary_feature]
                    if trailer_feature:
                        trailer_xml = feature_dict[trailer_feature]
                    else:
                        trailer_xml = ' '
                else:
                    text_xml, trailer_xml = primary_data(feature_dict['text'], feature_dict['suffix'])
                    feature_dict['text'] = text_xml
                    feature_dict['suffix'] = trailer_xml
                text = text_xml.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                trailer = trailer_xml.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
# Construct PRIMARY DATA
# Now we build up the primary data file and the regions file
# We have to keep count of the char position of the data in the primary data file
# So compute the length of the unicode strings that we need to write to the primary data
                ltext = len(text)
                ltrailer = len(trailer)
                n_m += 1
                if make_index: index_handle.write("{}\t{}\t{}\t{}\n".format(monad_num, o, o + ltext, o + ltext + ltrailer))
# Every unit to be written contains exactly one word, plus a trailer which contains spacing, punctuations and final codes
#   This is accumulated in p_data
#   The current char position is maintained in o
#
# For every word and trailer we create a <region> element that indicates its char position
#   This is accumulated in r_data
# There is always a word inside
                r_data = region_elem.format(xmlid = "{}_{}".format(region_word, monads), start = o, end = o + ltext)
                n_r +=1
                o += ltext
                p_data = text
# Possibly there is a trailer, some trailers end a verse, there we insert a newline
                if trailer != '':
                    p_data += trailer
                    n_nonword += 1
                    boundaries = "{} {}".format(o, o + ltext) if trailer != '' else "{}".format(o)
                    r_data += region_elem.format(xmlid = "{}_{}".format(region_punct, n_nonword), start = o, end = o + ltrailer)
                    n_r += 1
                    o += ltrailer
                    if add_verse_newline and '׃' in trailer:
                        o += 1
                        p_data += "\n"
                        r_data += "\n"
# When all is constructed, we write it away to the appropriate files (having been opened by the initialization
# of the Laf class
# Here we write the regions to a separate file.
# And we write the nodes to a separate file
                primary_handle.write(p_data)
                region_handle.write(r_data)
# END PRIMARY DATA generation
# COMPUTE THE NODES FOR THE SEPARATE NODE FILE IF NEEDED
            if separate_node_file and generate_nodes:
                n_data = ''
                if object_type == monad_type:
                    n_data = node_elem.format(
                        part = part[0], akind = db_label, aid = object_id, xmlid = object_id,
                        monads = monads, minmonad = minmonad, maxmonad = maxmonad, objectid = object_id, objecttype=object_type,
                        region = "{}_{}".format(region_word, monads)
                    ) 
                else:
                    n_data = node_elem.format(
                        part = part[0], akind = db_label, aid = object_id, xmlid = object_id,
                        monads = monads, minmonad = minmonad, maxmonad = maxmonad, objectid = object_id, objecttype=object_type,
                        region = " ".join("{}_{}".format(region_word, str(x)) for x in regions)
                    ) 
                statsdb[''] += 1
                n_data += "\n"
                n_n += 1
                n_f += 4 # the node_elem template adds 4 separate features: monads, minmonad, maxmonad, objectid
                plain_handle.write(n_data)
            the_subparts = subparts if do_primary else [this_subpart]
            for subpart in the_subparts:
# Construct REGIONS, NODES, ANNOTATIONS, EDGES if needed, per subpart
                if subpart == '' and do_primary: continue
                if subpart == region_types['name']: continue
# that was a subpart where a file with only regions has been constructed. So we can skip adding regions to the annotation file.
                features = {}
                if do_get_features:
                    features = self.et.feature_list_subpart(part, subpart, object_type)
                    prev_features[subpart] = features
                else: features = prev_features[subpart]
                r_data = ''     # region data
                n_data = ''     # node data
                a_data = ''     # annotation data
                f_data = ''     # feature data
                e_data = ''     # edge data
# Construct REGIONS
# only construct regions if use_index is in the configuration file for this part
                r_id = ''
                if use_index:
                    minchar = 0
                    maxchar = 0
                    minmonad = str(min(regions))
                    if minmonad not in monad_chars:
                        print("WARNING: line {}: min monad {} not in monad_char index, taking monad {} instead.".format(n_line, minmonad, gminmonad))
                        minmonad = gminmonad
                    minchar = monad_chars[minmonad][0]
                    if maxmonad not in monad_chars:
                        print("WARNING: line {}: max monad {} not in monad_char index, taking monad {} instead.".format(n_line, maxmonad, gmaxmonad))
                        maxmonad = gmaxmonad
                    maxchar = monad_chars[maxmonad][2]
                    r_id = "{}_{}".format(region_section, object_id)
                    r_data = region_elem.format(xmlid = r_id, start = minchar, end = maxchar)
                    n_r += 1
# Construct FEATURE data
# Relational features translate to EDGES
                has_real_features = False
                for feature in features:
                    if feature in ref_features:
                        value = feature_dict[feature]
                        if value != "0" and value != "" and value != " ":
                            value = value.strip()
                            values = value.split(" ")
                            for val in values:
                                n_en += 1
                                e_data += edgenode_elem.format(part = part[0], eid = n_en, fr = object_id, to = val, aid = n_en, akind = annotation_label, fname = feature, value = '')
                                n_e += 1
                                stats[feature][subpart] += 1
                    else:
                        has_real_features = True
                        f_data += "\n\t" + feature_elem.format(name = feature, value = feature_dict[feature].replace('\n', '&#xa;'))
                        n_f += 1
# Prepare EDGES for hierarchical sections
# We collect a list of all objects with the first and last monad as extra information
# This list will be sorted later
                if find_embedding: sort_objects.append((min(regions), max(regions), object_type, object_id))
                n_af += 1
# Construct NODES if needed
                if not separate_node_file:
                    if has_real_features:
                        if use_index:
                            n_data = node_elem.format(
                                part = part[0], akind = db_label, aid = object_id, xmlid = object_id,
                                monads = monads, minmonad = minmonad, maxmonad = maxmonad, objectid = object_id, objecttype=object_type,
                                region = r_id
                            ) 
                        else:
                            n_data = node_elem.format(
                                part = part[0], akind = db_label, aid = object_id, xmlid = object_id,
                                monads = monads, minmonad = minmonad, maxmonad = maxmonad, objectid = object_id, objecttype=object_type,
                                region = " ".join("{}_{}".format(region_word, str(x)) for x in regions)
                            ) 
                        statsdb[subpart] += 1
                        n_n += 1
                        n_f += 4 # the node_elem template adds 4 separate features: monads, minmonad, maxmonad, objectid
# Construct ANNOTATIONS
                if has_real_features:
                    a_data = annotation_elem.format(part = part[0], xmlid = n_af, akind = annotation_label, objectid = object_id, features = f_data)
                    n_a += 1
                outline = r_data + n_data + a_data + e_data
                if outline:
                    sub_handles[subpart][0].write(outline + "\n")
                stats[object_type][subpart] += 1
                statskind[subpart] += 1
#####################################################
# HERE ENDS THE MAIN LOOP
#####################################################
        print('')
# Generate additional EDGES based on whether objects are monad-wise included in each other
        if find_embedding:
            print("INFO: Creating embedding relations")
            sorted_objects = sorted(sort_objects, key=interval)
            for (outer, inner) in hierarchy:
                print("INFO: Generating embedding of {} in {}".format(inner, outer))
                cur_outer_id = -1
                for (start, end, object_type, object_id) in sorted_objects:
                    if object_type == outer:
                        cur_outer_id = object_id
                        continue
                    if object_type == inner:
                        if int(cur_outer_id) < 0: print("ERROR: {} with id {} not inside any {}".format(inner, object_id, outer))
                        else:
                            n_en += 1
                            e_data = edge_elem.format(part = part[0], eid = n_en, fr = cur_outer_id, to = object_id)
                            n_e += 1
                            sub_handles[''][0].write(e_data)
# Transfer the statistics information to the LAF object, so that the annotation files can be finalised properly
        for ob in stats:
            for sp in stats[ob]: self.lf.stats["{}.{}".format(sp, ob)] = stats[ob][sp]
        for subpart in subparts:
            self.lf.stats["{}.{}".format(subpart, db_label)] = statsdb[subpart]
            if subpart == '' and do_primary: continue
            if subpart == region_types['name']: continue
            self.lf.stats["{}.{}".format(subpart, annotation_label)] = statskind[subpart]
# Fill in general overall statistics
        self.lf.gstats['a Number of regions'] += n_r
        self.lf.gstats['b Number of nodes'] += n_n
        self.lf.gstats['c Number of edges'] += n_e
        self.lf.gstats['d Number of annotations'] += n_a
        self.lf.gstats['e Number of features'] += n_f
        self.lf.gstats['f Number of monads'] += n_m
        self.lf.gstats['g Number of chars in primary data'] += o
        if n_unmatched: print("ERROR: {} Unmatched lines".format(n_unmatched))
        else: print("INFO: {} object lines".format(n_line))
        if make_index: index_handle.close()
        file_handle.close()

def primary_data(text, trailer):
    ''' Distil primary data from two features on the word objects.
    Apply necessary tweaks!
    '''
    if text.endswith('׀'):
        text = text.rstrip('׀')
        trailer = ' ׀' + trailer
    return (text, trailer)

def makeuni(match):
    ''' Make proper unicode of a text that contains byte escape codes such as backslash xb6
    '''
    byts = eval('"' + match.group(0) + '"')
    return byts.encode('latin1').decode('utf-8')

def interval(iv): return (iv[0], -iv[1])
