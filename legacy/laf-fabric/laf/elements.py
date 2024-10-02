from .lib import grouper
from .names import Names

class Feature(object):
    '''Feature data and lookup.

    Holds the mapping from nodes/edges to values corresponding to a single feature.
    Has distinct mappings for main source data and annox data.

    ``v(node_or_edge)`` is the lookup method.
    ``s(value=None)`` yields the nodes/edges that have this value or any value.
    '''
    def __init__(self, lafapi, feature, kind):
        env = lafapi.names.env
        self.source = lafapi
        self.kind = kind
        data_items = lafapi.data_items
        label = Names.comp('mF' + kind + '0', feature)
        alabels = [Names.comp('a{}:F{}0'.format(anx, kind), feature) for anx in env['annox']] 
        self.lookup = data_items[label] if label in data_items else {}
        self.alookup = {}
        for alabel in alabels:
            if alabel in data_items: self.alookup.update(data_items[alabel])

    def v(self, ne): return self.alookup.get(ne, self.lookup.get(ne))
    def V(self, ne): return self.lookup.get(ne)

    def s(self, value=None):
        data_items = self.source.data_items
        order = data_items[Names.comp('mG00', ('node_sort_inv',))]
        domain = sorted(set(self.lookup) | set(self.alookup), key=lambda x:order[x])
        if value == None:
            for n in domain: yield n
        else:
            for n in domain:
                if self.alookup.get(n, self.lookup.get(n)) == value: yield n

class Connection(object):
    '''Connection info according to an edge feature.

    Holds the mapping from nodes to a set of ``(node, value)`` pairs for which there is
    an edge for which this edge feature has ``value``.
    Has distinct mappings for main source data and annox data.

    ``v(node)`` yields the nodes (without the values).
    ``vv(node)`` yields the node/value pairs.
    ``endnodes(nodeset, value=None) yields the set of end nodes after traveling from ``nodeset`` along edges
    (having this feature with this value or any value).
    '''
    def __init__(self, lafapi, feature, inv):
        env = lafapi.names.env
        self.lafapi = lafapi
        self.inv = inv
        data_items = lafapi.data_items
        label = Names.comp('mC0' + inv, feature)
        alabels = [Names.comp('a{}:C0{}'.format(anx, inv), feature) for anx in env['annox']] 
        self.lookup = data_items[label] if label in data_items else {}
        self.alookup = {}
        for alabel in alabels:
            if alabel in data_items: self.alookup.update(data_items[alabel])

    def e(self, n): return len(self.lookup.get(n, {})) or len(self.alookup.get(n, {}))

    def v(self, n, sort=False):
        lookup = self.lookup
        alookup = self.alookup
        if sort:
            cn = lookup.get(n, {})
            cn.update(alookup.get(n, {}))
            data_items = self.lafapi.data_items
            order = data_items[Names.comp('mG00', ('node_sort_inv',))]
            for x in sorted(cn.keys(), key=lambda x:order[x]): yield x
        else:
            for x in alookup.get(n, {}).keys(): yield x
            for x in lookup.get(n, {}).keys(): yield x

    def vv(self, n, sort=False):
        lookup = self.lookup
        alookup = self.alookup
        if sort:
            cn = lookup.get(n, {})
            cn.update(alookup.get(n, {}))
            data_items = self.lafapi.data_items
            order = data_items[Names.comp('mG00', ('node_sort_inv',))]
            for x in sorted(cn.items(), key=lambda x:order[x[0]]): yield x
        else:
            for x in alookup.get(n, {}).items(): yield x
            for x in lookup.get(n, {}).items(): yield x

    def endnodes(self, node_set, value=None, sort=False):
        data_items = self.lafapi.data_items
        order = data_items[Names.comp('mG00', ('node_sort_inv',))]
        visited = set()
        result = set()
        next_set = set(node_set)
        while next_set:
            new_next_set = set()
            for node in next_set:
                visited.add(node)
                next_nodes = set(self.v(node)) if value == None else set([n[0] for n in self.vv(node) if n[1] == value])
                if next_nodes: new_next_set |= next_nodes - visited
                else: result.add(node)
            next_set = new_next_set
        the_nodes = sorted(result, key=lambda x:order[x]) if sort else result
        for n in the_nodes: yield n

class XMLid(object):
    '''Mappings between XML identifiers in original LAF resource and integers identifying nodes and edges in compiled data.

    ``r(node or edge int) = xml identifier`` and ``i(xml identifier) = node or edge int``.
    '''
    def __init__(self, lafapi, kind):
        env = lafapi.names.env
        self.kind = kind
        data_items = lafapi.data_items
        label = Names.comp('mX' + kind + 'f', ())
        rlabel = Names.comp('mX' + kind + 'b', ())
        alabels = [Names.comp('a{}:X{}f'.format(anx, kind), ()) for anx in env['annox']] 
        arlabels = [Names.comp('a{}:X{}b'.format(anx, kind), ()) for anx in env['annox']] 
        self.lookup = data_items[label] if label in data_items else {}
        self.rlookup = data_items[rlabel] if rlabel in data_items else {}
        self.alookup = {}
        self.arlookup = {}
        for alabel in alabels:
            if alabel in data_items: self.alookup.update(data_items[alabel])
        for arlabel in arlabels:
            if arlabel in data_items: self.arlookup.update(data_items[arlabel])

    def r(self, int_code): return self.arlookup.get(int_code, self.rlookup.get(int_code))
    def i(self, xml_id): return self.alookup.get(xml_id, self.lookup.get(xml_id))

class PrimaryData(object):
    '''Primary data.

    ``data(node)`` is a list of chunks of primary data attached to that node.
    The chunk is delivered as a pair of the position where the chunk starts and the chunk itself.
    Empty chunks are possible. Consecutive chunks have been merged. The chunks appear in primary data order.
    '''
    def __init__(self, lafapi):
        self.all_data = lafapi.data_items[Names.comp('mP00', ('primary_data',))]
        self.lafapi = lafapi

    def data(self, node):
        lafapi = self.lafapi
        regions = lafapi._getitems(
            lafapi.data_items[Names.comp('mP00', ('node_anchor',))],
            lafapi.data_items[Names.comp('mP00', ('node_anchor_items',))],
            node,
        )
        if not regions: return None
        all_text = self.all_data
        result = []
        for r in grouper(regions, 2): result.append((r[0], all_text[r[0]:r[1]]))
        return result

