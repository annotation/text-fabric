import os
import glob
import collections
import functools
import time
from .lib import make_array_inverse
from .names import Names, FabricError
from .data import LafData
from .elements import Feature, Connection, XMLid, PrimaryData

class LafAPI(LafData):
    '''Makes all API methods available.
    ``API()`` returns a dict keyed by mnemonics and valued by API methods.
    '''
    def __init__(self, names):
        self.api = {}
        self.names = names
        self.stamp = names.stamp
        LafData.__init__(self)
        self.result_files = []

    def API(self):
        self._api_fcxp()
        self._api_nodes()
        self._api_edges()
        self._api_io()
        self._api_prep()
        return self.api

    def APIprep(self):
        self._api_post()
        return self.api

    def get_all_features(self):
        env = self.names.env
        loadables = set()
        for feat_path in glob.glob('{}/*'.format(env['m_compiled_dir'])):
            filename = os.path.basename(feat_path)
            if filename.startswith(('_', 'A', 'Z')): continue
            loadables.add('m{}'.format(filename))
        for anx in env['annox']:
            for feat_path in glob.glob('{}/*'.format(env['annox'][anx]['a_compiled_dir'])):
                filename = os.path.basename(feat_path)
                if filename.startswith('_'): continue
                loadables.add('a{}:{}'.format(anx, filename))
        self.all_features = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
        self.all_features_index = collections.defaultdict(lambda: collections.defaultdict(lambda: []))
        self.all_features_origin = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))
        for filename in loadables:
            (dorigin, dgroup, dkind, ddir, dcomps) = Names.decomp_full(filename)
            if dgroup != 'F': continue
            (namespace, label, name) = dcomps
            self.all_features[dkind][namespace].add("{}.{}".format(label, name))
            self.all_features_index[dkind][name].append((namespace, label))
            self.all_features_origin[dkind][(namespace, label, name)].add(dorigin)
        if 'e' in self.all_features:
            for fname in ('x', 'y'):
                self.all_features['e']['laf'].add('{}.{}'.format('', fname))
                self.all_features_index['e'][fname].append(('laf', ''))
                self.all_features_origin['e'][('laf', '', fname)].add(dorigin)

    def _api_fcxp(self):
        data_items = self.data_items
        api = {
            'F': Bunch(),
            'FE': Bunch(),
            'C': Bunch(),
            'Ci': Bunch(),
        }
        features = {'n': set(), 'e': set()}
        connections = {'f': set(), 'b': set()}
        xmlmaps = {'n': set(), 'e': set()}
        for dkey in data_items:
            (dorigin, dgroup, dkind, ddir, dcomps) = Names.decomp_full(dkey)
            if dgroup == 'F': features[dkind].add(dcomps)
            elif dgroup == 'C': connections[ddir].add(dcomps)
            elif dgroup == 'X': xmlmaps[dkind].add(dcomps)
            elif dgroup == 'P' and dcomps[0] == 'primary_data': api['P'] = PrimaryData(self)
        self.feature_abbs = collections.defaultdict(lambda: set())
        self.feature_abb = {}
        for kind in sorted(features):
            for feat in sorted(features[kind]):
                name = Names.apiname(feat) 
                for abb in (Names.apiname(feat[1:]), Names.apiname(feat[2:])):
                    if abb:
                        self.feature_abbs[abb].add(name)
                        self.feature_abb[abb] = name
        for abb in self.feature_abbs:
            expansions = self.feature_abbs[abb]
            chosen = self.feature_abb[abb]
            if len(expansions) > 1:
                self.stamp.Imsg("Feature {} refers to {}, not to {}".format(abb, chosen, ', '.join(sorted(expansions - set([chosen])))))
        for kind in features:
            for feat in features[kind]:
                name = Names.apiname(feat) 
                obj = Feature(self, feat, kind)
                dest = api['FE'] if kind == 'e' else api['F']
                dest.item[name] = obj
                setattr(dest, name, obj)
                for abb in (Names.apiname(feat[1:]), Names.apiname(feat[2:])):
                    if abb and self.feature_abb.get(abb, '') == name:
                        setattr(dest, abb, obj)
                        dest.item[abb] = obj
        for inv in connections:
            for feat in connections[inv]:
                name = Names.apiname(feat) 
                obj = Connection(self, feat, inv)
                dest = api['C'] if inv == 'f' else api['Ci'] if inv == 'b' else None
                dest.item[name] = obj
                setattr(dest, name, obj)
                for abb in (Names.apiname(feat[1:]), Names.apiname(feat[2:])):
                    if abb and self.feature_abb.get(abb, '') == name:
                        setattr(dest, abb, obj)
                        dest.item[abb] = obj
        for kind in xmlmaps:
            for comp in xmlmaps[kind]:
                obj = XMLid(self, kind)
                dest = 'XE' if kind == 'e' else 'X'
                api[dest] = obj

        def feature_list(kind):
            result = []
            for namespace in sorted(self.all_features[kind]):
                result.append((namespace, sorted(self.all_features[kind][namespace])))
            return result

        def pretty_fl(flist):
            result = []
            for ((namespace, features)) in flist:
                result.append('{}:'.format(namespace))
                for feature in features:
                    result.append('\t{}:'.format(feature))
            return '\n'.join(result)

        api.update({
            'F_all': feature_list('n'),
            'fF_all': pretty_fl(feature_list('n')),
            'FE_all': feature_list('e'),
            'fFE_all': pretty_fl(feature_list('e')),
        })
        self.api.update(api)

    def _api_prep(self):
        api = self.api
        api['make_array_inverse'] = make_array_inverse
        api['data_items'] = self.data_items

    def _api_post(self):
        (self.prepare_init)(self)

    def _api_edges(self):
        data_items = self.data_items
        edges_from = data_items[Names.comp('mG00', ('edges_from',))]
        edges_to = data_items[Names.comp('mG00', ('edges_to',))]

        def next_edge():
            for e in range(len(edges_from)):
                yield (e, edges_from[e], edges_to[e])

        self.api.update({
            'EE':      next_edge,
        })

    def _api_nodes(self):
        data_items = self.data_items
        node_anchor_min = data_items[Names.comp('mG00', ('node_anchor_min',))]
        node_anchor_max = data_items[Names.comp('mG00', ('node_anchor_max',))]

        def before(nodea, nodeb):
            if node_anchor_min[nodea] == node_anchor_max[nodea] or node_anchor_min[nodeb] == node_anchor_max[nodeb]: return None
            if node_anchor_min[nodea] < node_anchor_min[nodeb]: return True
            if node_anchor_min[nodea] > node_anchor_min[nodeb]: return False
            if node_anchor_max[nodea] > node_anchor_max[nodeb]: return True
            if node_anchor_max[nodea] < node_anchor_max[nodeb]: return False
            return None

        def node_sort_key(node): return data_items[Names.comp('mG00', ('node_sort_inv',))][node]

        def msetbefore(sa,sb):
            if sa == sb: return 0
            if sa <= sb: return 1
            if sb <= sa: return -1
            am = min(sa - sb)
            bm = min(sb - sa)
            return -1 if am < bm else 1 if bm < am else None
        msetkey = functools.cmp_to_key(msetbefore)

        def next_node(nodes=None, test=None, value=None, values=None, extrakey=None):
            class Extra_key(object):
                __slots__ = ['value', 'amin', 'amax']
                def __init__(self, node):
                    self.amin = node_anchor_min[node] - 1
                    self.amax = node_anchor_max[node] - 1
                    self.value = extrakey(node)
                def __lt__(self, other):
                    return (
                        self.amin == other.amin and
                        self.amax == other.amax and
                        self.value < other.value
                    )
                def __gt__(self, other):
                    return (
                        self.amin == other.amin and
                        self.amax == other.amax and
                        self.value > other.value
                    )
                def __eq__(self, other):
                    return (
                        self.amin != other.amin or
                        self.amax != other.amax or
                        self.value == other.value
                    )
                __hash__ = None

            order = data_items[Names.comp('mG00', ('node_sort',))]
            order_key = data_items[Names.comp('mG00', ('node_sort_inv',))]
            the_nodes = sorted(nodes, key=lambda x: order_key[x]) if nodes else order

            if extrakey != None:
                self.stamp.Imsg("Resorting {} nodes...".format(len(the_nodes)))
                the_nodes = sorted(the_nodes, key=Extra_key)
                self.stamp.Imsg("Done")
            if test != None:
                test_values = set(([value] if value != None else []) + (list(values) if values != None else []))
                if len(test_values):
                    for node in the_nodes:
                        if test(node) in test_values: yield node
                else:
                    for node in the_nodes:
                        if test(node): yield node
            else:
                for node in the_nodes: yield node

        def no_next_event(key=None, simplify=None):
            raise FabricError("Node events not available because primary data is not loaded.", self.stamp)
            return None

        def next_event(key=None, simplify=None):
            class Additional_key(object):
                __slots__ = ['value', 'kind', 'amin', 'amax']
                def __init__(self, event):
                    (node, kind) = event
                    self.amin = node_anchor_min[node] - 1
                    self.amax = node_anchor_max[node] - 1
                    self.value = key(node) * (-1 if kind < 2 else 1)
                    self.kind = kind
                def __lt__(self, other):
                    return (
                        self.amin == other.amin and
                        self.amax == other.amax and
                        (self.kind == other.kind or self.amin == self.amax) and
                        self.value < other.value
                    )
                def __gt__(self, other):
                    return (
                        self.amin == other.amin and
                        self.amax == other.amax and
                        (self.kind == other.kind or self.amin == self.amax) and
                        self.value > other.value
                    )
                def __eq__(self, other):
                    return (
                        self.amin != other.amin or
                        self.amax != other.amax or
                        (self.kind != other.kind and (self.amin != self.amax or other.amin != other.amax)) or
                        self.value == other.value
                    )
                __hash__ = None

            nodes = data_items[Names.comp('mP00', ('node_events_n',))]
            kinds = data_items[Names.comp('mP00', ('node_events_k',))]
            node_events = data_items[Names.comp('mP00', ('node_events',))]
            node_events_items = data_items[Names.comp('mP00', ('node_events_items',))]
            bufferevents = collections.deque([(-1, [])], 2)

            active = {}
            for anchor in range(len(node_events)):
                event_ids = self._getitems(node_events, node_events_items, anchor)
                if len(event_ids) == 0: continue
                eventset = []
                for event_id in event_ids:
                    node = nodes[event_id]
                    if key == None or key(node) != None: eventset.append((nodes[event_id], kinds[event_id]))
                if not eventset: continue
                if key != None: eventset = sorted(eventset, key=Additional_key)
                if simplify == None:
                    yield (anchor, eventset)
                    continue
                bufferevents.append([anchor, eventset])
                if bufferevents[0][0] == -1: continue
                (this_anchor, these_events) = bufferevents[0]
                (next_anchor, next_events) = bufferevents[1]
                deleted = {}
                for (n, kind) in these_events:
                    if simplify(n):
                        if kind == 3: deleted[n] = None
                        elif kind == 2: active[n] = False
                        elif kind == 1: active[n] = True
                        elif kind == 0: active[n] = True
                for n in deleted:
                    if n in active: del active[n]
                if True not in active.values():
                    weed = collections.defaultdict(lambda: False)
                    for (n, k) in these_events:
                        if k == 2: weed[n] = None
                    for (n, k) in next_events:
                        if k == 1:
                            if n in weed: weed[n] = True
                    if True in weed.values():
                        bufferevents[0][1] = [(n, k) for (n, k) in these_events if not (k == 2 and weed[n])] 
                        bufferevents[1][1] = [(n, k) for (n, k) in next_events if not (k == 1 and weed[n])] 
                yield (bufferevents[0])
            yield (bufferevents[0])

        self.api.update({
            'BF':      before,
            'NN':      next_node,
            'NE':      next_event if Names.comp('mP00', ('node_events',)) in data_items else no_next_event,
            'NK':      node_sort_key,
            'MK':      msetkey,
        })

    def _api_io(self):
        def _inf(msg, newline=True, withtime=True, verbose=None):
            self.stamp.raw_msg(msg, newline=newline, withtime=withtime, verbose=verbose, error=False)
        def _msg(msg, newline=True, withtime=True, verbose=None):
            self.stamp.raw_msg(msg, newline=newline, withtime=withtime, verbose=verbose, error=True)

        task_dir = self.names.env['task_dir']

        def add_output(file_name):
            result_file = "{}/{}".format(task_dir, file_name)
            handle = open(result_file, "w", encoding="utf-8")
            self.result_files.append(handle)
            return handle

        def add_input(file_name):
            result_file = "{}/{}".format(task_dir, file_name)
            handle = open(result_file, "r", encoding="utf-8")
            self.result_files.append(handle)
            return handle

        def result(file_name=None):
            if file_name == None: return task_dir
            else: return "{}/{}".format(task_dir, file_name)

        api = {
            'infile':  add_input,
            'outfile': add_output,
            'close':   self.finish_task,
            'my_file': result,
            'msg':     _msg,
            'inf':     _inf,
            'data_dir': self.names.env['data_dir'],
            'output_dir': self.names.env['output_dir'],
        }
        self.api.update(api)

    def _getitems(self, data, data_items, elem):
        data_items_index = data[elem]
        n_items = data_items[data_items_index]
        return data_items[data_items_index + 1:data_items_index + 1 + n_items]

    def __del__(self):
        for handle in self.result_files:
            if handle and not handle.closed: handle.close()
        LafData.__del__(self)

class Bunch(object):
    def __init__(self): self.item = {}

class LafFabric(object):
    '''Process manager.

    ``load(params)``: given the source, annox and task, loads the data, assembles the API, and returns the API.
    '''
    def __init__(self, data_dir=None, laf_dir=None, output_dir=None, save=False, verbose=None):
        self.lafapi = LafAPI(Names(data_dir, laf_dir, output_dir, save, verbose))
        self.lafapi.stamp.reset()
        self.api = {}

    def load(self, source, annox, task, load_spec, add=False, compile_main=False, compile_annox=False, verbose='NORMAL', time_reset=True):
        self.api.clear()
        lafapi = self.lafapi
        self.api['fabric'] = self
        if time_reset: lafapi.stamp.reset()
        Names.check_load_spec(load_spec, lafapi.stamp)
        self.lafapi.stamp.set_verbose(verbose)
        lafapi.stamp.Nmsg("LOADING API{}: please wait ... ".format(' with EXTRAs' if add else ''))
        lafapi.names.setenv(source=source, annox=annox, task=task)
        lafapi.names.set_annox()
        env = lafapi.names.env
        lafapi.prepare_dirs(env['annox'])
        lafapi.compile_all({'m': compile_main, 'a': compile_annox})
        req_items = {}
        lafapi.names.request_init(req_items)
        lafapi.get_all_features()
        if 'primary' in load_spec and load_spec['primary']: req_items['mP00'] = True
        if 'xmlids' in load_spec:
            for kind in [k[0] for k in load_spec['xmlids'] if load_spec['xmlids'][k]]:
                for ddir in ('f', 'b'): req_items['mX{}{}'.format(kind, ddir)].append(())
        if 'features' in load_spec: self._request_features(load_spec['features'], req_items, add)
        prep = load_spec['prepare'] if 'prepare' in load_spec else (lafapi.prepare_dict, lafapi.prepare_init) if add else ({}, None)
        lafapi.load_all(req_items, prep, add)
        lafapi.add_logfile()
        self.api.update(lafapi.API())
        if 'prepare' in load_spec:
            lafapi.stamp.Imsg("LOADING PREPARED data: please wait ... ")
            lafapi.prepare_all(self.api)
            self.api.update(lafapi.APIprep())
            lafapi.stamp.Imsg("LOADED PREPARED data")
        lafapi.stamp.Smsg(
            'DATA LOADED FROM SOURCE {} AND ANNOX {} FOR TASK {} AT {}'.format(
                env['source'], ', '.join(env['annox'].keys()), env['task'], time.strftime("%Y-%m-%dT%H-%M-%S", time.gmtime())
            ),
            'INFO' if time_reset else 'NORMAL',
        )
        if time_reset: lafapi.stamp.reset()
        self.localnames = '\n'.join('''{key} = {{var}}.api['{key}']'''.format(key=key) for key in self.api)
        self.llocalnames = '\n'.join('''if '{key}' not in locals(): {key} = dict()\n{key}['{{biblang}}'] = {{var}}.api['{key}']'''.format(key=key) for key in self.api)
        self.lafapi.stamp.set_verbose(verbose)
        return self.api

    def load_again(self, load_spec, annox=None, add=False, compile_main=False, compile_annox=False, verbose='NORMAL'):
        env = self.lafapi.names.env
        new_annox = annox
        if add:
            if annox == None or annox == '' or annox == env['empty'] or annox == [] or annox == {}: new_annox = env['annox']
            else: new_annox = list(env['annox'].keys()) + [annox]
        else:
            if annox == None or annox == '' or annox == env['empty'] or annox == [] or annox == {}: new_annox = []
            else: new_annox = [annox]
        x = self.load(env['source'], new_annox, env['task'], load_spec, add, compile_main=compile_main, compile_annox=compile_annox, verbose=verbose, time_reset=False)
        return x

    def resolve_feature(self, kind, feature_given):
        lafapi = self.lafapi
        all_features = lafapi.all_features_index
        stamp = lafapi.stamp
        dkind = kind[0]
        if dkind not in all_features: raise FabricError("No features of kind {} in LAF resource".format(kind), stamp)
        (aspace, feature_raw) = feature_given.split(':', 1) if ':' in feature_given else (None, feature_given)
        (alabel, fname) = feature_raw.split('.', 1) if '.' in feature_raw else (None, feature_raw)
        if fname not in all_features[dkind]: raise FabricError("No such feature in LAF resource: {}".format(fname), stamp)
        hits = []
        candidates = all_features[dkind][fname]
        for (aspacec, alabelc) in candidates:
            if (aspace == None or aspace == aspacec) and (alabel == None or alabelc == alabel): hits.append((aspacec, alabelc))
        if not hits: raise FabricError("No feature in LAF resource: {}{}{}".format((aspace+':') if aspace != None else '', (alabel+'.') if alabel != None else '', fname), stamp)
        hit = hits[-1]
        the_feature = (hit[0], hit[1], fname)
        if len(hits) > 1:
            stamp.Imsg("Feature {}{}{} may mean any of {}. Choosing {}".format(
                (aspace+':') if aspace != None else '',
                (alabel+'.') if alabel != None else '',
                fname,
                ', '.join("{}:{}.{}".format(fc[0], fc[1], fname) for fc in hits),
                "{}:{}.{}".format(*the_feature),
            ))
        return the_feature
        
    def _request_features(self, feat_spec, req_items, add):
        lafapi = self.lafapi
        env = lafapi.names.env
        all_features = lafapi.all_features_index
        stamp = lafapi.stamp
        the_features = collections.defaultdict(lambda: set())
        if type(feat_spec) == dict:
            for aspace in feat_spec:
                for kind in feat_spec[aspace]:
                    for line in feat_spec[aspace][kind]:
                        (alabel, fnamestring) = line.split('.') if '.' in line else (None, line)
                        fnames = fnamestring.split(',')
                        for fname in fnames:
                            the_features[kind].add((aspace, alabel, fname))
        else:
            for (kind, index) in (("node", 0), ("edge", 1)):
                feature_list = feat_spec[index]
                features = feature_list.split()
                for line in features:
                    the_features[kind].add(self.resolve_feature(kind, line))

        for kind in the_features:
            dkind = kind[0]
            if dkind not in all_features: raise FabricError("No features of kind {} in LAF resource".format(kind), stamp)
            for (aspace, alabel, fname) in the_features[kind]:
                if fname not in all_features[dkind]: raise FabricError("No such feature in LAF resource: {}".format(fname), stamp)
                for origin in ['m'] + ['a{}'.format(anx) for anx in env['annox']]:
                    osep = ':' if origin[0] == 'a' else ''
                    if origin in lafapi.all_features_origin[dkind][(aspace, alabel, fname)]:
                        req_items['{}F{}0'.format(origin+osep, dkind)].append((aspace, alabel, fname))
                        if dkind == 'e':
                            for ddir in ('f', 'b'): req_items['{}C0{}'.format(origin+osep, ddir)].append((aspace, alabel, fname))
