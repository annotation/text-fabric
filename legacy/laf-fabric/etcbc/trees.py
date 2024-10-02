import collections
import copy
import functools
from .lib import monad_set, object_rank

class Tree(object):
    def __init__(self, API, otypes=None, clause_type=None, phrase_type=None,
            ccr_feature=None, pt_feature=None, pos_feature=None, mother_feature=None
        ):
        node_features = "otype monads minmonad {} {} {}".format(
            ccr_feature if ccr_feature != None else '',
            pt_feature if pt_feature != None else '',
            pos_feature if pos_feature != None else ''
        )
        edge_features = mother_feature if mother_feature != None else ''
        API['fabric'].load_again({"features":
            (node_features, edge_features)}, add=True)
        self.API = API
        self.ccr_feature = ccr_feature
        self.pos_feature = pos_feature
        self.pt_feature = pt_feature
        NN = API['NN']
        F = API['F']
        msg = API['msg']

        if otypes == None: otypes = sorted(object_rank, key=lambda x: object_rank[x])
        if clause_type == None: clause_type = 'clause'
        if phrase_type == None: phrase_type = 'phrase'
        self.root_type = otypes[0]
        self.leaf_type = otypes[-1]
        self.clause_type = clause_type
        self.phrase_type = phrase_type
        msg("Start computing parent and children relations for objects of type {}".format(', '.join(otypes)))
        otype_set = set(otypes)
        self.otype_set = otype_set
        self.leaf_list = {'r': {}, 'e': {}}
        base_type = otypes[-1]
        cur_stack = []
        eparent = {}
        echildren = collections.defaultdict(lambda: [])
        nn = 0
        cn = 0
        chunk = 100000
        Fotypev = F.db_otype.v
        Fmonadsv = F.db_monads.v
        for node in NN():
            otype = Fotypev(node)
            if otype not in otype_set: continue
            nn += 1
            cn += 1
            if cn == chunk:
                msg("{} nodes".format(nn))
                cn = 0
            nm_set = monad_set(Fmonadsv(node))
            nm_min = min(nm_set)
            nm_max = max(nm_set)
            ls = len(cur_stack)
            tobe_removed = set()
            for si in range(ls):
                act_on = ls -si - 1
                (snode, sm_set, sm_max) = cur_stack[act_on]
                if nm_min > sm_max:
                    tobe_removed.add(act_on)
                    continue
                if nm_set <= sm_set:
                    eparent[node] = snode
                    echildren[snode].append(node)
                    break;
            cur_stack = [cur_stack[i] for i in range(len(cur_stack)) if i not in tobe_removed]
            if otype != base_type: cur_stack.append((node, nm_set, nm_max))
        msg("{} nodes: {} have parents and {} have children".format(nn, len(eparent), len(echildren)))
        self.eparent = eparent
        self.echildren = echildren
        self.elder_sister = {}
        self.rparent = {}
        self.rchildren = {}
        self.sisters = {}
        self.elder_sister = {}
        self.mother = {}

    def restructure_clauses(self, ccr_class):
        API = self.API
        NN = API['NN']
        F = API['F']
        C = API['C']
        MK = API['MK']
        msg = API['msg']
        msg("Restructuring {}s: deep copying tree relations".format(self.clause_type))
        rparent = copy.deepcopy(self.eparent)
        rchildren = copy.deepcopy(self.echildren)
        sisters = collections.defaultdict(lambda: [])
        elder_sister = {}
        mother = {}
        self.rparent = rparent
        self.rchildren = rchildren
        self.sisters = sisters
        self.elder_sister = elder_sister
        self.mother = mother
        if self.ccr_feature == None: return
        otype_set = self.otype_set

        msg("Pass 0: Storing mother relationship")
        moutside = collections.defaultdict(lambda: 0)
        mo = 0
        mf = C.mother.v
        for c in NN(test=F.db_otype.v, value=self.clause_type):
            lms = list(mf(c))
            ms = len(lms)
            if ms:
                m = lms[0]
                mtype = F.db_otype.v(m)
                if mtype in otype_set: mother[c] = m
                else:
                    moutside[mtype] += 1
                    mo += 1
        msg("{} {}s have a mother".format(len(mother), self.clause_type))
        if mo:
            msg("{} {}s have mothers of types outside {}.\nThese mother relationships will be ignored".format(mo, self.clause_type, otype_set))
            for mt in sorted(moutside):
                msg("{} mothers point to {} nodes".format(moutside[mt], mt), withtime=False)
        else:
            msg("All {}s have mothers of types in {}".format(self.clause_type, otype_set))

        msg("Pass 1: all {}s except those of type Coor".format(self.clause_type))
        motherless = set()
        ccrf = F.item[self.ccr_feature].v
        Fotypev = F.db_otype.v
        Fmonadsv = F.db_monads.v
        for cnode in NN(test=Fotypev, value=self.clause_type):
            cclass = ccr_class[ccrf(cnode)]
            if cclass == 'n' or cclass == 'x': pass
            elif cclass == 'r':
                if cnode not in mother:
                    motherless.add(cnode)
                    continue
                mnode = mother[cnode]
                mtype = Fotypev(mnode)
                pnode = rparent[cnode]
                if mnode not in rparent:
                    msg("Should not happen: node without parent: [{} {}]({}) =mother=> [{} {}]({}) =/=> parent".format(
                        self.clause_type, F.db_monads.v(cnode), cnode, mtype, Fmonadsv(mnode), mnode
                    ))
                pmnode = rparent[mnode]
                pchildren = rchildren[pnode]
                mchildren = rchildren[mnode]
                pmchildren = rchildren[pmnode]
                deli = pchildren.index(cnode)
                if mtype == self.leaf_type:
                    if pnode != pmnode:
                        rparent[cnode] = pmnode
                        del pchildren[deli:deli+1]
                        pmchildren.append(cnode)
                else:
                    if pnode != mnode:
                        rparent[cnode] = mnode
                        del pchildren[deli:deli+1]
                        mchildren.append(cnode)
        msg("Pass 2: {}s of type Coor only".format(self.clause_type))
        for cnode in NN(test=Fotypev, value=self.clause_type):
            cclass = ccr_class[ccrf(cnode)]
            if cclass != 'x': continue
            if cnode not in mother:
                motherless.add(cnode)
                continue
            mnode = mother[cnode]
            pnode = rparent[cnode]
            pchildren = rchildren[pnode]
            deli = pchildren.index(cnode)
            sisters[mnode].append(cnode)
            elder_sister[cnode] = mnode
            del rparent[cnode]
            del pchildren[deli:deli+1]

        sister_count = collections.defaultdict(lambda: 0)
        for n in sisters:
            sns = sisters[n]
            sister_count[len(sns)] += 1
        msg("Mothers applied. Found {} motherless {}s.".format(len(motherless), self.clause_type))
        ts = 0
        for l in sorted(sister_count):
            c = sister_count[l]
            ts += c * l
            msg("{} nodes have {} sisters".format(c, l))
        msg("There are {} sisters, {} nodes have sisters.".format(ts, len(sisters)))
        motherless = None

    def relations(self): return {
        'eparent': self.eparent,
        'echildren': self.echildren,
        'rparent': self.rparent,
        'rchildren': self.rchildren,
        'sisters': self.sisters,
        'elder_sister': self.elder_sister,
        'mother': self.mother,
    }

    def get_sisters(self, node):
        sisters = self.sisters
        MK = self.API['MK']
        def _mkey(n): return MK(self.get_monads(n, 'r'))
        def _get_sisters(n):
            result = (n,)
            if n in sisters and len(sisters[n]):
                for sn in sisters[n]: result += _get_sisters(sn)
            return result
        return sorted(_get_sisters(node), key=_mkey)

    def get_children(self, node, kind):
        children = self.rchildren if kind == 'r' else self.echildren 
        MK = self.API['MK']
        def _mkey(n): return MK(self.get_monads(n, kind))
        cnodes = ()
        if node in children and len(children[node]):
            cnodes = children[node]
        return sorted(cnodes, key=_mkey)

    def debug_write_tree(self, node, kind, legenda=False):
        API = self.API
        F = API['F']
        msg = API['msg']
        result = []
        ids = {}
        maxid = 0
        ccrf = F.item[self.ccr_feature].v
        bmonad = int(F.db_minmonad.v(node))
        Fotypev = F.db_otype.v
        Fmonadsv = F.db_monads.v
        elder_sister = self.elder_sister
        sisters = self.sisters if kind == 'r' else {}
        mother = self.mother

        def rep(n):
            if n in ids: return ids[n]
            nonlocal maxid
            maxid += 1
            ids[n] = maxid
            return maxid

        def _fillids(node):
            otype = F.db_otype.v(node)
            parent = self.eparent 
            children = self.echildren 
            if node in mother: rep(mother[node])
            rep(node)
            if node in children:
                for cnode in children[node]:
                    _fillids(cnode)

        def _debug_write_tree(node, level, indent):
            cnodes = self.get_children(node, kind)
            otype = Fotypev(node)
            subtype = ''
            subtype_sep = ''
            mspec = ''
            if otype == self.clause_type:
                subtype = ccrf(node)
                if subtype != None and subtype != 'none':
                    subtype_sep = '.'
                else:
                    subtype = ''
                    subtype_sep = ''
                if kind == 'e':
                    if node in mother:
                        mspec = '=> ({:>3})'.format(rep(mother[node]))
                elif kind == 'r':
                    if node in elder_sister:
                        mspec = '=> ({:>3})'.format(rep(elder_sister[node]))
            elif otype == self.phrase_type:
                subtype = F.item[self.pt_feature].v(node)
                if subtype != None:
                    subtype_sep = '.'
                else:
                    subtype = ''
                    subtype_sep = ''
            elif otype == self.leaf_type:
                posf = F.item[self.pos_feature].v
                subtype = posf(node)
                if subtype != None:
                    subtype_sep = '.'
                else:
                    subtype = ''
                    subtype_sep = ''
            monads = Fmonadsv(node)
            rangesi = [[int(a)-bmonad for a in r.split('-')] for r in monads.split(',')] 
            monadss = ','.join('-'.join(str(a) for a in r) for r in rangesi)

            result.append("{:>2}{:<30} {:<10}] ({:>3}) {:<8} <{}>\n".format(
                level,
                "{}[{:<10}".format(indent, "{}{}{}".format(otype, subtype_sep, subtype)),
                monadss, rep(node), mspec,
                ','.join("{:>3}".format(rep(c)) for c in cnodes),
            ))
            if kind == 'e':
                for cnode in cnodes: _debug_write_tree(cnode, level + 1, indent + '  ')
            else:
                for cnode in cnodes:
                    snodes = self.get_sisters(cnode)
                    if len(snodes) == 1:
                        _debug_write_tree(cnode, level + 1, indent + '  ')
                    else:
                        for snode in snodes:
                            if snode == cnode:
                                _debug_write_tree(snode, level + 1, indent + '  ' + '*')
                            else:
                                _debug_write_tree(snode, level + 1, indent + '  ' + '=')
        _fillids(node)
        _debug_write_tree(node, 0, '')
        if legenda:
            result.append("\nstart monad = {}\n\n".format(bmonad))
            result.append("{:>3} = {:>8} {:>8}\n".format('#', 'etcbc4_oid', 'laf_nid'))
            for (n, s) in sorted(ids.items(), key=lambda x: x[1]):
                result.append("{:>3} = {:>8} {:>8}\n".format(s, F.db_oid.v(n), n))
        return ''.join(result)

    def write_tree(self, node, kind, get_tag, rev=False, leafnumbers=True):
        API = self.API
        F = API['F']
        msg = API['msg']
        otype = F.db_otype.v(node)
        children = self.rchildren if kind == 'r' else self.echildren 
        sisters = self.sisters if kind == 'r' else {}
        bmonad = int(F.db_minmonad.v(node))

        words = []
        sequential = []
        def _write_tree(node):
            eldest = node in sisters and len(sisters[node])
            (tag, pos, monad, text, is_word) = get_tag(node)
            if is_word:
                sequential.append(("W", len(words)))
                words.append((monad - bmonad, text, pos))
            else: sequential.append(("O", tag))
            cnodes = self.get_children(node, kind)
            if kind == 'e':
                for cnode in cnodes: _write_tree(cnode)
            else:
                for cnode in cnodes:
                    snodes = self.get_sisters(cnode)
                    if len(snodes) == 1: _write_tree(cnode)
                    else:
                        ctag = get_tag(cnode)[0]
                        sequential.append(("O", ctag))
                        for snode in snodes:
                            if snode == cnode:
                                 sequential.append(("O", 'Ccoor'))
                                 for csnode in self.get_children(snode, kind): _write_tree(csnode)
                                 sequential.append(("C", 'Ccoor'))
                            else:
                                _write_tree(snode)
                        sequential.append(("C", ctag))
            if not is_word: sequential.append(("C", tag))

        def do_sequential():
            if leafnumbers: word_rep = ' '.join(x[1] for x in sorted(words, key=lambda x: x[0]))
            else: word_rep = ' '.join(str(x[0]) for x in words)
                            
            tree_rep = []
            for (code, info) in sequential:
                if code == 'O' or code == 'C':
                    if code == 'O': tree_rep.append('({}'.format(info))
                    else: tree_rep.append(')')
                elif code == 'W':
                    (monad, text, pos) = words[info]
                    leaf = monad if leafnumbers else text[::-1] if rev else text
                    tree_rep.append('({} {})'.format(pos, leaf))
            return (''.join(tree_rep), word_rep[::-1] if rev and leafnumbers else word_rep, bmonad) 

        _write_tree(node)
        return do_sequential()

    def depth(self, node, kind):
        API = self.API
        F = API['F']
        msg = API['msg']
        def _depth(node, kind):
            parent = self.rparent if kind == 'r' else self.eparent 
            children = self.rchildren if kind == 'r' else self.echildren 
            sisters = self.sisters
            elder_sister = self.elder_sister
            has_sisters =  node in sisters and len(sisters[node])
            has_children = node in children and len(children[node])
            cdepth = 1 + max(_depth(c, kind) for c in children[node]) if has_children else 0
            sdepth = 1 + max(_depth(s, kind) for s in sisters[node]) if has_sisters else 0
            if kind == 'e': return cdepth
            elif kind == 'r': return max(cdepth + 1, sdepth) if has_sisters else cdepth
        return _depth(node, kind)

    def length(self, node): return len(monad_set(self.API['F'].monads.v(node)))

    def get_leaves(self, node, kind):
        API = self.API
        F = API['F']
        msg = API['msg']
        visited = set()
        my_leaf_list = self.leaf_list[kind]
        parent = self.rparent if kind == 'r' else self.eparent 
        children = self.rchildren if kind == 'r' else self.echildren 
        sisters = self.sisters if kind == 'r' else {}
        elder_sister = self.elder_sister

        def _get_leaves(node, with_sisters=False):
            #print("start _GL({})".format(node))
            if node in my_leaf_list:
                return  my_leaf_list[node]
            if node in visited: return ()
            visited.add(node)
            result = ()
            #print("contA _GL({})".format(node))
            if node in children and len(children[node]) > 0:
                for cnode in children[node]:
                    result += _get_leaves(cnode, with_sisters=True)
            else: result += (node,)
            if with_sisters and node in sisters:
                for snode in sisters[node]:
                    result += _get_leaves(snode, with_sisters=True)
            my_leaf_list[node] = result
            return result

        return _get_leaves(node, with_sisters=False)

    def get_monads(self, node, kind):
        API = self.API
        F = API['F']
        Fmonadsv = F.db_monads.v
        return functools.reduce(lambda x,y: x | y, (monad_set(Fmonadsv(leaf)) for leaf in self.get_leaves(node, kind)), set())
        #return set(int(F.db_monads.v(n)) for n in self.get_leaves(node, kind))

    def get_root(self, node, kind):
        API = self.API
        F = API['F']
        msg = API['msg']
        otype = F.db_otype.v(node)
        parent = self.rparent if kind == 'r' else self.eparent 
        children = self.rchildren if kind == 'r' else self.echildren 
        if node in parent: return self.get_root(parent[node], kind)
        if kind == 'r':
            if node in elder_sister: return self.get_root(elder_sister[node], kind)
        return (node, otype)
    
