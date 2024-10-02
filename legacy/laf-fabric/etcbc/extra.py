import os
import collections
import re

class ExtraData(object):
    def __init__(self, API):
        self.API = API
        self.env = API['fabric'].lafapi.names.env
        NN = API['NN']
        F = API['F']
        msg = API['msg']

        cur_subtract = 0
        cur_chapter_cas = 0

    def create_annots(self, data, spec):
        API = self.API
        X = API['X']
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
            xml_id = X.r(node)
            for (n, (aspace, alabel, fname)) in enumerate(spec):
                features[aspace][alabel][xml_id][fname] = line[n+1]
            
        for aspace in sorted(features):
            for alabel in sorted(features[aspace]):
                for xml_id in sorted(features[aspace][alabel]):
                    aid += 1
                    result.append('''<a xml:id="a{}" as="{}" label="{}" ref="{}"><fs>'''.format(aid, aspace, alabel, xml_id))
                    for fname in sorted(features[aspace][alabel][xml_id]):
                        value = str(features[aspace][alabel][xml_id][fname])
                        value = value.replace('&', '&amp;').\
                            replace('<', '&lt;').\
                            replace('>', '&gt;').\
                            replace('"', '&quot;').\
                            replace('\n', '&#xa;')
                        result.append('\t<f name="{}" value="{}"/>'.format(fname, value))
                    result.append('</fs></a>')
        result.append("</graph>")
        return '\n'.join(result)

    def create_header(self, annox_parts, metadata):
        result = []
        if type(annox_parts) is str:
            annox_parts = [annox_parts]
        result.append("""<?xml version="1.0" encoding="UTF-8"?>
    <documentHeader xmlns="http://www.xces.org/ns/GrAF/1.0/" xmlns:graf="http://www.xces.org/ns/GrAF/1.0/" docId="http://persistent-identifier/?identifier=urn:nbn:nl:ui:13-xxx-999" creator="SHEBANQ" date.created="2013-12-05" version="1.0">
      <fileDesc>
        <titleStmt>
          <title>{title}</title>
        </titleStmt>
        <extent count="0" unit="byte"/>
        <sourceDesc>
          <title>ETCBC4 Hebrew Text Database</title>
          <author>ETCBC team</author>
          <publisher>Eep Talstra Centre for Bible and Computer, VU University</publisher>
          <pubDate>{date}</pubDate>
          <pubPlace>Amsterdam</pubPlace>
        </sourceDesc>
      </fileDesc>
      <profileDesc>
        <primaryData f.id="f.primary" loc="{source}.txt"/>
        <langUsage>
            <language iso639="hbo"/> <!-- ancient hebrew http://www-01.sil.org/iso639-3/documentation.asp?id=hbo -->
            <language iso639="arc"/> <!-- aramaic http://www-01.sil.org/iso639-3/documentation.asp?id=arc -->
        </langUsage>
        <annotations>
""".format(source=self.env['source'], **metadata))
        for annox_part in annox_parts:
            result.append("""
            <annotation f.id="f_{key}" loc="{key}.xml"/>
""".format(key=annox_part))
        result.append("""
        </annotations>
      </profileDesc>
    </documentHeader>""")
        
        return '\n'.join(result)

    def deliver_annots_single(self, data_base, annox, annox_part, read_method, specs, metadata):
        API = self.API
        data_dir = API['data_dir']
        annox_data = read_method('{}/{}'.format(data_dir, data_base))
        annox_dir = "{}/{}/annotations/{}".format(data_dir, self.env['source'], annox)
        if not os.path.exists(annox_dir): os.makedirs(annox_dir)
        with open("{}/_header_.xml".format(annox_dir), "w") as ah: ah.write(self.create_header(annox_part, metadata))
        with open("{}/{}.xml".format(annox_dir, annox_part), "w") as ah: ah.write(self.create_annots(annox_data, specs))

    def deliver_annots(self, annox, metadata, sets):
        if type(sets) is tuple:
            sets = [sets]
        API = self.API
        data_dir = API['data_dir']
        annox_dir = "{}/{}/annotations/{}".format(data_dir, self.env['source'], annox)
        annox_parts = []
        if not os.path.exists(annox_dir): os.makedirs(annox_dir)
        for (data_base, annox_part, read_method, specs) in sets:
            annox_parts.append(annox_part)
            annox_data = read_method('{}/{}'.format(data_dir, data_base))
            with open("{}/{}.xml".format(annox_dir, annox_part), "w") as ah: ah.write(self.create_annots(annox_data, specs))
        with open("{}/_header_.xml".format(annox_dir), "w") as ah: ah.write(self.create_header(annox_parts, metadata))

