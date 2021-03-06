"""
Perform test automation with nox.

For further details, see https://nox.thea.codes/en/stable/#

"""

from hashlib import sha256
import os
from pathlib import Path
from shutil import rmtree
from urllib.request import urlretrieve
from zipfile import ZipFile

import nox


#: Default to reusing any pre-existing nox environments.
nox.options.reuse_existing_virtualenvs = True

#: Name of the package to test.
PACKAGE = Path("iris_ugrid").absolute()

#: Cirrus-CI environment variable hook.
PY_VER = os.environ.get("PY_VER", "3.7")

# Git commit of iris that iris-ugrid depends on.
with Path("requirements").joinpath("manual", "iris_commit.txt").open() as fi:
    IRIS_COMMIT = fi.read().strip()


def venv_cached(session, cache_info_path, env_spec_path, iris_commit):
    """
    Determine whether the nox session environment has been cached.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    cache_info_path: Path
        A Path object pointing to the expected directory that would contain
        cache info.

    env_spec_path: pathlib.Path
        A Path object pointing to the conda env spec YAML for Iris-ugrid.

    iris_commit : str
        The string for the Iris commit Iris-ugrid is dependent on.

    Returns
    -------
    bool
        Whether the session has been cached.

    """
    result = False

    cache_env_spec = cache_info_path / env_spec_path.name
    cache_iris_commit = cache_info_path / "iris-commit"
    caches_found = all(
        [file.is_file() for file in (cache_env_spec, cache_iris_commit)]
    )

    if caches_found:
        with env_spec_path.open("rb") as fi:
            expected = sha256(fi.read()).hexdigest()
        with cache_env_spec.open("r") as fi:
            actual = fi.read()
        ok_env_spec = actual == expected

        expected = iris_commit
        with cache_iris_commit.open("r") as fi:
            actual = fi.read()
        ok_iris_commit = actual == expected

        result = ok_env_spec and ok_iris_commit

    return result


def cache_venv(session, cache_info_path, env_spec_path, iris_commit):
    """
    Cache the nox session environment.

    This consists of saving a hexdigest (sha256) of the associated
    conda requirements YAML file.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    cache_info_path: pathlib.Path
        A Path object denoting the directory that cache info should be written
        to.

    env_spec_path: pathlib.Path
        A Path object pointing to the conda env spec YAML for Iris-ugrid.

    iris_commit: str
        The string for the Iris commit Iris-ugrid is dependent on.

    """
    if not cache_info_path.is_dir():
        cache_info_path.mkdir()

    with env_spec_path.open("rb") as fi:
        hexdigest = sha256(fi.read()).hexdigest()
    cache_env_spec = cache_info_path / env_spec_path.name
    with cache_env_spec.open("w+") as fo:
        fo.write(hexdigest)

    cache_iris_commit = cache_info_path / "iris-commit"
    with cache_iris_commit.open("w+") as fo:
        fo.write(iris_commit)


@nox.session
def flake8(session):
    """
    Perform flake8 linting of iris-ugrid.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    """
    # Pip install the session requirements.
    session.install("flake8")
    # Execute the flake8 linter on the package.
    session.run("flake8", str(PACKAGE))
    # Execute the flake8 linter on this file.
    session.run("flake8", __file__)


@nox.session
def black(session):
    """
    Perform black format checking of iris-ugrid.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    """
    # Pip install the session requirements.
    session.install("black==19.10b0")
    # Execute the black format checker on the package.
    session.run("black", "--check", str(PACKAGE))
    # Execute the black format checker on this file.
    session.run("black", "--check", __file__)


@nox.session(python=[PY_VER], venv_backend="conda")
def tests(session):
    """
    Perform iris-ugrid tests.

    Parameters
    ----------
    session: object
        A `nox.sessions.Session` object.

    Notes
    -----
    See
      - https://github.com/theacodes/nox/issues/346
      - https://github.com/theacodes/nox/issues/260

    """
    INSTALL_DIR = Path().cwd().absolute()
    env_spec_self = (
        INSTALL_DIR
        / "requirements"
        / "ci"
        / f"py{PY_VER.replace('.', '')}.yml"
    )

    IRIS_DIR = Path(session.virtualenv.location) / "iris"

    cache_info_path = Path(session.virtualenv.location) / "nox_cache_info"
    if not venv_cached(session, cache_info_path, env_spec_self, IRIS_COMMIT):

        def conda_env_update(env_spec_path):
            # Back-door approach to force nox to use "conda env update".
            command = (
                f"conda env update --prefix={session.virtualenv.location} "
                f"--file={env_spec_path}"
            )
            command = command.split(" ")
            session._run(*command, silent=True, external="error")

        # Download Iris.
        github_archive_url = (
            f"https://github.com/SciTools/iris/archive/{IRIS_COMMIT}.zip"
        )
        iris_zip = Path(urlretrieve(github_archive_url, "iris.zip")[0])
        with ZipFile(iris_zip, "r") as zip_open:
            zip_open.extractall()
        if IRIS_DIR.is_dir():
            rmtree(IRIS_DIR)
        Path(f"iris-{IRIS_COMMIT}").rename(IRIS_DIR)
        iris_zip.unlink()

        # Install Iris dependencies.
        env_spec_iris = (
            IRIS_DIR
            / "requirements"
            / "ci"
            / f"py{PY_VER.replace('.', '')}.yml"
        )
        conda_env_update(env_spec_iris)

        # Configure Iris.
        site_cfg_content = [
            "[Resources]",
            f"test_data_dir = {os.environ['IRIS_TEST_DATA_DIR']}/test_data",
            f"doc_dir = {IRIS_DIR / 'docs' / 'iris'}",
            "[System]",
            f"udunits2_path = {session.virtualenv.location}/lib/libudunits2.so",
        ]
        site_cfg_path = IRIS_DIR / "lib" / "iris" / "etc" / "site.cfg"
        with site_cfg_path.open("w+") as site_cfg:
            site_cfg.writelines(line + "\n" for line in site_cfg_content)

        # Install Iris.
        os.chdir(IRIS_DIR)
        session.run(*"python setup.py install".split(" "), silent=True)

        #######################################################################

        # Install dependencies.
        conda_env_update(env_spec_self)

        cache_venv(session, cache_info_path, env_spec_self, IRIS_COMMIT)

    session.run("pytest", "-v", str(PACKAGE))
