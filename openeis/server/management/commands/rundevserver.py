from pip.exceptions import DistributionNotFound, BestVersionAlreadyInstalled
from pip.index import PackageFinder
from pip.req import InstallRequirement
# PipSession will be needed when SSL is used
# See pip.basecommand.Command._build_session for adding certificates to
# the verification chain. The resulting session object must be passed in
# the PackageFinder constructor using the session argument.
#from pip.download import PipSession
from pip.util import get_installed_distributions
from pip.log import logger
import sys

from django.core import management

runserver = __import__(management.get_commands()['runserver'] +
                       '.management.commands.runserver', fromlist=['Command'])


class Command(runserver.Command):
    def handle(self, *args, **kwargs):
        main()
        return super().handle(*args, **kwargs)


def get_latest_version(name, index_urls=(), find_links=(), prereleases=True):
    installed_packages = {d.key: d for d in get_installed_distributions()}
    try:
        dist = installed_packages[name]
    except KeyError:
        logger.error('Requirement {} is not installed'.format(name))
        return
    req = InstallRequirement.from_line(dist.key, None, prereleases=prereleases)
    finder = PackageFinder(find_links=find_links, index_urls=index_urls,
                           allow_all_prereleases=prereleases)
    try:
        link = finder.find_requirement(req, True)
    except DistributionNotFound:
        return
    except BestVersionAlreadyInstalled:
        remote_version = req.installed_version
    else:
        remote_version = finder._link_package_versions(link, req.name)[0]
    raw_version = remote_version[2]
    parsed_version = remote_version[0]
    return dist, raw_version, parsed_version


def check_version(name, index_urls=(), find_links=(), prereleases=True):
    version = get_latest_version(name,
        index_urls=index_urls, find_links=find_links, prereleases=prereleases)
    if version is None:
        return 1
    dist, raw_version, parsed_version = version
    if parsed_version > dist.parsed_version:
        logger.error('An updated version of {} is available.'.format(name))
        logger.warn('{} (Current: {} Latest: {})'.format(
                dist.project_name, dist.version, raw_version))
        return -1
    return 0


def main():
    logger.add_consumers((logger.NOTIFY, sys.stdout))
    return check_version('openeis-ui',
            find_links=['http://openeis-dev.pnl.gov/dist/openeis-ui'])


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
