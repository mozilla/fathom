from click import style
from contextlib import contextmanager
from datetime import timedelta
from functools import partial
from json import dump, JSONDecodeError, load
import hashlib
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from importlib.resources import open_binary
import os
from os import devnull, kill, makedirs
from os.path import expanduser, expandvars
from pathlib import Path
import platform
from shutil import copyfileobj, move, rmtree, which
import signal
import socket
import subprocess
from subprocess import CalledProcessError
from sys import exc_info
from tempfile import TemporaryDirectory
from threading import Thread
from time import sleep, time
from zipfile import ZipFile, ZIP_DEFLATED

from click import ClickException, progressbar
from filelock import FileLock
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from .utils import read_chunks, samples_from_dir


class GracefulError(ClickException):
    """An error that allows for a graceful shutdown"""


class UngracefulError(ClickException):
    """An error that does not allow for a graceful shutdown"""


class Timeout(Exception):
    """``retry()`` finished all its tries without succeeding."""


def make_or_find_vectors(ruleset, trainee, sample_set, sample_cache, show_browser, kind_of_set, delay, tabs):
    """Return the contents of a vector file, building it first if necessary.

    If passed a vector file for ``sample_set``, we return it verbatim. If
    passed a folder rather than a vector file, we use the cache if it's fresh.
    Otherwise, we build the vectors, based on the given ``ruleset`` and
    ``trainee`` ID, and then cache them at Path ``sample_cache``.

    :arg sample_cache: A Path to possibly-pre-existing vector files or None to
        use the default location

    """
    if not sample_set.is_dir():
        final_path = sample_set  # It's just a vector file.
    else:
        if not sample_cache:
            sample_cache = ruleset.parent / 'vectors' / f'{kind_of_set}_{trainee}.json'
        updated_hashes = out_of_date(sample_cache, ruleset, sample_set)
        if updated_hashes:
            # Make a vectors file, replacing it if already present:
            vectorize(ruleset, trainee, sample_set, sample_cache, show_browser, kind_of_set, delay, tabs)
            # Stick the new hashes in it:
            with sample_cache.open(encoding='utf-8') as file:
                json = load(file)
            json['header'].update(updated_hashes)
            with sample_cache.open('w', encoding='utf-8') as file:
                dump(json, file, separators=(',', ':'))
            return json
        final_path = sample_cache
    with open(final_path, encoding='utf-8') as file:
        json = load(file)
        if json['header']['version'] > 2:
            raise GracefulError(f'The vector file {final_path} has a newer format than these tools can handle. Please run `pip install -U fathom-web` to upgrade your tools.')
        return json


def out_of_date(sample_cache, ruleset, sample_set):
    """Determine whether the sample cache is out of date compared to the
    ruleset and sample set.

    If it is, return a dict of hashes we can add to the new sample cache. If
    not, return None.

    We use hashes to determine out-of-dateness because git sets the mod dates
    to now whenever it changes branches. This way, you can check out somebody
    else's branch from across the internet and still not have to revectorize,
    as long as they checked their vectors in. And it takes only .2s for 250
    samples on my 2020 SSD laptop.

    :arg sample_cache: A Path to possibly-pre-existing vector file
    :arg ruleset: A Path to a rulesets.js file. Can be None if ``sample_set``
        is a file.
    :arg sample_set: A Path to a folder full of samples

    """
    if sample_cache.exists():
        with sample_cache.open(encoding='utf-8') as file:
            try:
                cache_header = load(file)['header']
            except JSONDecodeError:
                cache_header = {}
    else:
        cache_header = {}
    ruleset_hash = hash_path(ruleset)
    page_hashes = {}
    with progressbar(samples_from_dir(sample_set), label='Checking for changes') as bar:
        for sample in bar:
            # Hash each file separately. Otherwise, we can't tell the
            # difference between file 1 that says "ab" and file 2 that says "c"
            # vs. file 1 that says "a" and file 2 "bc". Plus, if we store the
            # hashes along with their sample-dir-relative paths, we can someday
            # make this revectorize only the new samples if some are
            # added—and delete the ones deleted.
            page_hashes[str(sample.relative_to(sample_set))] = hash_path(sample)
    if (ruleset_hash != cache_header.get('rulesetHash') or
        page_hashes != cache_header.get('pageHashes')):
        return {'pageHashes': page_hashes,
                'rulesetHash': ruleset_hash}


def vectorize(ruleset_path, trainee_id, samples_directory, output_path, show_browser, kind_of_set, delay, tabs):
    """Create feature vectors for a directory of training samples.

    We unpack an embedded version of FathomFox, fetch its npm dependencies,
    copy the ruleset into it, bundle it up, run it in a copy of Firefox, and
    drive the Vectorizer with Selenium.

    :arg ruleset_path: Path to the rulesets.js file
    :arg trainee_id: The ID of the desired Fathom trainee in rulesets.js
    :arg samples_directory: Path to the directory containing the sample pages
    :arg output_path: Where to save the resulting vector file
    :arg show_browser: Whether to show Firefox vs. running it in headless mode

    Required for this to work are...
      * node (and npm, which ships with it)
      * Firefox

    The use of os.kill() when shutting down during vectorization is unfortunate
    but unavoidable due to a bug in geckodriver. We are working on fixing this.
    Repeatedly stopping this program during vectorization may cause problems
    with other currently running Firefox processes.

    """
    with ruleset_path.open('rb') as ruleset_file:
        with fathom_fox_addon(ruleset_file) as addon_and_geckodriver:
            addon_path, geckodriver_path = addon_and_geckodriver
            with running_firefox(addon_path,
                                 show_browser,
                                 geckodriver_path) as firefox:  # TODO: I can probably run FF once and share it across the training and validation vectorizations.
                with serving(samples_directory) as port:
                    sample_filenames = [str(sample.relative_to(samples_directory))
                                        for sample in samples_from_dir(samples_directory)]
                    run_vectorizer(firefox, trainee_id, sample_filenames, output_path, kind_of_set, port, delay, tabs)


@contextmanager
def fathom_fox_addon(ruleset_file):
    """Return a Path to a FathomFox extension containing your ruleset and
    another to the geckodriver executable."""
    print('Building FathomFox with your ruleset...', end='', flush=True)
    with TemporaryDirectory() as temp:
        temp_dir = Path(temp)

        with locked_cached_fathom() as source:
            fathom_fox = source / 'fathom_fox'

            # Copy in your ruleset:
            with (fathom_fox / 'src' / 'rulesets.js').open('wb') as new_ruleset_file:
                copyfileobj(ruleset_file, new_ruleset_file)

            # Build FathomFox:
            run(str(add_cmd_if_windows((fathom_fox / 'node_modules' / '.bin' / 'rollup').resolve())),
                '-c',
                cwd=fathom_fox,
                desc='Compiling ruleset')

            # Smoosh FathomFox down into an XPI. The Firefox webdriver requires
            # we load custom addons using .xpi files.
            addon_path = temp_dir / 'fathom-fox.xpi'
            zip_dir(fathom_fox / 'addon', addon_path)

        print('done.')

        # It should be okay to reference geckodriver outside the
        # locked_cached_fathom() lock, since that part of the cache is
        # immutable:
        yield addon_path, add_cmd_if_windows(fathom_fox / 'node_modules' / '.bin' / 'geckodriver')


def add_cmd_if_windows(binary_path):
    """Add the .cmd suffix to a pathlib.Path if running on Windows."""
    if os.name == 'nt':
        return binary_path.with_suffix('.cmd')
    else:
        return binary_path


def remove_old_fathom_caches(source_cache, current_hash):
    """Delete Fathom caches that haven't been used for awhile.

    They're 150MB, so this is good form.

    """
    for lock in source_cache.glob('*.lock'):
        if lock.stem != current_hash:
            # Don't delete the cache entry we're about to use.
            if time() - lock.stat().st_mtime > timedelta(weeks=1).total_seconds():
                # This lockfile is over a week old. Locking it touches its mod
                # date.
                with FileLock(lock, timeout=1):
                    # We accept an unlikely race here wherein a parallel
                    # vectorization run starts just before we acquire the lock,
                    # having given up the lock in order to allow other parallel
                    # runs to go on. However, it still counts on being able to
                    # use the copy of geckodriver within the cache, which we
                    # are about to delete. The parallel run would also have to
                    # be from an old version of the Fathom CLI that was at
                    # least a week old. I will trade this for simplicity and
                    # more performant parallel runs.
                    retry(lambda: rmtree(lock.with_suffix('')), retry_on=OSError)
                    # The retrying is to work around a behavior on the Mac
                    # wherein deleting fails with "OSError: [Errno 66]
                    # Directory not empty: 'node_modules'" sometimes.
                    lock.unlink()


@contextmanager
def locked_cached_fathom():
    """Return a Path to a directory containing a copy of Fathom and FathomFox's
    source, and reserve exclusive access to it while the context manager is
    open.

    We guarantee that the copy of FathomFox we provide will be brought to a
    runnable state by copying a ruleset.js in and running rollup.

    Caching this saves 15 seconds if your npm packages are already cached, more
    otherwise. For simplicity, we cache only one copy of each version of
    Fathom, as determined by a hash of fathom.zip. But the lock is held only
    while we run rollup and zip up the result, so parallel invocations of the
    vectorizer still basically work.

    """
    source_cache = cache_directory() / 'source'
    makedirs(source_cache, exist_ok=True)
    hash = hash_fathom()
    remove_old_fathom_caches(source_cache, hash)

    with FileLock(source_cache / f'{hash}.lock', timeout=30):
        # Ownership of 123abc.lock means we have sole dominion over the 123abc
        # folder next to it.
        hash_dir = source_cache / hash
        finished_flag = hash_dir / 'finished_flag'
        fathom_fox = hash_dir / 'fathom_fox'
        if not finished_flag.exists():
            # Remove any half-built failures lying around. Sometimes
            # removing node_modules fails temporarily with an OSError: dir
            # not empty.
            def remove_hash_dir_if_exists():
                try:
                    rmtree(hash_dir)
                except FileNotFoundError:
                    pass
            retry(remove_hash_dir_if_exists, retry_on=OSError)
            hash_dir.mkdir()

            # Extract a fresh copy of FathomFox and Fathom (which it needs to build
            # your ruleset) from resources stored in this Python package. By
            # including it directly from the source tree, we save downloading it
            # afterward (and figuring out where to put it), and FathomFox can
            # continue to refer to Fathom as file:../fathom for easy development.
            with fathom_zip() as zip_file:
                zip = ZipFile(zip_file)
                zip.extractall(hash_dir)

            def run_in_fathom_fox(*args, desc):
                """Run a command using the FathomFox dir as the working dir."""
                run(*args, cwd=fathom_fox, desc=desc)

            # Install yarn, because it installs FathomFox's dependencies in 15s rather
            # than 30s. And once installed once, yarn itself takes only 1.5s to install
            # again. Also, it has security advantages. Though this install itself isn't
            # hashed, so we're just trusting NPM. Additionally, we have to call
            # shutils.which() on npm because it is a .cmd file on Windows, while node
            # (down below) is an executable.
            run_in_fathom_fox(which('npm'), 'install', 'yarn@1.22.4',
                              desc='Installing yarn')

            # Figure out how to invoke yarn:
            if os.name == 'nt':
                yarn_binary = str((fathom_fox / 'node_modules' / 'yarn' / 'bin' / 'yarn.js').resolve())
            else:
                yarn_binary = str((fathom_fox / 'node_modules' / '.bin' / 'yarn').resolve())

            # Pull in npm dependencies:
            run_in_fathom_fox('node', yarn_binary, 'install',
                              desc='Installing dependencies with yarn')
            # FWIW, I find the most common failure on `yarn install` is a server-side
            # 500 error while downloading geckodriver, which comes from GitHub rather
            # than npm. The output needed to distinguish this is not captured by
            # subprocess.run(capture_output=True).

            # Drop a little turd to declare that we finished building this
            # cached copy entirely:
            finished_flag.touch()

        yield hash_dir

        # Clean up project-specific build artifacts, just for peace of mind:
        unlink_if_exists(fathom_fox / 'src' / 'rulesets.js')
        unlink_if_exists(fathom_fox / 'addon' / 'rulesets.js')


def zip_dir(dir, archive_path):
    """Compress an entire dir, and write it to ``archive_path``."""
    with ZipFile(archive_path, 'w', compression=ZIP_DEFLATED) as archive:
        for file in dir.rglob('*'):
            archive.write(file, file.relative_to(dir))


class SilentRequestHandler(SimpleHTTPRequestHandler):
    """A request handler that will not output the log for each request to the
    terminal

    Not only is this distracting but it also seems to prevent requests from
    being served when using the ThreadingHTTPServer.

    """
    def log_message(self, format, *args):
        pass


class SilentHTTPServer(ThreadingHTTPServer):
    swallowable_error_count = 0

    def handle_error(self, request, client_address):
        """Silence and tally some anticipated errors.

        Things like BrokenPipeErrors can happen, probably when we take too long
        to serve a request (like an unextracted 40MB HTML file). Meanwhile
        FathomFox's 5-second default delay finishes and it begins trying to
        vectorize, after which it slams the tab, aborting the transfer.

        """
        if issubclass(exc_info()[0], BrokenPipeError):
            self.swallowable_error_count += 1
        else:
            # Print it so we can evaluate whether to suppress it in a future
            # version:
            super().handle_error(request, client_address)


def http_server(samples_directory):
    """Return an HTTP server on an unused port."""
    request_handler = partial(SilentRequestHandler, directory=samples_directory)

    START_PORT = 8000
    END_PORT = 8100
    for port in range(START_PORT, END_PORT):
        try:
            server = SilentHTTPServer(('localhost', port), request_handler)
        except socket.error:
            pass
        else:
            return server
    raise GracefulError(f"Couldn't find an unused port between {START_PORT} and {END_PORT} for the HTTP server.")


@contextmanager
def serving(samples_directory):
    """Start a local HTTP server for the samples, and yield its port."""
    print('Starting HTTP server...', end='', flush=True)
    server = http_server(samples_directory)
    Thread(target=server.serve_forever).start()
    print('done.')
    # Without this try/finally, the server thread will hang forever if the main
    # thread raises an exception. The program will require 2 control-Cs to exit.
    try:
        yield server.server_port
    finally:
        server.shutdown()
        server.server_close()  # joins threads in ThreadingHTTPServer
    if server.swallowable_error_count:
        print(style(f'{server.swallowable_error_count} error{"" if server.swallowable_error_count == 1 else "s"} while serving samples. Increase vectorization --delay or use `fathom extract` to make smaller HTML files.', fg='red'))


@contextmanager
def running_firefox(fathom_fox, show_browser, geckodriver_path):
    """Configure and return a running Firefox to run the vectorizer with.

    Sets headless mode, sets the download directory to a temp directory, turns
    off page caching, and installs FathomFox. Tries its best to quit Firefox
    afterward.

    """
    print('Running Firefox...', end='', flush=True)

    with TemporaryDirectory() as download_dir:
        options = webdriver.FirefoxOptions()

        if not show_browser:
            options.add_argument('-headless')

        options.set_preference('browser.download.folderList', 2)
        options.set_preference('browser.download.dir', download_dir)
        options.set_preference('browser.cache.disk.enable', False)
        options.set_preference('browser.cache.memory.enable', False)
        options.set_preference('browser.cache.offline.enable', False)
        options.set_preference('devtools.chrome.enabled', True)

        service = webdriver.firefox.service.Service(
            executable_path=str(geckodriver_path.resolve()),
            log_path=devnull,
        )
        firefox = webdriver.Firefox(
            service=service,
            options=options,
        )

        firefox.install_addon(str(fathom_fox), temporary=True)
        firefox_pid = firefox.capabilities['moz:processID']
        geckodriver_pid = firefox.service.process.pid
        print('done.')

        # There is a graceful shutdown path and an ungraceful shutdown path. If
        # the vectorizer has started running, we use the ungraceful shutdown
        # path. This is because Firefox becomes unresponsive to the call to
        # `quit()`.
        graceful_shutdown = False
        try:
            yield firefox
            graceful_shutdown = True
        except GracefulError:
            graceful_shutdown = True
            raise  # happens AFTER the finally
        finally:
            if graceful_shutdown:
                firefox.quit()
            else:
                # This is the only way I could get killing the program with
                # ctrl+c to work properly.
                signal_for_killing = (signal.CTRL_C_EVENT if os.name == 'nt'
                                      else signal.SIGTERM)
                try:
                    # https://bugzilla.mozilla.org/show_bug.cgi?id=1430064
                    kill(firefox_pid, signal_for_killing)
                except (SystemError, ProcessLookupError):
                    pass
                kill(geckodriver_pid, signal_for_killing)


# A substring the Vectorizer spits out when something goes wrong:
FAILURE_SIGNIFIER = 'failed:'


def run_vectorizer(firefox, trainee_id, sample_filenames, output_path, kind_of_set, port, delay, tabs):
    """Set up the vectorizer and run it, creating the vector file.

    Move the vector file to ``output_path``, replacing any file already there.

    We navigate to the vectorizer page of FathomFox, paste the sample filenames
    into the text area, and hit the Vectorize button. We monitor the status
    text area for errors and to see how many samples have been vectorized, so
    we know when the Vectorizer has stopped running.

    """
    def put_into_field(field_id, string):
        """Put a given string into the text field of a given ID."""
        field = firefox.find_element(By.ID, field_id)
        field.clear()
        field.send_keys(string)

    print('Configuring Vectorizer...', end='', flush=True)
    # Navigate to the vectorizer page
    fathom_fox_uuid = get_fathom_fox_uuid(firefox)
    firefox.get(f'moz-extension://{fathom_fox_uuid}/pages/vector.html')

    ruleset_dropdown_selector = Select(firefox.find_element(By.ID, 'trainee'))
    try:
        ruleset_dropdown_selector.select_by_visible_text(trainee_id)
    except NoSuchElementException:
        raise UngracefulError(f"Couldn't find trainee ID \"{trainee_id}\" in your rulesets.")

    put_into_field('pages', '\n'.join(sample_filenames))
    put_into_field('baseUrl', f'http://localhost:{port}/')
    put_into_field('wait', str(delay))
    put_into_field('maxTabs', str(tabs))

    number_of_samples = len(sample_filenames)
    status_box = firefox.find_element(By.ID, 'status')
    vectorize_button = firefox.find_element(By.ID, 'freeze')
    completed_samples = 0
    print('done.')

    with progressbar(length=number_of_samples, label=f'Vectorizing {kind_of_set} set') as bar:
        vectorize_button.click()
        while completed_samples < number_of_samples:
            try:
                status_box_text = status_box.text
            except NoSuchWindowException:
                raise UngracefulError('Vectorization aborted: Firefox window closed during vectorization')
            try:
                failure_detected = FAILURE_SIGNIFIER in status_box_text
            except TypeError:
                raise UngracefulError('Vectorization aborted: Firefox window closed during vectorization')
            if failure_detected:
                error = extract_error_from(status_box_text)
                raise UngracefulError(f'Vectorization failed with error:\n{error}')
            now_completed_samples = len([line for line in status_box_text.splitlines() if line.endswith(': vectorized')])
            bar.update(now_completed_samples - completed_samples)
            completed_samples = now_completed_samples
            sleep(.25)

    download_dir = Path(firefox.options.preferences['browser.download.dir'])
    new_file = wait_for_vectors_in(download_dir)
    unlink_if_exists(output_path)  # move() won't overwrite a file on Windows.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    move(str(new_file.resolve()), str(output_path.resolve()))


def get_fathom_fox_uuid(firefox):
    """Try to get the internal UUID for FathomFox from `prefs.js`.

    We use a loop to try multiple times because the `prefs.js` file needs a
    little time to update before the fathom addon information appears. Five
    seconds seems adequate since one second has always worked for me (Daniel).

    """
    def get_uuid():
        prefs = (Path(firefox.capabilities.get('moz:profile')) / 'prefs.js').read_text().split(';')
        uuids = next((line for line in prefs if 'extensions.webextensions.uuids' in line)).split(',')
        fathom_fox_uuid = next((line for line in uuids if '{954efd86-8f62-49e7-8a65-80016051e382}' in line)).split('\\"')[3]
        return fathom_fox_uuid

    try:
        return retry(get_uuid)
    except Timeout:
        raise GracefulError('Could not find UUID for FathomFox. No entry in the prefs.js file.')


def extract_error_from(status_text):
    """Look for errors in the vectorizer's status text.

    If there is an error, raise an exception, causing an ungraceful shutdown.

    """
    lines = status_text.splitlines()
    for line in lines:
        if FAILURE_SIGNIFIER in line:
            return line
    raise UngracefulError(f'There was a vectorizer error, but we could not find it in {status_text}')


def wait_for_vectors_in(download_dir):
    """Wait for a vector file to appear in the downloads directory, and return
    its Path.

    The file system needs a little little time to update before the file
    appears. Five seconds seems adequate since one second has always worked for
    me (Daniel).

    """
    try:
        return retry(lambda: next(download_dir.glob('vectors*.json')))
    except Timeout:
        contents = ', '.join(item.name for item in download_dir.iterdir())
        raise GracefulError(f'Could not find vectors*.json in downloads folder. Present items were: {contents}.')


def retry(function, max_tries=5, retry_on=Exception):
    """Try to execute a function some number of times before raising Timeout.

    :arg function: A function that likely has some time dependency and you want
        to try executing it multiple times to wait for the time dependency to
        resolve
    :arg max_tries: The number of times to try the function before raising
        Timeout
    :arg retry_on: An exception or tuple of exceptions that should trigger a
        retry

    """
    for _ in range(max_tries):
        try:
            return function()
        except retry_on:
            sleep(1)
    else:
        raise Timeout()


def hash_path(path):
    """Return the hex digest of the SHA256 hash of a file."""
    with path.open('rb') as file:
        return hash_file(file)


def hash_fathom():
    """Return the first 8 chars of the hash of my embedded copy of the Fathom
    source."""
    with fathom_zip() as zip_file:
        return hash_file(zip_file)[:8]


def hash_file(file):
    hash = hashlib.new('sha256')
    for chunk in read_chunks(file):
        hash.update(chunk)
    return hash.hexdigest()


@contextmanager
def fathom_zip():
    """Return a file-like object representing my embedded, zipped copy of
    Fathom and FathomFox."""
    with open_binary('fathom_web', 'fathom.zip') as zip_file:
        yield zip_file


def cache_directory():
    """Return the directory where we can cache things on this OS."""
    if os.name == 'nt':
        dir = expandvars(r'%LOCALAPPDATA%\Fathom\Cache')
    elif platform.system() == 'Darwin':
        dir = expanduser('~/Library/Caches/Fathom')
    else:
        dir = expanduser('~/.fathom/cache')
    return Path(dir)


def unlink_if_exists(path):
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def run(*args, cwd, desc):
    """Run a command using the given working dir, and raise a nice error.

    If it fails, raise a GracefulError that includes the command
    invocation as well as captured stdout and stderr to give you a chance at
    diagnosing the problem.

    """
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, check=True)
    except CalledProcessError as e:
        raise GracefulError('\n'.join([f'{desc} failed:',
                                       ' '.join(str(arg) for arg in args),
                                       e.stdout.decode(errors='ignore'),
                                       e.stderr.decode(errors='ignore')]))
    except FileNotFoundError as e:
        # Happens when the command isn't found.
        raise GracefulError(f'{desc} failed: {e.filename} not found.')
