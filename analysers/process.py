from subprocess           import PIPE, Popen
from sys                  import stderr
from os                   import path, O_NONBLOCK
from ConfigParser         import ConfigParser
from fcntl                import fcntl, F_GETFL, F_SETFL
import time
import logging

logger = logging.getLogger(__name__)

config = ConfigParser()
_package_directory = path.dirname(__file__)

config.read(path.join(_package_directory, "../external.conf"))

class Process(object):
    '''Intended to be an abstract class
    Its subclasses must have an attribute "params" of the type list and a string attribute "path_to_bin"
    '''
    def __init__(self, path_to_bin, disposable, time_out = None, *params):
        self.path_to_bin = path_to_bin
        self.params      = params
        self._disposable = disposable
        self._time_out   = time_out
        self._proc       = None
        try:
            self._proc_name = str(self.__class__).split('\'')[1].split('.')[-1]
        except IndexError:
            self._proc_name = str(self.__class__)
        self._init_popen()

    def _read_line(self, stop_condition = lambda out: False):
        count = 0
        out = []
        logger.debug('{proc}: reading line'.format(proc = self._proc_name))
        if not stop_condition(out):
            while self._time_out != None and count < self._time_out:
                try:
                    out.append(self._proc.stdout.readline())
                    logger.debug('{proc} line: {out}'.format(proc = self._proc_name,
                                                            out  = repr(out[-1])))
                except IOError as e:
                    time.sleep(0.1)
                    count = count + 1
                    continue
                if stop_condition(out):
                    break
            logger.info ('{proc} count: {time}'.format(proc = self._proc_name,
                                                       time = count))
            assert self._time_out == None or count < self._time_out
        return out

    def _init_popen(self):
        if self._proc != None:
            try:
                self._proc.kill()
            except OSError:
                pass
        process = Popen([self.path_to_bin] + list(self.params),
                                       shell=False,
                                       stdin=PIPE,
                                       stdout=PIPE,
                                       stderr=PIPE)
        chstdin, chstdout = process.stdin, process.stdout
        fl = fcntl(chstdout, F_GETFL)
        fcntl(chstdout, F_SETFL, fl | O_NONBLOCK)
        self._proc = process
        out = []
        if not self._header_completed(out):
            out = self._read_line(stop_condition = self._header_completed)
        return out

    def _header_completed(self, out_list):
        return True

    def _process_completed(self, out_list):
        return len(out_list) > 0

    def _process_output(self, out):
        return out

    def _err_handler(self, err):
        logger.debug('Error:"%s"' %err)

    def _process(self, input_text, shell = False, tries = 3):
        out, err = None, None
        if self._proc.stdin.closed:
            self._init_popen()

        if self._disposable:
            logger.info('{proc}: communicating \'{input}\''.format(proc  = self._proc_name,
                                                                   input = input_text))
            out, err = self._proc.communicate(input_text)
        else:
            err = []
            try:
                self._proc.stdin.write(input_text)
                self._proc.stdin.flush()
                logger.info('{proc}:  input: {input}'.format(proc  = self._proc_name,
                                                             input = repr(input_text)))
                out = self._read_line(stop_condition = self._process_completed)
            except (AssertionError, IOError) as e:
                if tries > 0:
                    logger.info('Another try:')
                    self._init_popen()
                    out,err  = self._process(input_text, shell = False, tries = tries-1)
                else:
                    raise e
        self._err_handler(err)
        logger.debug('{proc} out: {out}'.format(proc = self._proc_name,
                                                out  = repr(out)))
        out = self._process_output(''.join(out))
        logger.info('{proc}: finished'.format(proc = self._proc_name))
        return out, err