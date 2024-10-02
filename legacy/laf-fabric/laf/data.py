import os
import glob
import time
import array
import pickle
import collections
import gzip
from .names import Names, FabricError
from .parse import parse
from .model import model

GZIP_LEVEL = 2
PICKLE_PROTOCOL = 3

class LafData(object):
    '''Manage the compiling and loading of LAF/GraF data.'''

    def __init__(self):
        self.log = None
        self.clog = None
        self.data_items = {}

    def prepare_dirs(self, annox):
        env = self.names.env
        try:
            if not os.path.exists(env['m_compiled_dir']): os.makedirs(env['m_compiled_dir'])
        except os.error as e:
            raise FabricError("could not create bin directory {}".format(env['m_compiled_dir']), self.stamp, cause=e)
        for anx in annox:
            try:
                a_compiled_dir = env['annox'][anx]['a_compiled_dir']
                if not os.path.exists(a_compiled_dir): os.makedirs(a_compiled_dir)
            except os.error as e:
                raise FabricError("could not create bin directory {}".format(a_compiled_dir), self.stamp, cause=e)
        try:
            if not os.path.exists(env['task_dir']): os.makedirs(env['task_dir'])
        except os.error as e:
            raise FabricError("could not create result directory {}".format(env['task_dir']), self.stamp, cause=e)

    def finish_task(self, show=True):
        '''Close all open files that have been opened by the API'''
        task_dir = self.names.env['task_dir']
        for handle in self.result_files:
            if handle and not handle.closed: handle.close()
        self.result_files = []
        self._flush_logfile()
        mg = []
        if show:
            self.stamp.Nmsg("Results directory:\n{}".format(task_dir))
            for name in sorted(os.listdir(path=task_dir)):
                path = "{}/{}".format(task_dir, name) 
                size = os.path.getsize(path)
                mtime = time.ctime(os.path.getmtime(path))
                mg.append("{:<30} {:>12} {}".format(name, size, mtime))
            self.stamp.Nmsg("\n" + "\n".join(mg), withtime=False)
        self._finish_logfile()

    def _finish_logfile(self, compile=None):
        the_log = self.log if compile == None else self.clog
        try:
            the_log.write("\nCLOSED AT:{}".format(time.strftime("%Y-%m-%dT%H-%M-%S", time.gmtime())))
            the_log.close()
        except: pass
        self.stamp.disconnect_log()
        if compile == None: self.log = None
        else: self.clog = None

    def _flush_logfile(self):
        try: self.log.flush()
        except: pass

    def add_logfile(self, compile=None):
        env = self.names.env
        log_dir = env['task_dir'] if compile == None else env["{}_compiled_dir".format(compile)] if compile == 'm' else env['annox'][compile[1:]]["{}_compiled_dir".format(compile[0])]
        log_path = env['log_path'] if compile == None else env["{}_compiled_path".format(compile)] if compile == 'm' else env['annox'][compile[1:]]["{}_compiled_path".format(compile[0])]
        the_log = self.log if compile == None else self.clog
        try:
            if not os.path.exists(log_dir): os.makedirs(log_dir)
        except os.error as e:
            raise FabricError("could not create log directory {}".format(log_dir), self.stamp, cause=e)

        if not the_log:
            the_log = open(log_path, "w", encoding="utf-8")
            the_log.write("OPENED AT:{}\n".format(time.strftime("%Y-%m-%dT%H-%M-%S", time.gmtime())))
            self.stamp.connect_log(the_log)
            self.stamp.Nmsg("LOGFILE={}".format(log_path))
            if compile == None: self.log = the_log
            else: self.clog = the_log

    def compile_all(self, force):
        env = self.names.env
        compile_uptodate = collections.OrderedDict()
        compile_uptodate['m'] = not os.path.exists(env['m_source_path']) or (
                os.path.exists(env['m_compiled_path']) and
                os.path.getmtime(env['m_compiled_path']) >= os.path.getmtime(env['m_source_path'])
            )

        for anx in sorted(env['annox']):
            uptodate = True
            for afile in glob.glob('{}/*.xml'.format(env['annox'][anx]['a_source_dir'])):
                this_uptodate = (
                    os.path.exists(env['annox'][anx]['a_compiled_path']) and
                    os.path.getmtime(env['annox'][anx]['a_compiled_path']) >= os.path.getmtime(afile)
                )
                if not this_uptodate:
                    uptodate = False
                    break
            compile_uptodate['a{}'.format(anx)] = uptodate
        has_compiled_main = False
        for origin in compile_uptodate:
            origin_type = origin if origin == 'm' else origin[0]
            origin_spec = env['source'] if origin == 'm' else origin[1:]
            if (not compile_uptodate[origin]) or force[origin_type] or has_compiled_main:
                self.stamp.Nmsg("BEGIN COMPILE {}: {}".format(origin_type, origin_spec))
                self._clear_origin_unnec(origin)
                if origin_type == 'a':
                    self._load_extra(['mXnf()', 'mXef()'] + Names.maingroup('G'))
                self._compile_origin(origin)
                if origin_type == 'm':
                    has_compiled_main = True
                self.stamp.Nmsg("END   COMPILE {}: {}".format(origin_type, origin_spec))
            else: self.stamp.Dmsg("COMPILING {}: {}: UP TO DATE".format(origin_type, origin_spec))
            the_time = 'UNSPECIFIED'
            compiled_path = env['{}_compiled_path'.format(origin)] if origin_type == 'm' else env['annox'][origin_spec]["{}_compiled_path".format(origin_type)]
            with open(compiled_path) as h:
                last_line = list(h)[-1]
                if ':' in last_line:
                    the_time = last_line.split(':', 1)[1]
            self.stamp.Nmsg("USING {}: {} DATA COMPILED AT: {}".format('main' if origin_type == 'm' else 'annox', origin_spec, the_time))
        if has_compiled_main:
            for origin in (compile_uptodate):
                self._clear_origin_unnec(origin)
            self.names.setenv()

    def _compile_origin(self, origin):
        env = self.names.env
        self.add_logfile(compile=origin)
        self._parse(origin)
        self._model(origin)
        self._store_origin(origin)
        self._finish_logfile(compile=origin)

    def _clear_origin_unnec(self, origin):
        dkeys = list(self.data_items.keys())
        for dkey in sorted(dkeys):
            if dkey in self.names.req_data_items: continue
            (dorigin, dgroup, dkind, ddir, dcomps) = Names.decomp_full(dkey)
            if dorigin == origin: self._clear_file(dkey)

    def _clear_file(self, dkey):
        if dkey in self.data_items: del self.data_items[dkey]

    def unload_all(self):
        self.loadspec = {}
        for dkey in self.data_items: del self.data_items[dkey]
        self.names.req_data_items = collections.OrderedDict()
        self.names._old_data_items = collections.OrderedDict()

    def load_all(self, req_items, prepare, add):
        dkeys = self.names.request_files(req_items, prepare[0])
        self.loadspec = dkeys
        self.prepare_dict = prepare[0]
        self.prepare_init = prepare[1]
        for dkey in dkeys['keep']:
            if dkey not in dkeys['prep']:
                self.stamp.Dmsg("keep {}".format(Names.dmsg(dkey))) 
        if not add:
            for dkey in dkeys['clear']:
                if dkey not in dkeys['prep']:
                    self.stamp.Dmsg("clear {}".format(Names.dmsg(dkey))) 
                    self._clear_file(dkey)
        for dkey in dkeys['load']:
            if dkey not in dkeys['prep']:
                self.stamp.Dmsg("load {}".format(Names.dmsg(dkey))) 
                ism = self.names.dinfo(dkey)[0]
                self._load_file(dkey, accept_missing=not ism)

    def _load_extra(self, dkeys):
        for dkey in dkeys:
            self.stamp.Dmsg("load {}".format(Names.dmsg(dkey))) 
            ism = self.names.dinfo(dkey)[0]
            self._load_file(dkey, accept_missing=not ism)

    def prepare_all(self, api):
        if hasattr(self, 'api'):
            self.api.update(api)
        else:
            self.api = api
        dkeys = self.loadspec
        for dkey in dkeys['keep']:
            if dkey in dkeys['prep']:
                self.stamp.Dmsg("keep {}".format(Names.dmsg(dkey))) 
        for dkey in dkeys['clear']:
            if dkey in dkeys['prep']:
                self.stamp.Dmsg("clear {}".format(Names.dmsg(dkey))) 
                self._clear_file(dkey)
        for dkey in dkeys['load']:
            if dkey in dkeys['prep']:
                self.stamp.Nmsg("prep {}".format(Names.dmsg(dkey))) 
                self._load_file(dkey, accept_missing=False)

    def _load_file(self, dkey, accept_missing=False):
        env = self.names.env
        dprep = self.names.dinfo(dkey)[-1]
        if dprep:
            if dkey not in self.prepare_dict:
                raise FabricError("Cannot prepare data for {}. No preparation method available.".format(Names.dmsg(dkey)), self.stamp)
                return
            self.names.setenv(zspace=self.prepare_dict[dkey][-1])
        (ism, dloc, dfile, dtype, dprep) = self.names.dinfo(dkey)
        dpath = "{}/{}".format(dloc, dfile)
        prep_done = False
        if dprep:
            (method, method_source, replace, zspace) = self.prepare_dict[dkey] 
            up_to_date = os.path.exists(dpath) and \
                os.path.getmtime(dpath) >= os.path.getmtime(method_source) and \
                os.path.getmtime(dpath) >= os.path.getmtime(env['m_compiled_path']) 
            if not up_to_date:
                self.stamp.Nmsg("PREPARING {}".format(Names.dmsg(dkey)))
                compiled_dir = self.names.env['{}_compiled_dir'.format('z')]
                try:
                    if not os.path.exists(compiled_dir): os.makedirs(compiled_dir)
                except os.error as e:
                    raise FabricError("could not create compiled directory {}".format(compiled_dir), self.stamp, cause=e)
                newdata = method(self.api)
                self.data_items[dkey] = newdata
                self.stamp.Nmsg("WRITING {}".format(Names.dmsg(dkey)))
                self._store_file(dkey)
                prep_done = True
        if not os.path.exists(dpath):
            if not accept_missing:
                raise FabricError("Cannot load data for {}: File does not exist: {}.".format(Names.dmsg(dkey), dpath), self.stamp)
            return
        if not prep_done:
            newdata = None
            if dtype == 'arr':
                newdata = array.array('I')
                with gzip.open(dpath, "rb") as f: contents = f.read()
                newdata.frombytes(contents)
            elif dtype == 'dct':
                with gzip.open(dpath, "rb") as f: newdata = pickle.load(f)
            elif dtype == 'str':
                with gzip.open(dpath, "rt", encoding="utf-8") as f: newdata = f.read(None)
            self.data_items[dkey] = newdata
        if dprep:
            if replace:
                okey = Names.orig_key(dkey)
                if okey not in self.data_items:
                    raise FabricError("There is no orginal {} to be replaced by {}".format(Names.dmsg(okey), Names.dmsg(dkey)), self.stamp)
                    return 
                if okey == dkey:
                    self.stamp.Wmsg("Data to be replaced {} is identical to replacement".format(Names.dmsg(okey)))
                else:
                    self.data_items[okey] = self.data_items[dkey]

    def _store_origin(self, origin):
        env = self.names.env
        origin_type = origin if origin == 'm' else origin[0]
        origin_spec = env['source'] if origin == 'm' else origin[1:]
        self.stamp.Nmsg("WRITING RESULT FILES for {}: {}".format(origin_type, origin_spec))
        data_items = self.data_items
        for dkey in sorted(data_items):
            (dorigin, dgroup, dkind, ddir, dcomps) = Names.decomp_full(dkey)
            if dorigin == origin: self._store_file(dkey)

    def _store_file(self, dkey):
        (ism, dloc, dfile, dtype, dprep) = self.names.dinfo(dkey)
        dpath = "{}/{}".format(dloc, dfile)
        if dpath == None: return
        thedata = self.data_items[dkey]
        self.stamp.Dmsg("write {}".format(Names.dmsg(dkey))) 
        if dtype == 'arr':
            with gzip.open(dpath, "wb", compresslevel=GZIP_LEVEL) as f: thedata.tofile(f)
        elif dtype == 'dct':
            with gzip.open(dpath, "wb", compresslevel=GZIP_LEVEL) as f: pickle.dump(thedata, f, protocol=PICKLE_PROTOCOL)
        elif dtype == 'str':
            with gzip.open(dpath, "wt", encoding="utf-8") as f: f.write(thedata)

    def _parse(self, origin):
        env = self.names.env
        origin_type = origin if origin == 'm' else origin[0]
        origin_spec = env['source'] if origin == 'm' else origin[1:]
        self.stamp.Nmsg("PARSING ANNOTATION FILES")
        env = self.names.env
        if origin_type == 'm':
            source_dir = env['{}_source_dir'.format(origin)]
            source_path = env['{}_source_path'.format(origin)]
            compiled_dir = env['{}_compiled_dir'.format(origin)]
        else:
            source_dir = env['annox'][origin_spec]['{}_source_dir'.format(origin_type)]
            source_path = env['annox'][origin_spec]['{}_source_path'.format(origin_type)]
            compiled_dir = env['annox'][origin_spec]['{}_compiled_dir'.format(origin_type)]
        self.cur_dir = os.getcwd()
        if not os.path.exists(source_path):
            raise FabricError("LAF header does not exists {}".format(source_path), self.stamp)
        try:
            os.chdir(source_dir)
        except os.error as e:
            raise FabricError("could not change to LAF source directory {}".format(source_dir), self.stamp, cause=e)
        try:
            if not os.path.exists(compiled_dir): os.makedirs(compiled_dir)
        except os.error as e:
            os.chdir(self.cur_dir)
            raise FabricError("could not create directory for compiled source {}".format(compiled_dir), self.stamp, cause=e)
        parse(
            origin,
            source_path,
            self.stamp,
            self.data_items,
        )
        os.chdir(self.cur_dir)

    def _model(self, origin):
        self.stamp.Nmsg("MODELING RESULT FILES")
        model(origin, self.data_items, self.stamp)

    def __del__(self):
        self.stamp.Nmsg("END")
        for handle in (self.log,):
            if handle and not handle.closed: handle.close()

