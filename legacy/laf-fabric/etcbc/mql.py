import subprocess
from lxml import etree

#MQL_PROC = '/usr/local/bin/mql'
MQL_PROC = 'mql'
MQL_OPTS = ['--cxml', '-b', 's3', '-d']

F = None
NN = None

class MQL(object):
    index2node = {}
    node2verse = {}
    node2sentence = {}
    object2words = {}

    def __init__(self, API):
        global F
        global NN
        env = API['fabric'].lafapi.names.env
        self.data_path = env['source_xdata']
        self.parser = etree.XMLParser(remove_blank_text=True)
        NN = API['NN']
        F = API['F']
        cur_object = {}
        for n in NN():
            otype = F.db_otype.v(n)
            if otype != 'word': cur_object[otype] = n
            if otype == 'word':
                for curo in cur_object.values():
                    MQL.object2words.setdefault(curo, []).append(n)
            MQL.index2node[F.db_oid.v(n)] = n
            MQL.node2verse[n] = cur_object.get('verse', None)
            MQL.node2sentence[n] = cur_object.get('sentence', None)

    def mql(self, query, format='sheaf'):
        proc = subprocess.Popen(
            [MQL_PROC] + MQL_OPTS + [self.data_path],
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )
        proc.stdin.write(bytes(query, encoding='utf8'))
        proc.stdin.close()
        xml = proc.stdout.read()
        if format == 'xml':
            return xml
        elif format == None or format == 'sheaf':
            sheaf = self._parse_results(xml)
            return Sheaf(sheaf)

    def _parse_results(self, xml):
        root = etree.fromstring(xml, self.parser)
        results = [MQL._parse_result(child) for child in root]
        nres = len(results)
        if nres > 1:
            print("WARNING: multiple results: {}".format(nres))
            return None
        return results[0] if nres else []
            
    def _parse_result(elem):
        results = [MQL._parse_sheaf(child) for child in elem if child.tag == 'sheaf']
        nres = len(results)
        return results[0] if nres else []

    def _parse_sheaf(elem):
        return [MQL._parse_straw(child) for child in elem]

    def _parse_straw(elem):
        return [MQL._parse_grain(child) for child in elem]

    def _parse_grain(elem):
        node = MQL.index2node[elem.attrib["id_d"]]
        result = (node,)
        for child in elem:
            if child.tag == 'sheaf' and len(child):
                result = (node, MQL._parse_sheaf(child))
                break
        return result

    def _results_sheaf(sheaf, limit=None):
        yielded = 0
        if sheaf == None: return
        for straw in sheaf:
            for result in MQL._results_straw(straw):
                if limit != None and yielded >= limit: return
                yielded += 1
                yield result

    def _results_straw(straw):
        if not(len(straw)):
            yield ()
        else:
            for t in MQL._results_grain(straw[0]):
                for a in MQL._results_straw(straw[1:]):
                    yield tuple((t,) + a)

    def _results_grain(grain):
        if len(grain) == 1:
            yield grain
        else:
            for r in MQL._results_sheaf(grain[1]):
                yield (grain[0], r)
                    
    def _render_sheaf(data, indent, monadrep):
        if data == None or not len(data):
            print("Empty sheaf")
        else:
            for (i, elem) in enumerate(data):
                if i>0: print("{}--".format(' '*indent))
                MQL._render_straw(elem, indent+1, monadrep)
        
    def _render_straw(data, indent, monadrep):
        if len(data):
            for elem in data:
                MQL._render_grain(elem, indent+1, monadrep)
            
    def _render_grain(data, indent, monadrep):
        otype = F.db_otype.v(data[0])
        if otype == 'word':
            print("{}'{}'".format(' '*indent, monadrep(data[0])))
        else:
            print("{}[{}".format(' '*indent, F.db_otype.v(data[0])))
            if len(data) > 1:
                MQL._render_sheaf(data[1], indent+1, monadrep)
            print("{}]".format(' '*indent))

    def _compact_sheaf(data, level, monadrep):
        if data == None: return ''
        sep = '\n' if level == 0 else ' -- '
        return sep.join([MQL._compact_straw(elem, level+1, monadrep) for elem in data])
            
    def _compact_straw(data, level, monadrep):
        return ' '.join([MQL._compact_grain(elem, level, monadrep) for elem in data])

    def _compact_grain(data, level, monadrep):
        otype = F.db_otype.v(data[0])
        if otype == 'word':
            return "'{}'".format(monadrep(data[0]))
        else:
            subdata = data[1] if len(data) > 1 else []
            return "[{} {}]".format(F.db_otype.v(data[0]), MQL._compact_sheaf(subdata, level, monadrep))

    def _compact_results(data, level, monadrep, passages, sentence):
        if data == None: return ''
        sep = '\n' if level == 0 else ' -- '
        return sep.join([MQL._compact_result(elem, level+1, monadrep, passages, sentence) for elem in data])

    def _compact_result(data, level, monadrep, passages, sentence):
        return ' '.join([MQL._compact_resgrain(elem, level, monadrep, passages, sentence) for elem in data])

    def _compact_resgrain(data, level, monadrep, passages, sentence):
        passage = ''
        sentext = ''
        if level == 1:
            if passages:
                verse = MQL.node2verse[data[0]]
                passage = "{} ".format(F.verse_label.v(verse))
            if sentence:
                sent = MQL.node2sentence[data[0]]
                sentext = '{} '.format(' '.join(monadrep(w) for w in MQL.object2words[sent]))

        otype = F.db_otype.v(data[0])
        if otype == 'word':
            return "{}{} '{}'".format(passage,sentext, monadrep(data[0]))
        else:
            subdata = data[1] if len(data) > 1 else []
            return "{}{} [{} {}]".format(passage, sentext, F.db_otype.v(data[0]), MQL._compact_result(subdata, level+1, monadrep, passages, sentence))


class Sheaf(object):
    def __init__(self, sheaf): self.data = sheaf
    def render(self, monadrep): MQL._render_sheaf(self.data, 0, monadrep)
    def compact(self, monadrep): return MQL._compact_sheaf(self.data, 0, monadrep)
    def results(self): return MQL._results_sheaf(self.data)
    def nresults(self):
        i = 0;
        for r in MQL._results_sheaf(self.data): i += 1
        return i
    def compact_results(self, monadrep, passages=None, sentence=None, limit=None):
        return MQL._compact_results(MQL._results_sheaf(self.data, limit=limit), 0, monadrep, passages, sentence)
