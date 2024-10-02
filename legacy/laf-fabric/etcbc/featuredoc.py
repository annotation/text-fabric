import sys
import collections
from copy import deepcopy

class FeatureDoc(object):
    '''Extracts feature information for selected features.

    The information returned consists of value lists, number of occurrences, and
    an summary spreadsheet.
    '''

    def __init__(self, processor, study):
        '''Upon creation, re-initializes the laf processor with requested features plus some needed features.

        Args:
            study:
                A dictionary directing the feature study. Contains:
                    
                    * a list of features to be studied.
                      It is a list of feature names
                    * a set of *absence values*, i.e. values like ``none`` or ``unknown`` that somehow count as the absence of a value.
                    * VALUE_THRESHOLD: a parameter that indicates how many distinct values to list in the summary.
        '''
        self.BASELOAD = {
            "xmlids": {
                "node": False,
                "edge": False,
            },
            "features": ('''otype {}'''.format(study['vlabel']), ''),
            "primary": False,
        }

        self.processor = processor
        self.study = study
        this_load = deepcopy(self.BASELOAD)
        this_load['features'] = (
            this_load['features'][0] + ' ' + study['features']['node'],
            this_load['features'][1] + ' ' + study['features']['edge'],
        )
        processor.load_again(this_load, verbose='DETAIL')
        self.API = processor.api

    def feature_doc(self):
        '''Create the feature information.

        Based on the study information given at the creation of the FeatureDoc object, a set of files is created.

        * A tab separated overview of statistical feature/value information.
        * For each feature, a file with its values and number of occurrences.
        * A file of node types and the features they carry.

        '''
        msg = self.API['msg']
        outfile = self.API['outfile']
        F = self.API['F']
        FE = self.API['FE']
        NN = self.API['NN']
        EE = self.API['EE']
        msg = self.API['msg']
        outfile = self.API['outfile']
        my_file = self.API['my_file']

        msg("Looking up feature values ... ")
        node_feats = [ft.replace(':','_').replace('.','_') for ft in self.study['features']['node'].split()]
        edge_feats = [ft.replace(':','_').replace('.','_') for ft in self.study['features']['edge'].split()]
        absence_values = self.study['absence_values']
        VALUE_THRESHOLD = self.study['VALUE_THRESHOLD']

# values and object types for this feature
        
        vals = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
        vals_def = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
        vals_undef = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
        n_otypes = collections.defaultdict(lambda: collections.defaultdict(lambda: [0,0]))
        n_otypesi = collections.defaultdict(lambda: collections.defaultdict(lambda: [0,0]))
        e_otypes = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
        e_otypesi = collections.defaultdict(lambda: collections.defaultdict(lambda: 0))
        
        chunk_size = 100000
        ci = 0
        i = 0
        for node in NN():
            i += 1
            ci += 1
            if ci == chunk_size:
                ci = 0
                msg("{:>7} nodes done".format(i))
            for ft in node_feats:
                val = F.item[ft].v(node)
                if val != None:
                    otype = F.db_otype.v(node)
                    if val in absence_values:
                        n_otypes[otype][ft][0] += 1
                        n_otypesi[ft][otype][0] += 1
                        vals_undef[ft][val] += 1
                    else:
                        n_otypes[otype][ft][1] += 1
                        n_otypesi[ft][otype][1] += 1
                        vals_def[ft][val] += 1
        msg("{:>7} nodes done".format(i))

        ci = 0
        i = 0
        for edge in EE():
            i += 1
            ci += 1
            if ci == chunk_size:
                ci = 0
                msg("{:>7} edges done".format(i))
            for ft in edge_feats:
                val = FE.item[ft].v(edge[0])
                if val != None:
                    otype_from = F.db_otype.v(edge[1])
                    otype_to = F.db_otype.v(edge[2])
                    e_otypes[(otype_from, otype_to)][ft] += 1
                    e_otypesi[ft][(otype_from, otype_to)] += 1
                    vals[ft][val] += 1
        msg("{:>7} edges done".format(i))
        
        node_otypes = sorted(n_otypes.keys())
        edge_otypes = sorted(e_otypes.keys())

        msg("Computing results ...")
        
        for ft in node_feats:
            result_file = outfile("{} values.txt".format(ft))
            result_file.write("{} DIFFERENT DEFINED VALUES IN TOTAL\n".format(len(vals_def[ft])))
            result_file.write("UNDEFINED VALUES\n")
            for x in sorted(vals_undef[ft].items(), key=lambda y: (-y[1], y[0])):
                result_file.write("{} x {}\n".format(*x))
            result_file.write("\nDEFINED VALUES\n")
            for x in sorted(vals_def[ft].items(), key=lambda y: (-y[1], y[0])):
                result_file.write("{} x {}\n".format(*x))
            result_file.close()
            result_file = outfile("{}.rst".format(ft))
            result_file.write('''
{ft}
{ln}
.. literalinclude:: ../values/{ft} values.txt
'''.format(ft=ft, ln=('=' * len(ft))))
            result_file.close()
        
        for ft in edge_feats:
            result_file = outfile("edge {} values.txt".format(ft))
            result_file.write("\nVALUES\n")
            for x in sorted(vals[ft].items(), key=lambda y: (-y[1], y[0])):
                result_file.write("{} x {}\n".format(*x))
            result_file.close()
        
        result_file = outfile("1_types_node.txt")
        for ft in sorted(n_otypesi):
            for otype in sorted(n_otypesi[ft]):
                result_file.write("{}\t{}\t{}\t{}\n".format(ft, otype, *n_otypesi[ft][otype]))
        result_file.close()
        
        result_file = outfile("1_types_edge.txt")
        for ft in sorted(e_otypesi):
            for otype in sorted(e_otypesi[ft]):
                result_file.write("{}\t{}->{}\t{}\n".format(ft, otype[0], otype[1], e_otypesi[ft][otype]))
        result_file.close()
        
        n_vals_def = collections.defaultdict(lambda: 0)
        n_vals_undef = collections.defaultdict(lambda: 0)
        for ft in node_feats:
            for val in vals_def[ft]:
                n_vals_def[ft] += vals_def[ft][val]
            for val in vals_undef[ft]:
                n_vals_undef[ft] += vals_undef[ft][val]
        
        index_file = outfile("index.rst")
        index_file.write('''
Feature Index
#############
''')
        for ft in sorted(node_feats):
            index_file.write('''
:doc:`{ft} <{ft}>`
'''.format(ft=ft))
        index_file.close()

        summary_file = outfile("0_summary_node.csv")
        summary_file.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
            'Feature',
            'val (-)',
            'val (+)',
            '#vals (-)',
            '#vals (+)',
            'occs (-)',
            'occs (+)',
            '\t'.join(["{} (-)\t{} (+)".format(otype, otype) for otype in node_otypes]),
        ))
                           
        for ft in node_feats:
            summary_file.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                ft,
                '',
                '',
                len(vals_undef[ft]),
                len(vals_def[ft]),
                n_vals_undef[ft],
                n_vals_def[ft],
                '\t'.join(["{}\t{}".format(*n_otypes[otype][ft]) for otype in node_otypes]),
            ))
            for (val, n) in sorted(vals_undef[ft].items(), key=lambda x: (-x[1], x[0])):
                summary_file.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                    '',
                    val,
                    '',
                    '',
                    '',
                    n,
                    '',
                    '\t' * (2 * len(node_otypes) - 1),
            ))
            i = 0
            for (val, n) in sorted(vals_def[ft].items(), key=lambda x: (-x[1], x[0])):
                i += 1
                if i > VALUE_THRESHOLD:
                    summary_file.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                        '',
                        '',
                        "{} MORE".format(len(vals_def[ft]) - VALUE_THRESHOLD),
                        '',
                        '',
                        '',
                        '',
                        '\t' * (2 * len(node_otypes) - 1),
                    ))
                    break
                summary_file.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                    '',
                    '',
                    val,
                    '',
                    '',
                    '',
                    n,
                    '\t' * (2 * len(node_otypes) - 1),
            ))
        summary_file.close()

        e_vals = collections.defaultdict(lambda: 0)
        for ft in edge_feats:
            for val in vals[ft]:
                e_vals[ft] += vals[ft][val]
        
        summary_file = outfile("0_summary_edge.csv")
        summary_file.write("{}\t{}\t{}\t{}\t{}\n".format(
            'Feature',
            'val',
            '#vals',
            'occs',
            '\t'.join(["{}->{}".format(*otype) for otype in edge_otypes]),
        ))
                           
        for ft in edge_feats:
            summary_file.write("{}\t{}\t{}\t{}\t{}\n".format(
                ft,
                '',
                len(vals[ft]),
                e_vals[ft],
                '\t'.join(["{}".format(e_otypes[otype][ft]) for otype in edge_otypes]),
            ))
            i = 0
            for (val, n) in sorted(vals[ft].items(), key=lambda x: (-x[1], x[0])):
                i += 1
                if i > VALUE_THRESHOLD:
                    summary_file.write("{}\t{}\t{}\t{}\n".format(
                        '',
                        "{} MORE".format(len(vals[ft]) - VALUE_THRESHOLD),
                        '',
                        '\t' * (len(edge_otypes) - 1),
                    ))
                    break
                summary_file.write("{}\t{}\t{}\t{}\n".format(
                    '',
                    val,
                    n,
                    '\t' * (len(edge_otypes) - 1),
            ))
        summary_file.close()
        
        msg("Done")
