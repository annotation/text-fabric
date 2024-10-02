import os
import sys
import collections
import glob

import configparser
import argparse

NAME = 'LAF-Fabric'
VERSION = '4.8.4'
APIREF = 'http://laf-fabric.readthedocs.org/en/latest/texts/API-reference.html'
DEFAULT_DATA_DIR = 'laf-fabric-data'
MAIN_CFG = 'laf-fabric.cfg'
ALL_PARTS = ['monad', 'section', 'lingo']

class Settings:
    ''' Stores configuration information from the main configuration file and the command line.
        
        Defines an extra function in order to get the items in a section as a dictionary,
        without getting the DEFAULT items as wel
    '''
    _myconfig = {
        'my_name':              NAME,
        'version':              VERSION,
    }
    _env_def = {
        'my_name':              '{my_name}',
        'version':              '{version}',
        'template_dir':         '{script_dir}/templates',
        'xml_dir':              '{script_dir}/xml',
        'source':               '{source}',
        'meta_info':            '{data_dir}/{source}/config/main.cfg',
        'feature_info':         '{data_dir}/{source}/config/ObjectsFeaturesValues.txt',
        'feature_plain_info':   '{data_dir}/{source}/config/ObjectsFeatures.csv',
        'object_info':          '{data_dir}/{source}/config/Objects.txt',
        'raw_emdros_dir':       '{data_dir}/{source}/raw',
        'source_data':          '{data_dir}/{source}/mql/{source}',
        'query_dst_dir':        '{data_dir}/{source}/mql',
        'result_dir':           '{data_dir}/{source}/laf',
        'annot_hdr':            '{data_dir}/{source}/laf/{source}',
        'primary_text':         '{data_dir}/{source}/laf/{source}.txt',
        'primary_hdr_txt':      '{data_dir}/{source}/laf/{source}.txt.hdr',
        'resource_hdr_txt':     '{data_dir}/{source}/laf/{source}.hdr',
        'monad_index':          '{data_dir}/{source}/laf/{source}.lst',
        'decl_dst_dir':         '{data_dir}/{source}/decl',

    }
    _metaconfig = {
        'my_name':              NAME,
        'version':              VERSION,
        'ISOcatprefix':         'http://www.isocat.org/datcat/DC-',
        'DANSpidprefix':        'http://persistent-identifier/?identifier=',
    }
    _meta_def = {
        'my_name':              '{my_name}',
        'version':              '{version}',
        'source':               '{source}',
        'ISOcatprefix':         '{ISOcatprefix}',
        'DANSpidprefix':        '{DANSpidprefix}',
        'danspid_act':          '{DANSpidprefix}{danspid_urn}',
        'publicationdate':      '{publicationdate}',
        'danspid_urn':          '{danspid_urn}',
        'annot_method':         'conversion script {my_name} {version}',
        'annot_resp':           '{annot_resp}',
        'primary':              '{primary}',
        'trailer':              '{trailer}',
        'verse_newline':        '{verse_newline}',
        'annot_space_def':      '{annot_space_def}',
        'prim_creator':         '{prim_creator}',
        'res_creator':          '{res_creator}',
        'prim_title':           '{prim_title}',
        'res_title':            '{res_title}',
        'prim_source_title':    '{prim_source_title}',
        'prim_source_author':   '{prim_source_author}',
        'prim_source_publisher':'{prim_source_publisher}',
        'prim_source_date':     '{prim_source_date}',
        'prim_source_year':     '{prim_source_year}',
        'prim_source_place':    '{prim_source_place}',
        'prim_languages':       '{prim_languages}',
        'res_funder':           '{res_funder}',
        'res_respons_link':     '{res_respons_link}',
        'res_respons_name':     '{res_respons_name}',
        'res_distributor':      '{res_distributor}',
        'res_institute':        '{res_institute}',
        'res_email':            '{res_email}',
        'res_project_desc':     '{res_project_desc}',
        'res_sampling_desc':    '{res_sampling_desc}',
        'res_transduction':     '{res_transduction}',
        'res_correction':       '{res_correction}',
        'res_segmentation':     '{res_segmentation}',
    }
    _laf_templates = {
        'feature_decl':         ('feature_decl.xml', False),
        'feature':              ('feature.xml', True),
        'feature_local':        ('feature_local.xml', True),
        'feature_val':          ('feature_val.xml', True),
        'feature_val1':         ('feature_sym.xml', True),
        'feature_basic':        ('feature_basic.xml', True),
        'annotation_decl':      ('annotation_decl.xml', True),
        'annotation_item':      ('annotation_item.xml', True),
        'annotation_hdr':       ('annotation_header.xml', False),
        'annotation_label':     ('annotation_label.xml', True),
        'annotation_ftr':       ('annotation_footer.xml', False),
        'annotation_elem':      ('annotation_element.xml', False),
        'feature_elem':         ('feature_element.xml', False),
        'node_elem':            ('node_element.xml', False),
        'edge_elem':            ('edge_element.xml', False),
        'edgenode_elem':        ('edgenode_element.xml', False),
        'region_hdr':           ('region_header.xml', False),
        'region_elem':          ('region_element.xml', False),
        'resource_hdr':         ('resource_header.xml', False),
        'primary_hdr':          ('primary_header.xml', False),
        'dependency':           ('dependency.xml', True),
    }
    _laf = {
        'resource_header':      'requires',
        'annotation_header':    'dependsOn',
    }
    _xml = {
        'xmllint_cmd':          'xmllint --noout --nonet --schema {{schema}} {{xmlfile}}',
        'xmllint_cat_env_var':  'XML_CATALOG_FILES',
        'xmllint_cat_env_val':  '{xml_dir}/xmllint_cat.xml',
        'xlink_src':            '{xml_dir}/xlink.xsd',
        'xlink_dst':            '{decl_dst_dir}/xlink.xsd',
        'xml_src':              '{xml_dir}/xml.xsd',
        'xml_dst':              '{decl_dst_dir}/xml.xsd',
        'xml_isofs_src':        '{xml_dir}/xml-isofs.xsd',
        'xml_isofs_dst':        '{decl_dst_dir}/xml-isofs.xsd',
        'graf_annot_src':       '{xml_dir}/graf-standoff.xsd',
        'graf_annot_dst':       '{decl_dst_dir}/graf-standoff.xsd',
        'graf_resource_src':    '{xml_dir}/graf-resource.xsd',
        'graf_resource_dst':    '{decl_dst_dir}/graf-resource.xsd',
        'graf_document_src':    '{xml_dir}/graf-document.xsd',
        'graf_document_dst':    '{decl_dst_dir}/graf-document.xsd',
        'tei_fs_src':           '{xml_dir}/isofs_dcr.xsd',
        'tei_fs_dst':           '{decl_dst_dir}/isofs_dcr.xsd',
        'dcr_src':              '{xml_dir}/dcr.xsd',
        'dcr_dst':              '{decl_dst_dir}/dcr.xsd',
    }
    _parts = {
        'monad': {
            'raw_text':         '{raw_emdros_dir}/monad.txt',
            'object_type':      'word',
            'make_index':       '',
            'do_primary':       '',
            'separate_node_file':'',
        },
        'section': {
            'raw_text':         '{raw_emdros_dir}/section.txt',
            'use_index':        '',
            'find_embedding':   '',
            'hierarchy':        'book chapter verse half_verse',
        },
        'lingo': {
            'raw_text':         '{raw_emdros_dir}/lingo.txt',
            'separate_node_file':'',
            'no_monad_nodes':   '',
        },
    }
    _annotation_kind = {
        'monad':                'minimal objects&text&',
        'section':              'section objects&text&',
        'lingo':                'linguistic objects&text&',
        'reference':            'linguistic relationships&fsDecl&decl/ft.xml',
        'ft':                   'linguistic features&fsDecl&decl/ft.xml',
        'sft':                  'sectional features&fsDecl&decl/sft.xml',
        'db':                   'database features&fsDecl&decl/db.xml',
    }
    _annotation_regions = {
        'name':                 'region',
        'word':                 'w',
        'punct':                'p',
        'section':              's',
    }
    _annotation_skip_object = {
        'lingo':                'word',
    }
    annotation_skip = set(('self',))
    _annotation_label = {
        'section_label':        'sft',
        'lingo_label':          'ft',
        'monad_label':          'ft',
        'db_label':             'db',
    }
    _type_mapping = {
        'string':               'string',
        'ascii':                'string',
        'integer':              'numeric&value="0" max="100000000"',
        'enum':                 'symbol',
        'boolean':              'binary',
        'reference':            'string',
    }
    _type_boolean = {
        't':                    'false',
        'f':                    'true',
    }
    laf_switches = set(('comment_local_deps',))
    _file_types = collections.OrderedDict((
        ('f.hdr',               '.hdr&xml'),
        ('f.primary.hdr',       '.text.hdr&xml'),
        ('f.primary',           '.txt&text'),
        ('f_monad.region',      '_regions.xml&xml'),
        ('f_monad',             '_monads.xml&xml&db&f_monad.region'),
        ('f_lingo',             '_lingo.xml&xml&db&f_monad'),
        ('f_section',           '_sections.xml&xml&db sft'),
        ('f_monad.*',           '_monads.{{subpart}}.xml&xml&ft&f_monad'),
        ('f_lingo.*',           '_lingo.{{subpart}}.xml&xml&ft&f_lingo'),
    ))

    def flag(self, name): return getattr(self.args, name)

    def __init__(self):
        print('This is {} {}\n{}'.format(NAME, VERSION, APIREF))
        strings = configparser.ConfigParser(inline_comment_prefixes=('#'))
        script_dir = os.path.dirname(os.path.abspath(__file__))
        home_dir = os.path.expanduser('~')

        global_config_dir = "{}/{}".format(home_dir, DEFAULT_DATA_DIR)
        global_config_path = "{}/{}".format(global_config_dir, MAIN_CFG)
        local_config_path = MAIN_CFG
        default_data_dir = global_config_dir
        default_laf_dir = global_config_dir
        config_data_dir = None
        config_laf_dir = None
        config_output_dir = None
        the_config_path = None
        for config_path in (local_config_path, global_config_path):
            if os.path.exists(config_path): the_config_path = config_path
        if the_config_path != None:
            with open(the_config_path, "r", encoding="utf-8") as f: strings.read_file(f)
            if 'locations' in strings:
                if 'data_dir' in strings['locations']: config_data_dir = strings['locations']['data_dir']
                if 'laf_dir' in strings['locations']: config_laf_dir = strings['locations']['laf_dir']
                if 'output_dir' in strings['locations']: config_output_dir = strings['locations']['output_dir']
        the_data_dir = config_data_dir or default_data_dir
        the_laf_dir = config_laf_dir or the_data_dir
        the_output_dir = config_output_dir
        the_data_dir = \
            the_data_dir.replace('.', cw_dir, 1) if the_data_dir.startswith('.') else the_data_dir.replace('~', home_dir, 1) if the_data_dir.startswith('~') else the_data_dir
        the_laf_dir = \
            the_laf_dir.replace('.', cw_dir, 1) if the_laf_dir.startswith('.') else the_laf_dir.replace('~', home_dir, 1) if the_laf_dir.startswith('~') else the_laf_dir
        the_output_dir = \
            the_output_dir.replace('.', cw_dir, 1) if the_output_dir.startswith('.') else the_output_dir.replace('~', home_dir, 1) if the_output_dir.startswith('~') else the_output_dir

        sources = [os.path.basename(x) for x in glob.glob("{}/*".format(the_data_dir)) if os.path.isdir(x)]

        self._myconfig['data_dir'] = the_data_dir
        self._myconfig['home_dir'] = home_dir
        self._myconfig['script_dir'] = script_dir

        argsparser = argparse.ArgumentParser(description = 'Conversion of Emdros to LAF')
        argsparser.add_argument(
            '--source',
            nargs = 1,
            type = str,
            choices = sources,
            metavar = 'Source',
            help = 'Source selection for conversion',
        )
        argsparser.add_argument(
            '--parts',
            nargs = '*',
            type = str,
            choices = ALL_PARTS + ['all', 'none'],
            metavar = 'Kind',
            help = 'task in conversion process',
        )
        argsparser.add_argument(
            "--raw",
            action = "store_true",
            help = "retrieve raw data from Emdros",
        )
        argsparser.add_argument(
            "--validate",
            action = "store_true",
            help = "validate genrated xml files against their schemas",
        )
        argsparser.add_argument(
            "--fdecls-only",
            dest = 'fdecls_only',
            default = False,
            action = "store_true",
            help = "only generate feature declaration file, nothing else",
        )
        argsparser.add_argument(
            "--limit",
            dest = 'limit',
            type = int,
            metavar = 'Limit',
            help = "limit to the first N monads",
        )
        self.args = argsparser.parse_args()
        self.given_parts = collections.OrderedDict()
        for arg in self.args.parts:
            if arg == 'none' or self.args.fdecls_only:
                for a in ALL_PARTS:
                    if a in self.given_parts: del self.given_parts[a]
            elif arg == 'all':
                for a in ALL_PARTS: self.given_parts[a] = True
            else: self.given_parts[arg] = True
        source = self.args.source[0]

        self.env = dict((e, v.format(source=source, **self._myconfig)) for (e,v) in self._env_def.items())
        with open(self.env['meta_info'], "r", encoding="utf-8") as f: strings.read_file(f)
        self._metaconfig.update(strings['meta'] if 'meta' in strings else {})
        self.meta = dict((e, v.format(source=source, **self._metaconfig).replace('\\n','\n')) for (e,v) in self._meta_def.items())
        self._myconfig.update(self.env)
        self.laf_templates = dict((e, (v[0].format(**self._myconfig), v[1])) for (e,v) in self._laf_templates.items()) 
        self.laf = dict((e, v.format(**self._myconfig)) for (e,v) in self._laf.items())
        self.xml = dict((e, v.format(**self._myconfig)) for (e,v) in self._xml.items())
        self.parts = {}
        for p in self._parts:
            self.parts[p] = {}
            self.parts[p] = dict((e, v.format(**self._myconfig)) for (e,v) in self._parts[p].items())
        self.annotation_kind = dict((e, v.format(**self._myconfig)) for (e,v) in self._annotation_kind.items())
        self.annotation_regions = dict((e, v.format(**self._myconfig)) for (e,v) in self._annotation_regions.items())
        self.annotation_skip_object = dict((e, v.format(**self._myconfig)) for (e,v) in self._annotation_skip_object.items())
        self.annotation_label = dict((e, v.format(**self._myconfig)) for (e,v) in self._annotation_label.items())
        self.type_mapping = dict((e, v.format(**self._myconfig)) for (e,v) in self._type_mapping.items())
        self.type_boolean = dict((e, v.format(**self._myconfig)) for (e,v) in self._type_boolean.items())
        self.file_types = collections.OrderedDict((e, v.format(**self._myconfig)) for (e,v) in self._file_types.items())
