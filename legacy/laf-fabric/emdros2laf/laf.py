import sys
import re
import collections

from .mylib import *

class Laf:
    ''' Knows the LAF data format.

    All LAF knowledge is stored in template files together with sections in the main configuration file.
    The LAF class finds those templates, sets up the result files, and fills them.

    Note:
        Templates

        *template[key] = text*
            where key is an entry in the *laf_templates* section of the main config file.

    Note:
        Files and Filetypes

        *annotation_files[part][subpart] = (ftype, medium, location, requires, annotations, is_region)*

        The order is important, so we generate a list too:

        *file_order*
            list of ftypes according *file_types section* in main config file, expanded, in the order encountered

        where

        *ftype*
            comes from the file_types section in the main config file.
            It has the shape of LAF file identifier, but with wild cards.

            *f.xxxxxx*
                not an annotation file, but primary data or a header file
            *f_part.subpart*
                annotation file for part, subpart

        *for each ftype*    
            there is an infostring consisting of fields

            *location*
                file name of corresponding file, modulo a common prefix
            *medium*
                file type (text or xml)
            *annotations*
                space separated annotation labels occurring in this part, subpart
            *requires*
                space separated list of ftypes of required files

        *is_region*
            reveals whether the file only contains regions or not.
            A pure region file needs a different template.

    Note:
        Header Generation

        All header files are generated here: 
        * the feature declaration file
        * the header for the resource as a whole
        * the header for the primary data file

        The headers of the annotation files are included in those files.
        Those headers contain statistics: counts of the number of annotations with a given label.
        We know those number only after generation because these statistics will be collected during
        further processing.

        When the annotation files are generated, we use placeholders for the statistics.
        In a post-generation stage we read/write the annotation files and replace the place holders by
        the true numbers. The files are written in situ. So we must take care that the placeholders
        contain enough space around them.

    Note:
        Processing

        This class provides methods to initialize and finalize the generation of primary data files
        and annotation files. There are methods to open/close all files that are relevant to the
        part that is being processed. (Part being: 'monad', 'section', 'lingo').

    Note:
        Statistics

        Counts are collected in a *stats* dictionary.

        * stats[statistic_name] = statistic_value*

    '''
    settings = None
    et = None
    annotation_files = collections.defaultdict(lambda: {})
    file_order = []
    file_handles = {}
    primary_handle = None
    template = {}
    stats = collections.defaultdict(lambda: 0)
    gstats = collections.defaultdict(lambda: 0)

    def __init__(self, settings, et, val):
        self.settings = settings
        self.et = et
        self.val = val
# make sure the directories in which files will be created, exist
        run('mkdir -p ' + settings.env['result_dir'])
        run('mkdir -p ' + settings.env['decl_dst_dir'])
# parse the config info about the LAF files to be created and create a to do list from this
# The todo list is a list of entries having the following information
#   part, subpart, filetype specification, annotation information
        todo = []
        for (ftype_spec, info_spec) in settings.file_types.items():
            info_x = info_spec.format(
                referencefeatures = " ".join(et.list_ref_noskip()),
                myobjects = '{myobjects}',
                subpart = '{subpart}',
            )
            if ftype_spec.startswith('f_'):
                partspec = ftype_spec.replace('f_', '', 1)
                components = partspec.split('.')
                part = components[0]
                if len(components) > 1:
                    subpart = components[1]
                    if subpart != '*':
                        todo += [(part, subpart, ftype_spec, info_x.format(
                            myobjects = " ".join(et.object_list_part(part)),
                            subpart = components[1],
                        ))]
                    else:
                        for subpart in et.subpart_list(part):
                            if subpart == '': continue
                            ftype_spec_x = ftype_spec.replace('*', subpart)
                            todo += [(part, subpart, ftype_spec_x, info_x.format(
                                myobjects = " ".join(et.object_list(part, subpart)),
                                subpart = subpart,
                            ))]
                else:
                    todo += [(part, '', ftype_spec, info_x.format(
                        myobjects = " ".join(et.object_list_part(part)),
                    ))]
            else:
                partspec = ftype_spec.replace('f.', '', 1)
                todo += [('', partspec, ftype_spec, info_x)]
        regions = settings.annotation_regions
# now the todo list is interpreted further, especially the info string.
# The result is stored in a dictionary keyed by part, then subpart.
        for (part, subpart, ftype, infostring) in todo:
            self.file_order += [ftype]
            (location, medium, annotstring, requirestring) = fillup(4, '', infostring.split('&'))
            annotations = annotstring.split(" ") if annotstring != '' else []
            requires = requirestring.split(" ") if requirestring != '' else []
            self.annotation_files[part][subpart] = (ftype, medium, location, requires, annotations, subpart == regions['name'])
# read and store the templates
        laf_templates = settings.laf_templates
        for tpl in laf_templates:
            (fname, nl_before) = laf_templates[tpl]
            file_handle = open('{}/{}'.format(settings.env['template_dir'], fname), encoding = 'utf-8')
            template = file_handle.read()
            file_handle.close()
            self.template[tpl] = ("\n" + template.rstrip("\n")) if  nl_before else template
        
    def makeheaders(self):
        if not self.et.simple or self.et.plain:
            self.makefeatureheader()
        if not self.settings.args.fdecls_only:
            self.makeresourceheader()
            self.makeprimaryheader()

    def makefeatureheader(self):
        f_text = collections.defaultdict(lambda: '')
        f_index = 0
        iso_prefix = self.settings.meta['ISOcatprefix']
        truth_values = sorted(self.settings.type_boolean.values())
        db_label = self.settings.annotation_label['db_label']
        meta = self.settings.meta
        plain_info = collections.defaultdict(lambda: {})
        plain_iso_info = {}
        for db_feature in (
            ('monads', 'monads', 'integer', 'the monads that belong to this object'),
            ('minmonad', 'minmonad', 'integer', 'the first monad of this object'),
            ('maxmonad', 'maxmonad', 'integer', 'the last monad of this object'),
            ('oid', 'objectId', 'integer', 'object identifier'),
            ('otype', 'objectType', 'string', 'object type'),
        ):
            (fname, longfname, ftype, descr) = db_feature
            f_index += 1
            (fs_type, fs_type_atts) = fillup(2, '', self.settings.type_mapping[ftype].split('&'))
            if fs_type_atts != '': fs_type_atts = ' ' + fs_type_atts
            fv_text = self.template['feature_basic'].format(valtype = fs_type, atts = fs_type_atts, **meta)
            f_text[db_label] += self.template['feature_local'].format(i = f_index, name = fname, isoname = longfname, isodescr = 'database value:' + descr,
                values = fv_text, **meta
            )
        if self.et.plain:
            fpfile = self.settings.env['feature_plain_info']
            with open(fpfile, 'r', encoding='utf-8') as fh:
                for line in fh:
                    if line.startswith('#'): continue
                    (otype, fname, local_name, ftype, iso_name, iso_id, iso_def, iso_exm, iso_exp) = fillup(9, '', line.rstrip().split("\t"))
                    if iso_def != 'idem.':
                        plain_iso_info[iso_id] = (iso_name, iso_def, iso_exm, iso_exp)
                    plain_info[otype][fname] = (local_name, iso_id)
            for part in sorted(self.et.part_feature):
                for object_type in sorted(self.et.part_feature[part]):
                    if object_type not in plain_info:
                        print("ERROR: object type {} not specified".format(object_type))
                        continue
                    object_kind = self.settings.annotation_label[part + '_label']
                    for feature_name in sorted(self.et.part_feature[part][object_type]):
                        if self.et.is_ref_skip(feature_name): continue
                        if feature_name not in plain_info[object_type]:
                            print("ERROR: feature {} of object type {} not specified".format(feature_name, object_type))
                            continue
                        (local_name, iso_id) = plain_info[object_type][feature_name]
                        (iso_name, iso_def, iso_exm, iso_exp) = plain_iso_info[iso_id]
                        f_index += 1
                        fv_text = self.template['feature_basic'].format(valtype = 'string', atts = fs_type_atts, **meta)
                        f_text[object_kind] += self.template['feature'].format(i = f_index, name = feature_name,
                            isoname = iso_name,
                            isolink = iso_prefix + iso_id,
                            isodescr = 'name in local documentation: {}. {}{}{}'.format(
                                local_name,
                                ('Definition: ' + iso_def.rstrip('.') + '. ') if iso_def else '',
                                ('Example: ' + iso_exm.rstrip('.') + '. ') if iso_exm else '',
                                ('Explanation: ' + iso_exp.rstrip('.') + '. ') if iso_exp else '',
                            ),
                            values = fv_text, **meta
                        )
        else:
            for part in self.et.part_list():
                for object_type in self.et.object_list_part(part):
                    object_kind = self.settings.annotation_label[part + '_label']
                    f_index += 1
                    isocat_key, isocat_name = self.et.object_atts(object_type)
                    fv_text = self.template['feature_basic'].format(valtype = 'string', atts = '', **meta)
                    f_text[object_kind] += self.template['feature'].format(i = f_index, name = object_type,
                        isoname = camel(isocat_name) if isocat_name != '' else object_type + '_object',
                        isolink = iso_prefix + isocat_key, isodescr = isocat_name if isocat_name != '' else 'MISSING ISOcat name',
                        values = fv_text, **meta
                    )
                    for feature_name in self.et.feature_list(object_type):
                        defined_on, etcbc_type, isocat_key, isocat_name = self.et.feature_atts(object_type, feature_name)
                        if defined_on != '': continue
                        if self.et.is_ref_skip(feature_name): continue
                        (fs_type, fs_type_atts) = fillup(2, '', self.settings.type_mapping[etcbc_type].split('&'))
                        if fs_type_atts != '': fs_type_atts = ' ' + fs_type_atts
                        f_index += 1
                        value_list = self.et.value_list(object_type, feature_name)
                        fv_text = ''
                        if len(value_list) > 0:
                            fv1_text = ''
                            for feature_value in value_list:
                                v_etcbc_type, v_isocat_key, v_isocat_name = self.et.value_atts(object_type, feature_name, feature_value)
                                fv1_text += self.template['feature_val1'].format(valtype = 'symbol', name = feature_value,
                                    value = camel(v_isocat_name) if v_isocat_name != '' else feature_value,
                                    isolink = iso_prefix + v_isocat_key, **meta
                                )
                            fv_text = self.template['feature_val'].format(values = fv1_text, **meta)
                        if fs_type != 'symbol':
                            if fs_type == 'binary':
                                fv1_text = ''
                                for feature_value in truth_values:
                                    fv1_text += "\n\t\t\t\t" + '<{} value="{}"/>'.format(fs_type, feature_value)
                                fv_text = self.template['feature_val'].format(values = fv1_text, **meta)
                            else:
                                fv_text = self.template['feature_basic'].format(valtype = fs_type, atts = fs_type_atts, **meta)
                        f_text[object_kind] += self.template['feature'].format(i = f_index, name = feature_name,
                            isoname = camel(isocat_name) if isocat_name != '' else feature_name,
                            isolink = iso_prefix + isocat_key, isodescr = isocat_name if isocat_name != '' else 'MISSING ISOcat name',
                            values = fv_text, **meta
                        )
        for feature_type in f_text:
            absolute_path = "{}/{}.xml".format(self.settings.env['decl_dst_dir'], feature_type)
            file_handle = open(absolute_path, "w", encoding = 'utf-8')
            text = self.template['feature_decl'].format(kind = feature_type, features = f_text[feature_type], **meta)
            file_handle.write(text) 
            file_handle.close()
            self.val.add(absolute_path, self.settings.xml['tei_fs_dst'])

    def makeresourceheader(self):
        absolute_path = self.settings.env['resource_hdr_txt']
        file_handle = open(absolute_path, "w", encoding = 'utf-8')
# generate the variable parts: the list of filetypes, the specification of file types
        filetypes_decl = ''
        annotation_decls = ''
        meta = self.settings.meta
        for part in sorted(self.annotation_files):
            for subpart in sorted(self.annotation_files[part]):
                ftype, medium, location, requires, annotations, is_region = self.annotation_files[part][subpart]
                dependencies = ''
                for dep in requires:
                    dependencies += self.template['dependency'].format(indent = "\t\t", elementname = self.settings.laf['resource_header'], fileid = dep, **meta)
                requirestxt = "/>"
                if requires:
                    requirestxt = ">" + dependencies + "\n\t\t\t\t</fileType>"
                filetypes_decl += ("\n\t\t\t\t" + '<fileType xml:id="{type}" f.suffix="{suffix}" {aids}medium="{medium}"{requires}').format(
                    type = ftype,
                    suffix = location,
                    medium = medium,
                    aids = 'a.ids="{}" '.format(" ".join(annotations)) if len(annotations) > 0 else '',
                    requires = requirestxt,
                )
        filetypes_list = ''
        for ftype in self.file_order: filetypes_list += "\n\t\t\t\t\t{}".format(ftype)
        danspid = self.settings.meta['danspid_act']
        decl_items = [('reference', self.et.list_ref_noskip())]
        skips = self.settings.annotation_skip_object
        for part in self.et.part_list():
            skip_objects = set()
            if part in skips: skip_objects.add(skips[part])
            decl_items.append((part, sorted(x for x in self.et.object_list_part(part) if x not in skip_objects)))
        plabels = self.settings.annotation_label
        labels = set()
        for plabel in plabels: labels.add(plabels[plabel])
        for label in sorted(labels): decl_items.append((label, [label]))
        for decl_item in decl_items:
            itemtype, items = decl_item
            info = self.settings.annotation_kind[itemtype]
            descr, schematype, schemaloc = info.split('&')
            for item in items:
                schema = danspid
                if schematype == 'fsDecl': schema = '{}/{}'.format(danspid, schemaloc)
                annotation_decls += self.template['annotation_decl'].format(name = item, kind = descr, schema = schema, schematype = schematype, **meta)
        text = self.template['resource_hdr'].format(createdate = today(), filetypeslist = filetypes_list, filetypesdecl = filetypes_decl,
            annotationdecls = annotation_decls, nmonads = self.gstats['f Number of monads'], **meta).format(nmonads = self.gstats['f Number of monads'], **meta)
        file_handle.write(text)
        file_handle.close()
        self.val.add(absolute_path, self.settings.xml['graf_resource_dst'])

    def makeprimaryheader(self):
        absolute_path = self.settings.env['primary_hdr_txt']
        file_handle = open(absolute_path, "w", encoding = 'utf-8')
        danspid = self.settings.meta['danspid_act']
        annotation_item_dict = {} 
        meta = self.settings.meta
        for part in sorted(self.annotation_files):
            if part == '': continue
            for subpart in sorted(self.annotation_files[part]):
                ftype, medium, location, requires, annotations, is_region = self.annotation_files[part][subpart]
                annotation_item_dict[ftype] = self.template['annotation_item'].format(id = ftype, loc = location, **meta)
        annotation_items = ''
        for ftype in self.file_order:
            if ftype in annotation_item_dict: annotation_items += annotation_item_dict[ftype]
        text = self.template['primary_hdr'].format(createdate = today(), charsize = self.stats['charsize'], annotationitems = annotation_items, **meta)
        file_handle.write(text)
        file_handle.close()
        self.val.add(absolute_path, self.settings.xml['graf_document_dst'])

    def start_annot(self, part):
        print("INFO: Generating annotation files for {}".format(part))
        self.file_handles = {}
        meta = self.settings.meta
        for subpart in self.annotation_files[part]:
            (ftype, medium, location, requires, annotations, is_region) = self.annotation_files[part][subpart]
            absolute_path = "{}{}".format(self.settings.env['annot_hdr'], location)
            annotation_labels = ''
            for annot in annotations:
                annotation_labels += self.template['annotation_label'].format(annot = annot, **meta)
            dependencies = ''
            for dep in requires:
                dependencies += self.template['dependency'].format(indent = "", elementname = self.settings.laf['annotation_header'], fileid = dep, **meta)
            if dependencies and 'comment_local_deps' in self.settings.laf_switches:
                dependencies = "<!--" + dependencies + "-->"
            annotation_header = ''
            if is_region:
                annotation_header = self.template['region_hdr'].format(dependencies = dependencies, **meta)
            else:
                annotation_header = self.template['annotation_hdr'].format(labels = annotation_labels, dependencies = dependencies, **meta)
            file_handle = open(absolute_path, "w", encoding = 'utf-8')
            file_handle.write(annotation_header)
            file_handle.close()
            file_handle = open(absolute_path, "a", encoding = 'utf-8')
            self.file_handles[subpart] = (file_handle, absolute_path, len(annotation_header), annotations)

    def start_primary(self):
        ftype, medium, location, requires, annotations, is_region = self.annotation_files['']['primary']
        absolute_path = self.settings.env['primary_text']
        self.primary_handle = open(absolute_path, "w", encoding = 'utf-8')

    def finish_annot(self, part):
        meta = self.settings.meta
        for subpart in self.file_handles:
            file_handle, absolute_path, length, annotations = self.file_handles[subpart]
            file_handle.write(self.template['annotation_ftr'].format(**meta))
            file_handle.close()
            file_handle = open(absolute_path, "r+")
            header = file_handle.read(length)
            for annot in annotations:
                number_annot = '"{}"'.format(self.stats["{}.{}".format(subpart, annot)]).ljust(14, ' ')
                header = re.sub('"{}" occurs="nnnnnnnnnnnn"'.format(annot), '"{}" occurs={}'.format(annot, number_annot), header)
            file_handle.seek(0)
            file_handle.write(header)
            file_handle.close()
            self.val.add(absolute_path, self.settings.xml['graf_annot_dst'])

    def finish_primary(self):
        ftype, medium, location, requires, annotations, is_region = self.annotation_files['']['primary']
        absolute_path = self.settings.env['primary_text']
        self.primary_handle.close()
        self.val.add(absolute_path, None)

    def report(self):
        for stat in sorted(self.gstats): print("INFO: {:<30}: {:>10}".format(stat, self.gstats[stat]))
