import array
from .lib import grouper, arrayify, make_inverse, make_array_inverse 
from .names import Names

def normalize_ranges(ranges):
    covered = {}
    for (start, end) in ranges:
        if start == end:
            if start not in covered: covered[start] = False
        else:
            for i in range(start, end): covered[i] = True
    cur_start = None
    cur_end = None
    result = []
    for i in sorted(covered.keys()):
        if not covered[i]:
            if cur_end != None: result.extend((cur_start, cur_end))
            result.extend((i, i))
            cur_start = None
            cur_end = None
        elif cur_end == None or i > cur_end:
            if cur_end != None: result.extend((cur_start, cur_end))
            cur_start = i
            cur_end = i + 1
        else: cur_end = i + 1
    if cur_end != None: result.extend((cur_start, cur_end))
    return result

def model(origin, data_items, stamp):
    '''Augment the results of XML parsing by precomputing additional data structures.'''

    osep = ':' if origin[0] == 'a' else ''

    def model_x():
        stamp.Imsg("XML-IDS (inverse mapping)")
        for kind in ('n', 'e'):
            xi = (origin + osep + 'X' + kind + 'f', ())
            xr = (origin + osep + 'X' + kind + 'b', ())
            Names.deliver(make_inverse(data_items[Names.comp(*xi)]), xr, data_items)

    def model_regions():
        stamp.Imsg("NODES AND REGIONS")
        node_region_list = data_items[Names.comp(origin + osep + 'T00', ('node_region_list',))]
        n_node = len(node_region_list)

        stamp.Imsg("NODES ANCHOR BOUNDARIES")
        node_anchor_min = array.array('I', (0 for i in range(n_node)))
        node_anchor_max = array.array('I', (0 for i in range(n_node)))
        node_linked = array.array('I')
        region_begin = data_items[Names.comp(origin + osep + 'T00', ('region_begin',))]
        region_end = data_items[Names.comp(origin + osep + 'T00', ('region_end',))]
        node_anchor_list = []
        for node in range(n_node):
            links = node_region_list[node]
            if len(links) == 0:
                node_anchor_list.append([])
                continue
            node_linked.append(node)
            ranges = []
            for r in links:
                this_anchor_begin = region_begin[r]
                this_anchor_end = region_end[r]
                ranges.append((this_anchor_begin, this_anchor_end))
            norm_ranges = normalize_ranges(ranges)
            node_anchor_list.append(norm_ranges)
            node_anchor_min[node] = min(norm_ranges) + 1
            node_anchor_max[node] = max(norm_ranges) + 1
        (node_anchor, node_anchor_items) = arrayify(node_anchor_list)
        Names.deliver(node_anchor_min, (origin + osep + 'G00', ('node_anchor_min',)), data_items)
        Names.deliver(node_anchor_max, (origin + osep + 'G00', ('node_anchor_max',)), data_items)
        Names.deliver(node_anchor, (origin + osep + 'P00', ('node_anchor',)), data_items)
        Names.deliver(node_anchor_items, (origin + osep + 'P00', ('node_anchor_items',)), data_items)

        node_region_list = None
        del data_items[Names.comp(origin + osep + 'T00', ('region_begin',))]
        del data_items[Names.comp(origin + osep + 'T00', ('region_end',))]
        del data_items[Names.comp(origin + osep + 'T00', ('node_region_list',))]

        def interval(node): return (node_anchor_min[node], -node_anchor_max[node])

        stamp.Imsg("NODES SORTING BY REGIONS")
        node_sort = array.array('I', sorted(node_linked, key=interval))
        node_sort_inv = make_array_inverse(node_sort)
        Names.deliver(node_sort, (origin + osep + 'G00', ('node_sort',)), data_items)
        Names.deliver(node_sort_inv, (origin + osep + 'G00', ('node_sort_inv',)), data_items)

        stamp.Imsg("NODES EVENTS")
        anchor_max = max(node_anchor_max) - 1
        node_events = list([([],[],[]) for n in range(anchor_max + 1)])
        for n in node_sort:
            ranges = node_anchor_list[n]
            amin = ranges[0]
            amax = ranges[len(ranges)-1] 
            for (r, (a_start, a_end)) in enumerate(grouper(ranges, 2)):
                is_first = r == 0
                is_last = r == (len(ranges) / 2) - 1
                start_kind = 0 if is_first else 1 # 0 = start,   1 = resume
                end_kind = 3 if is_last else 2    # 2 = suspend, 3 = end
                if amin == amax: node_events[a_start][1].extend([(n, 0), (n,3)])
                else:
                    node_events[a_start][0].append((n, start_kind))
                    node_events[a_end][2].append((n, end_kind))
        node_events_n = array.array('I')
        node_events_k = array.array('I')
        node_events_a = list([[] for a in range(anchor_max + 1)])
        e_index = 0
        for (anchor, events) in enumerate(node_events):
            events[2].reverse()
            for main_kind in (2, 1, 0):
                for (node, kind) in events[main_kind]:
                    node_events_n.append(node)
                    node_events_k.append(kind)
                    node_events_a[anchor].append(e_index)
                    e_index += 1
        node_events = None
        (node_events, node_events_items) = arrayify(node_events_a)
        node_events_a = None
        Names.deliver(node_events_n, (origin + osep + 'P00', ('node_events_n',)), data_items)
        Names.deliver(node_events_k, (origin + osep + 'P00', ('node_events_k',)), data_items)
        Names.deliver(node_events, (origin + osep + 'P00', ('node_events',)), data_items)
        Names.deliver(node_events_items, (origin + osep + 'P00', ('node_events_items',)), data_items)
        node_anchor_list = None

    def model_conn():
        node_anchor_min = data_items[Names.comp('mG00', ('node_anchor_min',))]
        node_anchor_max = data_items[Names.comp('mG00', ('node_anchor_max',))]

        def interval(elem): return (node_anchor_min[elem[0]], -node_anchor_max[elem[0]])

        stamp.Imsg("CONNECTIVITY")
        edges_from = data_items[Names.comp('mG00', ('edges_from',))]
        edges_to = data_items[Names.comp('mG00', ('edges_to',))]
        labeled_edges = set()
        efeatures = set()
        for dkey in data_items:
            (dorigin, dgroup, dkind, ddir, dcomps) = Names.decomp_full(dkey)
            if dgroup != 'F' or dorigin != origin or dkind != 'e': continue
            efeatures.add((dkey, dcomps))
        for (dkey, feat) in efeatures:
            feature_map = data_items[dkey]
            connections = {}
            connectionsi = {}
            for (edge, fvalue) in feature_map.items():
                labeled_edges.add(edge)
                node_from = edges_from[edge]
                node_to = edges_to[edge]
                connections.setdefault(node_from, {})[node_to] = fvalue
                connectionsi.setdefault(node_to, {})[node_from] = fvalue
            Names.deliver(connections, (origin + osep + 'C0f', feat), data_items)
            Names.deliver(connectionsi, (origin + osep + 'C0b', feat), data_items)

        connections = {}
        connectionsi = {}
        if origin == 'm':
            for edge in range(len(edges_from)):
                if edge in labeled_edges: continue
                node_from = edges_from[edge]
                node_to = edges_to[edge]
                connections.setdefault(node_from, {})[node_to] = ''
                connectionsi.setdefault(node_to, {})[node_from] = ''
        elif origin[0] == 'a':
            for edge in range(len(edges_from)):
                if edge not in labeled_edges: continue
                node_from = edges_from[edge]
                node_to = edges_to[edge]
                connections.setdefault(node_from, {})[node_to] = ''
                connectionsi.setdefault(node_to, {})[node_from] = ''
        sfeature = Names.E_ANNOT_NON if origin == 'm' else Names.E_ANNOT_YES if origin[0] == 'a' else ''
        Names.deliver(connections, (origin + osep + 'C0f', sfeature), data_items)
        Names.deliver(connectionsi, (origin + osep + 'C0b', sfeature), data_items)

    if origin == 'm':
        model_x()
        model_regions()
    model_conn()

