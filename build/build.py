"""This program is used to build the application so that it can be
loaded onto a Digi device. It is also used to build the documentation
and create customer releases.
"""

from ConfigParser import RawConfigParser
from os.path import join
from py_compile import compile
import filecmp
import fnmatch
import imp
import logging
import modulefinder
import optparse
import os
import pprint
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

logging.basicConfig(format="%(asctime)s: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# do not build files that have a __platform__ for which the following
# expression does not return true
TARGET_PLATFORM_MATCHER = lambda x: x.startswith('digi')
SPHINX_BUILD = r'C:\python24\scripts\sphinx-build.exe'

# The build script will check the directories on sys.path to see if any
# of them include directories with these names. Any files in the
# 'COPY_TO_OUT_DIR' will be copied to the 'OUT_PATH'. Any files in the
# 'COPY_TO_OUT_ZIP_DIR' will be copied to 'OUT_PATH/DEFAULT_OUT_ZIP'.
COPY_TO_OUT_DIR = 'to_out'
COPY_TO_OUT_ZIP_DIR = 'to_out_zip'

DEFAULT_SRC_DIR = 'src'
DEFAULT_TMP_DIR = 'tmp'
DEFAULT_OUTPUT_DIRECTORY = 'out'
DEFAULT_OUT_ZIP = 'appfiles.zip'
DEFAULT_KICKERS = ['main.py', 'fake.py']

DEFAULT_EXCLUDE_MODULES = [
    # Common OS specific modules that ModuleFinder likes to suck in.

     # We don't run these OSes
    "ntpath",
    "macpath",
    "os2emxpath",
    "nturl2path",
    "macurl2path",

    # Other things that can get in the way, and don't seem likely
    "gopherlib",
    # "ftplib",
    "doctest",
    "pydoc",
    # "unittest",
    "pydev",
    "py_compile",
    "BaseHTTPServer",
    "netbios",
    "win32con",
    "win32evtlogutil",
    "winerror",

    # Files that should be in Digi's python.zip already
    "Queue",
    "StringIO",
    "__future__",
    "_abcoll",
    "abc",
    "atexit",
    "bdb",
    "cmd",
    "code",
    "codeop",
    "copy_reg",
    "linecache",
    "os",
    "pdb",
    "posixpath",
    "pprint",
    "random",
    "re",
    "repr",
    "socket",
    "sre",
    "sre_compile",
    "sre_constants",
    "sre_parse",
    "stat",
    "string",
    "threading",
    "traceback",
    "types",
    "warnings",
    "codecs",
]

# Python 2.4 does not include the relpath function so define
# it here if necessary
try:
    from os.path import relpath
except ImportError:
    def relpath(path, start=os.path.curdir):
        """Return a relative version of a path"""
        if not path:
            raise ValueError("no path specified")

        start_list = os.path.abspath(start).split(os.path.sep)
        path_list = os.path.abspath(path).split(os.path.sep)

        # Work out how much of the filepath is shared by start and path.
        i = len(os.path.commonprefix([start_list, path_list]))

        rel_list = [os.path.pardir] * (len(start_list) - i) + path_list[i:]
        if not rel_list:
            return start()
        return join(*rel_list)


def _clean_path(path):
    return os.path.abspath(path)


class BuildConfiguration(object):
    """Encapsulate input state for a build"""

    @property
    def output_directory_path(self):
        return _clean_path(self.output_directory)

    @property
    def source_directory_path(self):
        return _clean_path(self.source_directory)

    @property
    def tmp_directory_path(self):
        return _clean_path(self.tmp_directory)

    def __init__(self):
        self.source_directory = DEFAULT_SRC_DIR
        self.tmp_directory = DEFAULT_TMP_DIR
        self.output_directory = DEFAULT_OUTPUT_DIRECTORY
        self.exclude_modules = DEFAULT_EXCLUDE_MODULES[:]
        self.out_zip = DEFAULT_OUT_ZIP
        self.resource_filters = []
        self.kickers = DEFAULT_KICKERS[:]
        self.epoxy_use_dict_config = False
        self.epoxy_config_to_zipfile = False
        self.epoxy_config_to_fs = True
        self.exclude_stdlib = False

    def _get_config(self, parser, option, default=None):
        if parser.has_option('build', option):
            return parser.get('build', option)
        return default

    def _get_epoxy_config(self, parser, option, default=None):
        if parser.has_option('epoxy', option):
            return parser.get('epoxy', option)
        return default

    def _get_epoxy_boolean(self, parser, option, default=None):
        if parser.has_option('epoxy', option):
            return parser.getboolean('epoxy', option)
        return default

    def _get_config_list(self, parser, option, default=None):
        raw_value = self._get_config(parser, option, None)
        if raw_value is None:
            return default
        list_values = []
        for item in raw_value.split():
            item = item.strip()
            if len(item) > 0:
                list_values.append(item)
        return list_values

    def update_from_config(self, *config_search_paths):
        parser = RawConfigParser()
        parser.read(config_search_paths)
        if not parser.has_section('build'):
            return
        self.source_directory = self._get_config(
            parser, 'source_directory', self.source_directory)
        self.output_directory = self._get_config(
            parser, 'output_directory', self.output_directory)
        self.out_zip = self._get_config(
            parser, 'output_zipfile', self.out_zip)
        self.kickers = self._get_config_list(
            parser, 'kickers', self.kickers)
        self.resource_filters = self._get_config_list(
            parser, 'resource_filters', self.resource_filters)
        self.exclude_stdlib = self._get_config(
            parser, 'exclude_stdlib', self.exclude_stdlib)
        extra_excludes = self._get_config_list(parser, 'exclude_modules', [])
        self.exclude_modules.extend(extra_excludes)

        if not parser.has_section('epoxy'):
            return
        self.epoxy_use_dict_config = self._get_epoxy_boolean(
            parser, 'use_dict_config', self.epoxy_use_dict_config)
        self.epoxy_config_to_fs = self._get_epoxy_boolean(
            parser, 'write_config_to_fs', self.epoxy_config_to_fs)
        self.epoxy_config_to_zipfile = self._get_epoxy_boolean(
            parser, 'write_config_to_zip', self.epoxy_config_to_zipfile)
        if self.epoxy_use_dict_config:
            self.exclude_modules.append("yaml")

#===============================================================================
# Setup the Option Parser and parse arguments into options, args
#===============================================================================
def _get_parser():
    parser = optparse.OptionParser()
    parser.add_option('-v', '--verbose',
                      action="store_true",
                      dest="verbose",
                      default=False,
                      help="Turn on verbose mode")
    parser.add_option('-c', '--clean',
                      action="store_true",
                      dest="clean",
                      default=False,
                      help="Do a clean build (removes all build directories prior to build)")
    parser.add_option('--config',
                      action="store",
                      dest="config",
                      default=None,
                      help="Specify the path to a config file to use")
    parser.add_option('-t', '--test',
                      action="store",
                      dest="test_package",
                      default=None,
                      help="Build test runner for specified test package")
    return parser

def _setup_env(build_config, clean):
    for d in (build_config.tmp_directory_path,
              build_config.output_directory_path):
        if clean:
            shutil.rmtree(d, True)
        try:
            os.makedirs(d)
        except OSError:
            pass

def _find_dirs(starting_dir, dir_name):
    for root, dirs, files in os.walk(starting_dir):
        for dir in dirs:
            if dir == dir_name:
                yield os.path.join(root, dir)

def _find_addl_files():
    files_to_copy = []
    for path in sys.path:
        for dirpath in _find_dirs(path, COPY_TO_OUT_DIR):
            for root, dirs, files in os.walk(dirpath):
                rel_root = root.replace(dirpath, "")
                if rel_root.startswith(os.sep):
                    rel_root = rel_root[len(os.sep):]
                for filename in files:
                    filename = os.path.join(rel_root, filename)
                    src = os.path.join(root, filename)
                    files_to_copy.append((src, filename))
    return files_to_copy


def _matches_any_glob(target, patterns):
    for pattern in patterns:
        if fnmatch.fnmatch(target, pattern):
            return True
    return False


def _is_stdlib(filename):
    """Return True if the file appears to be part of the standard library"""
    stdlib_root = os.path.dirname(os.__file__)
    rootpath, _ext = os.path.splitext(filename)
    if not filename.startswith(stdlib_root):
        return False
    if os.path.exists(rootpath + ".egg-info"):
        return False

    # Even if we are in the same dir structure as the stdlib, we aren't
    # in the stdlib unless we are a part of the contiguous package
    # tree of the standard library.
    dirs_between_stdlib_and_mine = \
        os.path.dirname(filename).replace(stdlib_root, '').split(os.path.sep)
    if dirs_between_stdlib_and_mine:
        curpath = os.path.join(stdlib_root, dirs_between_stdlib_and_mine[0])
        for dirname in dirs_between_stdlib_and_mine[1:]:
            curpath = os.path.join(curpath, dirname)
            if not "__init__.py" in os.listdir(curpath):
                return False
    return True


def _fully_find_module(name):
    """same as imp.find_module, but handles dotted names"""
    if '.' in name:
        package_name, module_name = name.rsplit('.', 1)
        package = __import__(package_name, globals(), locals(), [package_name, ])
        return imp.find_module(module_name, [os.path.dirname(package.__file__)])
    else:
        return imp.find_module(name)


def _find_kickers(candidates):
    """Given a set of candidates which may be python files or yaml, find kickers
    
    This function was added in order to be able to handle yaml files being
    used with epoxy in order to find kickers that are declared
    dynamically.

    """
    kickers = []
    for candidate in candidates:
        if candidate.endswith('.py'):
            kickers.append(candidate)
        elif candidate.endswith('.yml') or candidate.endswith('.yaml'):
            from epoxy.configuration import YamlConfigurationLoader
            loader = YamlConfigurationLoader(candidate)
            data = loader.load_configuration()
            for component_name, component in data.get('components', {}).iteritems():
                class_path = component.get('class', None)
                if class_path is None:
                    continue
                module_name = class_path.split(':')[0]
                (file, pathname, _desc) = _fully_find_module(module_name)
                if os.path.isdir(pathname):
                    pathname = os.path.join(pathname, "__init__.py")
                kickers.append(pathname)

    # remove duplicates
    return list(set(kickers))


def _perform_build(build_config):
    src_to_analyze = _find_kickers(build_config.kickers)

    # This will check for source files in build_config.source_directory_path other than KICKER.
    addl_files = [src_file
                  for src_file
                  in os.listdir(build_config.source_directory_path)
                  if (os.path.isfile(src_file) and
                      os.path.splitext(src_file)[1] in ('.py', '.pyc') and
                      src_file not in src_to_analyze)]
    if addl_files:
        addl_files_script = os.path.join((build_config.tmp_directory_path), 'addlfiles.py')
        f = open(addl_files_script, 'w')
        try:
            for src_file in addl_files:
                f.write('import %s\n' % src_file)
        finally:
            f.close()
        src_to_analyze.append(addl_files_script)

    temp_dir = tempfile.mkdtemp(dir=build_config.tmp_directory_path)
    mf = modulefinder.ModuleFinder(excludes=build_config.exclude_modules)

    for src_file in src_to_analyze:
        src_file = os.path.join(build_config.source_directory_path, src_file)
        logger.info("Analyzing: %s", src_file)
        mf.load_file(src_file)

    for (name, mod) in mf.modules.iteritems():
        logger.debug("References: %s", name)
        if not _matches_any_glob(name, build_config.exclude_modules):
            if mod.__file__:
                filename = mod.__file__
                if not (build_config.exclude_stdlib and _is_stdlib(filename)):
                    if filename.endswith(".py"):
                        first_line = open(filename, 'r').readline()
                        matches = re.findall("PLATFORM:(\w+)", first_line)
                        if len(matches) == 0 or TARGET_PLATFORM_MATCHER(matches[0]):
                            start_dir = '.'
                            for path in sys.path:
                                if filename.startswith(path) and len(path) > len(start_dir):
                                    start_dir = path
                            dst = join(temp_dir, relpath(filename, start_dir)) + "c"
                            if not os.path.isdir(os.path.dirname(dst)):
                                os.makedirs(os.path.dirname(dst))
                            logger.debug("..compiling %s --> %s", filename, dst)
                            compile(filename, dst)
                        else:
                            logger.debug(".. skipping (PLATFORM: %s)" % matches[0])
                    else:
                        logger.debug(".. skipping (stdlib)")
                else:
                    logger.debug("..skipping (not Python file)")
            else:
                logger.debug("..skipping (builtin)")
        else:
            logger.debug("..skipping (in EXCLUDE_MODULES)")


    # check for static resources that should be included based on filters
    for dirpath, dirnames, filenames in os.walk(build_config.source_directory_path):
        for filename in filenames:
            full_filename = os.path.abspath(os.path.join(dirpath, filename))
            relative_path = relpath(full_filename, build_config.source_directory_path)
            if _matches_any_glob(relative_path, build_config.resource_filters):
                dst_path = join(temp_dir, relative_path)
                if not os.path.isdir(os.path.dirname(dst_path)):
                    os.makedirs(os.path.dirname(dst_path))
                shutil.copyfile(full_filename, dst_path)
                print "STATIC RESOURCE %s" % full_filename

    package_file = join(build_config.tmp_directory_path, build_config.out_zip)
    z = zipfile.ZipFile(file=package_file, mode="w", compression=zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(temp_dir):
        root = root.replace(temp_dir, "")
        if root.startswith(os.sep):
            root = root[len(os.sep):]
        if not ("__init__.pyc" in files or "__init__.py" in files) and len(root) > 0:
            files.append("__init__.py")
            filename = os.path.join(root, "__init__.py")
            src = os.path.join(temp_dir, filename)
            f = open(os.path.join(temp_dir, filename), "wb")
            try:
                f.write("")
            finally:
                f.close()
        for filename in files:
            filename = os.path.join(root, filename)
            src = os.path.join(temp_dir, filename)
            logger.debug("Writing %s --> %s", src, os.path.join(package_file, filename))
            z.write(src, filename)

    for path in sys.path:
        for dirpath in _find_dirs(path, build_config.output_directory_path):
            for root, dirs, files in os.walk(dirpath):
                rel_root = root.replace(dirpath, "")
                if rel_root.startswith(os.sep):
                    rel_root = rel_root[len(os.sep):]
                for filename in files:
                    src = os.path.join(root, filename)
                    filename = os.path.join(rel_root, filename)
                    logger.debug("Writing %s --> %s", src, os.path.join(package_file, filename))
                    z.write(src, filename)

    files_to_copy = [(package_file, os.path.basename(package_file))]
    for f in build_config.kickers:
        if f.endswith('.yml'):
            from epoxy.configuration import YamlConfigurationLoader
            loader = YamlConfigurationLoader(f)
            data = loader.load_configuration()
            try:
                del data['extends']
            except:
                pass

            tmp_path = tempfile.mktemp()
            tmp = open(tmp_path, 'wb')
            if build_config.epoxy_use_dict_config:
                try:
                    tmp.write('config = %s' % pprint.pformat(data))
                finally:
                    tmp.close()
                if build_config.epoxy_config_to_zipfile:
                    z.write(tmp_path, 'appconfig.py')
                if build_config.epoxy_config_to_fs:
                    files_to_copy.append((tmp_path, 'appconfig.py'))
            else:
                import yaml
                try:
                    yaml.dump(data, tmp)
                finally:
                    tmp.close()
                files_to_copy.append((tmp_path, 'app.yml'))
        else:
            source_file_path = os.path.join(build_config.source_directory_path, f)
            if os.path.exists(source_file_path):
                files_to_copy.append((source_file_path, f))
            elif os.path.exists(f):
                files_to_copy.append((f, f))
    z.close()

    files_to_copy.extend([(os.path.join(build_config.source_directory_path, src_file), src_file)
                          for src_file in addl_files])

    shutil.rmtree(temp_dir, ignore_errors=True)

    return files_to_copy


def _need_to_copy(src, dst):
    if os.path.exists(dst) and not os.path.isdir(src) and filecmp.cmp(src, dst, False):
        return False
    return True

def _write_to_out(filename, file_contents):
    dst = os.path.join(OUT_PATH, filename)
    dst_file = open(dst, 'w')
    try:
        dst_file.write(file_contents)
    finally:
        dst_file.close()

def _copy_to_out(out_path, files_to_copy):
    for src, dst in files_to_copy:
        dst = join(out_path, dst)
        try:
            os.makedirs(os.path.dirname(dst))
        except OSError:
            pass
        if _need_to_copy(src, dst):
            logger.info("Copying %s to %s", src, out_path)
            if os.path.isdir(src):
                shutil.rmtree(dst, True)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        else:
            logger.info("Skipping unmodified file %s", src)

#===================================================================================================
# Test Discovery and Building
#
# Since the source files are not available on the gateway, we need to do discovery at build
# time.  We generate a python file based on gwtest_template.py which includes references
# to all modules to be tested, along with our test runner and some basic test logic.
#===================================================================================================
def fill_test_template(test_modules,
                       template_file=os.path.join(os.path.dirname(__file__), 'gwtest_template.py')):
    f = open(template_file, 'r')
    try:
        template_text = f.read()
    finally:
        f.close()

    return template_text.replace('{test_modules}',
                                 ',\n'.join(["    '%s'" % x for x in test_modules]))

class TestFinder(object):
    """Quick and easy test finder which finds all unit tests in test directory"""

    def __init__(self, test_package):
        # test package should look like: my_application.test
        self.test_package = test_package
        print (test_package, test_package.split('.')[-1])
        package_mod = __import__(test_package, globals(), locals(), [test_package.split('.')[-1], ])
        self.test_directory = os.path.dirname(package_mod.__file__)

    def _make_package_name(self, full_path):
        assert full_path.endswith('.py')

        rel_path = full_path.replace(self.test_directory, '')
        module_parts = self.test_package.split('.') + rel_path.split(os.sep)
        module_parts[-1] = module_parts[-1][:-3]  # remove .py
        if module_parts[-1] == '__init__':
            module_parts = module_parts[:-1]  # drop __init__ foo.bar.__init__ -> foo.bar
        return '.'.join([x for x in module_parts if len(x) > 0])

    def find_test_modules(self):
        test_modules = []
        for dirpath, dirnames, filenames in os.walk(self.test_directory):
            full_dir_path = os.path.join(self.test_directory, dirpath)
            for filename in filenames:
                full_file_path = os.path.join(full_dir_path, filename)
                if full_file_path.endswith('.py'):
                    test_modules.append(self._make_package_name(full_file_path))
        return test_modules

    def make_suite(self):
        loader = unittest.TestLoader()
        return loader.loadTestsFromNames(self.find_test_modules())


def main():
    """Parse command-line arguments and initiate the build process"""
    if __debug__:  # run ourself in subprocess
        print "Executing in subprocess"
        args = [sys.executable, '-OO'] + sys.argv
        sys.exit(subprocess.call(args))

    # HACK: work around deficiencies with modulefinder not examining
    # __path__ along the way (known limitation of modulefinder).
    try:
        import spectrum
        import spectrum.lib
        for path in spectrum.__path__:
            modulefinder.AddPackagePath('spectrum', path)
        for path in spectrum.lib.__path__:
            modulefinder.AddPackagePath('spectrum.lib', path)
    except ImportError:
        pass

    parser = _get_parser()
    options, args = parser.parse_args()
    if options.verbose:
        logger.setLevel(logging.DEBUG)

    build_config = BuildConfiguration()
    if options.config is not None:
        build_config.update_from_config(options.config)

    _setup_env(build_config, options.clean)

    files_to_copy = []
    if options.test_package is not None:
        # first, find the tests
        test_modules = TestFinder('my_application.test').find_test_modules()
        testfile_contents = fill_test_template(test_modules=test_modules)
        _write_to_out('runtests.py', testfile_contents)

    # perform the build
    files_to_copy.extend(_perform_build(build_config))
    files_to_copy.extend(_find_addl_files())
    _copy_to_out(build_config.output_directory_path, files_to_copy)


if __name__ == '__main__':
    print __file__
    main()
