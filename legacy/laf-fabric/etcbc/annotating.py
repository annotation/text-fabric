import sys
import collections

def nonerep(val):
    return '' if val == None else val

class GenForm(object):
    '''Generates input forms for new annotations and creates new annotations based on filled in forms.
    '''

    def __init__(self, API, form_name, config):
        '''Upon creation, takes in the config information for a new form.

        Args:
            API(object):
                the API object of the LAF processor, so that the form creator can use its methods for 
                creating files and issuing messages and accessing features.
            
            form_name(string): the base name of the form to be created

            config(dict): which nodes and feature data to fill the form with, which new feature columns to make.
        '''
        self.API = API
        self.name = form_name
        self.config = config

        self.target_types = config['target_types']
        self.type_col = {}
        self.n_types = len(self.target_types)
        for (n, tt) in enumerate(self.target_types):
            self.type_col[tt] = n

        new_features_spec = config['new_features']
        self.new_fqnames = []
        new_fnames = []
        self.new_features = []
        for aspace in sorted(new_features_spec.keys()):
            for kind in sorted(new_features_spec[aspace].keys()):
                for line in new_features_spec[aspace][kind]:
                    (alabel, fnames) = line.split('.')
                    for fname in fnames.split(','):
                        fqname = "{}:{}.{}".format(aspace, alabel, fname)
                        self.new_fqnames.append(fqname)
                        self.new_features.append((aspace, alabel, fname))
                        new_fnames.append(fname)
        self.n_new_features = len(self.new_fqnames)

        show_features_spec = config['show_features']
        show_fqnames = []
        self.show_fnames = []
        self.show_features = []
        for aspace in sorted(show_features_spec.keys()):
            for kind in sorted(show_features_spec[aspace].keys()):
                for line in show_features_spec[aspace][kind]:
                    (alabel, fnames) = line.split('.')
                    for fname in fnames.split(','):
                        fqname = "{}:{}.{}".format(aspace, alabel, fname)
                        show_fqnames.append(fqname)
                        self.show_features.append((aspace, alabel, fname))
                        self.show_fnames.append(fname.replace('_',' '))
        self.n_show_features = len(show_fqnames)

    def make_form(self):
        '''Creates a form based on the information passed when creating this object.
        '''
        msg = self.API['msg']
        outfile = self.API['outfile']
        F = self.API['F']
        NN = self.API['NN']
        X = self.API['X']
        P = self.API['P']
        msg("Reading the data ...")
        outf = outfile("form_{}.csv".format(self.name))

        the_book = None
        the_chapter = None
        the_verse = None
        in_book = False
        in_chapter = False
        do_chapters = {}
        outf.write("{}\t{}\t{}\t{}\n".format(
            'passage',
            "\t".join(self.target_types),
            "\t".join(self.show_fnames),
            "\t".join(self.new_fqnames),
        ))
        for i in NN():
            this_type = F.db_otype.v(i)
            if this_type in self.target_types:
                if in_chapter:
                    the_xml_id = X.r(i)
                    the_text = " ".join([text for (n, text) in P.data(i)])
                    the_show_features = "\t".join([nonerep(F.item["{}_{}_{}".format(*sf)].v(i)) for sf in self.show_features])
                    outf.write("{}\t{}{}{}{}{}\n".format(
                        the_xml_id,
                        "\t" * self.type_col[this_type],
                        the_text,
                        "\t" * (self.n_types - self.type_col[this_type]),
                        the_show_features,
                        "\t" * self.n_new_features,
                    ))
            elif this_type == "book":
                the_book = F.sft_book.v(i)
                in_book = the_book in self.config['passages']
                if in_book:
                    sys.stderr.write(the_book)
                    do_chapters = {}
                    chapter_ranges = self.config['passages'][the_book].split(',')
                    for chapter_range in chapter_ranges:
                        boundaries = chapter_range.split('-')
                        (b, e) = (None, None)
                        if len(boundaries) == 1:
                            b = int(chapter_range)
                            e = int(chapter_range) + 1
                        else:
                            b = int(boundaries[0])
                            e = int(boundaries[1]) + 1
                        for chapter in range(b, e):
                            do_chapters[str(chapter)] = None
                else:
                    sys.stderr.write("*")
            elif this_type == "chapter":
                if in_book:
                    the_chapter = F.sft_chapter.v(i)
                    if the_chapter in do_chapters:
                        sys.stderr.write("{},".format(the_chapter))
                        in_chapter = True
                    else:
                        in_chapter = False
                else:
                    in_chapter = False
            elif this_type == "verse":
                if in_chapter:
                    the_verse = F.sft_verse.v(i)
                    outf.write("#{} {}:{}\t{}\t{}\n".format(
                        the_book,
                        the_chapter,
                        the_verse,
                        "\t" * self.n_types,
                        "\t" * self.n_new_features,
                    ))
        outf.close()
        msg("Done")

    def make_annots(self):
        '''Converts a filled in form into a set of new annotations.
        '''
        infile = self.API['infile']
        outfile = self.API['outfile']

        inp = infile("data_{}.csv".format(self.name))
        outa = outfile("annot_{}.xml".format(self.name))
        outa.write('''<?xml version="1.0" encoding="UTF-8"?>
    <graph xmlns="http://www.xces.org/ns/GrAF/1.0/" xmlns:graf="http://www.xces.org/ns/GrAF/1.0/">
    <graphHeader>
        <labelsDecl/>
        <dependencies/>
        <annotationSpaces/>
    </graphHeader>
    ''')
        aid = 0
        header = True
        features = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: {})))
        for line in inp:
            if header:
                header = False
                continue
            if line.startswith('#'):
                continue
            fields = line.rstrip().split("\t")
            xml_id = fields[0]
            values = fields[self.n_types + self.n_show_features + 1:self.n_types + self.n_show_features + 1 + self.n_new_features]
            for (n, value) in enumerate(values): 
                if value == "":
                    continue
                (aspace, alabel, fname) = self.new_features[n]
                features[aspace][alabel][xml_id][fname] = value

        for aspace in features:
            for alabel in features[aspace]:
                for xml_id in features[aspace][alabel]:
                    aid += 1
                    outa.write('<a xml:id="a{}" as="{}" label="{}" ref="{}"><fs>\n'.format(aid, aspace, alabel, xml_id))
                    for fname in features[aspace][alabel][xml_id]:
                        value = features[aspace][alabel][xml_id][fname]
                        outa.write('\t<f name="{}" value="{}"/>\n'.format(fname, value))
                    outa.write('</fs></a>\n')
        outa.write("</graph>\n")        
        inp.close()
        outa.close()

def create_annots(API, data):
    '''Converts a list of node, value,feature entries to a string which can be saved as an annotation file.

    The columns must be: nodeid, value, feature name, feature_label (optional), namespace (optional)
    '''
    result = []
    result.append('''<?xml version="1.0" encoding="UTF-8"?>
<graph xmlns="http://www.xces.org/ns/GrAF/1.0/" xmlns:graf="http://www.xces.org/ns/GrAF/1.0/">
<graphHeader>
    <labelsDecl/>
    <dependencies/>
    <annotationSpaces/>
</graphHeader>''')
    aid = 0
    features = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: {})))
    for line in data:
        node = line[0]
        value = line[1]
        feat = line[2]
        if len(line) > 3:
            feat = "{}.{}".format(line[3], feat)
        if len(line) > 4:
            feat = "{}:{}".format(line[4], feat)
        (aspace, alabel, fname) = API['fabric'].resolve_feature('node', feat)
        xml_id = API['X'].r(node)
        features[aspace][alabel][xml_id][fname] = value

    for aspace in features:
        for alabel in features[aspace]:
            for xml_id in features[aspace][alabel]:
                aid += 1
                result.append('<a xml:id="a{}" as="{}" label="{}" ref="{}"><fs>'.format(aid, aspace, alabel, xml_id))
                for fname in features[aspace][alabel][xml_id]:
                    value = features[aspace][alabel][xml_id][fname]
                    result.append('\t<f name="{}" value="{}"/>'.format(fname, value))
                result.append('</fs></a>')
    result.append("</graph>")        
    return '\n'.join(result)
