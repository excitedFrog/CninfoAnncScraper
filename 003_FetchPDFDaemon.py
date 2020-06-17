# Python 3.6.1

import os
import sys
import time
import atexit
import signal
import subprocess

from params import TMP_DIR, ROOT_DIR

CURRENT_DIR = os.getcwd()
LOG_FILE = os.path.join(CURRENT_DIR, 'daemon.log')


class Daemon(object):
    def __init__(self, daemon_pidfile=os.path.join(TMP_DIR, 'daemon.pid'),
                 stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        super().__init__()
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.daemon_pidfile = daemon_pidfile

    def daemonize(self):
        if os.path.exists(self.daemon_pidfile):
            print('Daemon already running.')
        # First fork (detach from parent)
        try:
            if os.fork() > 0:
                raise SystemExit(0)
        except OSError as error:
            raise RuntimeError('fork #1 failed: {0} ({1})'.format(error.errno, error.strerror))
        os.chdir(ROOT_DIR)
        os.setsid()
        os.umask(0o22)
        # Second fork (relinquish session leadership)
        try:
            if os.fork() > 0:
                raise SystemExit(0)
        except OSError as error:
            raise RuntimeError('fork #2 failed: {0} ({1})\n'.format(error.errno, error.strerror))
        # Flush I/O buffers
        sys.stdout.flush()
        sys.stderr.flush()
        # Replace file descriptors for stdin, stdout, and stderr
        with open(self.stdin, 'rb', 0) as f:
            os.dup2(f.fileno(), sys.stdin.fileno())
        with open(self.stdout, 'ab', 0) as f:
            os.dup2(f.fileno(), sys.stdout.fileno())
        with open(self.stderr, 'ab', 0) as f:
            os.dup2(f.fileno(), sys.stderr.fileno())
        # Write the PID file
        with open(self.daemon_pidfile, 'w') as f:
            print(os.getpid(), file=f)
        # Arrange to have the PID file removed on exit/signal
        atexit.register(lambda: os.remove(self.daemon_pidfile))
        signal.signal(signal.SIGTERM, self.__sigterm_handler)

    # Signal handler for termination (required)
    @staticmethod
    def __sigterm_handler(signo, frame):
        raise SystemExit(1)

    def start(self):
        try:
            self.daemonize()
        except RuntimeError as error:
            print(error, file=sys.stderr)
            raise SystemExit(1)
        self.run()

    def stop(self):
        try:
            if os.path.exists(self.daemon_pidfile):
                with open(self.daemon_pidfile) as f:
                    os.kill(int(f.read()), signal.SIGTERM)
            else:
                print('Not running.', file=sys.stderr)
                raise SystemExit(1)
        except OSError as error:
            if 'No such process' in str(error) and os.path.exists(self.daemon_pidfile):
                os.remove(self.daemon_pidfile)

    def restart(self):
        self.stop()
        self.start()

    def run(self):
        pass


class LDaemon(Daemon):
    def __init__(self, daemon_pidfile=os.path.join(TMP_DIR, 'daemon.pid'),
                 child_pidfile=os.path.join(TMP_DIR, 'child.pid'),
                 stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        super().__init__(daemon_pidfile=daemon_pidfile, stdin=stdin, stdout=stdout, stderr=stderr)
        self.child_pidfile = child_pidfile
        self.process = None

    def log_child_pid(self):
        with open(self.child_pidfile, 'w') as f:
            print(self.process.pid, file=f)

    def run(self):
        sys.stdout.write('Daemon started with pid {}\n'.format(os.getpid()))
        sys.stdout.flush()
        self.process = subprocess.Popen(['python', os.path.join(CURRENT_DIR, '002_FetchPDF.py')])
        sys.stdout.write('Child spawned! {}\n'.format(self.process.pid))
        sys.stdout.flush()
        self.log_child_pid()
        while True:
            time.sleep(60)
            sys.stdout.write('Daemon Alive! {}\n'.format(time.ctime()))
            sys.stdout.flush()
            if self.process.poll() is not None:
                sys.stdout.write('Child died!\n')
                sys.stdout.flush()
                self.process = subprocess.Popen(['python', os.path.join(CURRENT_DIR, '002_FetchPDF.py')])
                sys.stdout.write('Child respawned! {}\n'.format(self.process.pid))
                sys.stdout.flush()
                self.log_child_pid()

    def start(self):
        try:
            self.daemonize()
        except RuntimeError as error:
            print(error, file=sys.stderr)
            raise SystemExit(1)
        self.run()

    def stop(self):
        super().stop()
        with open(self.child_pidfile, 'r') as f:
            child_pid = int(f.read())
        os.kill(child_pid, signal.SIGKILL)
        os.remove(self.child_pidfile)


if __name__ == '__main__':
    daemon = LDaemon(stdout=LOG_FILE, stderr=LOG_FILE)
    daemon.start()
