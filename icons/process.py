#!/usr/bin/env python3
"""
The script parses icon definitions from YAML file, gets
them from the specified resources, and optimizes them
for web use.
"""

from ruamel.yaml import YAML
import requests

from dataclasses import dataclass
from functools import singledispatchmethod
import argparse
import logging
import pathlib as pth

DEFAULTS = {'filename': 'icons.yml', 'builddir': 'build/', 'verbose': False}

RESOLVERS = dict()

# Initialize YAML as type-safe. Default was 'rt' (round-trip)
yaml = YAML(typ='safe')
log = logging.getLogger(__name__)


@dataclass
class IconEntry:
    icon_name: str
    resource: str
    icon_id: str

    @classmethod
    def from_data(cls, icon_name, data):
        """Creates entry from YAML parsing result (as icon_name:data)"""
        resource, *icon_id = data.split(':')
        icon_id = ':'.join(icon_id)

        # Use icon_id is icon_name when not explicitly provided
        icon_id = icon_id or icon_name

        return cls(icon_name=icon_name, resource=resource, icon_id=icon_id)


class Downloader:
    HEADERS = {
        # Latest Chrome on Linux
        'User-Agent': (r'Mozilla/5.0 (X11; Linux x86_64) '
                       r'AppleWebKit/537.36 (KHTML, like Gecko) '
                       r'Chrome/128.0.0.0 Safari/537.36'),
    }

    def __init__(self, *, session=None):
        ses = requests.Session() if session is None else session
        ses.headers.update(self.HEADERS)

        self.session = ses


class ReshotDownloader(Downloader):
    ICON_JSONURL_FMT = r'https://www.reshot.com/free-svg-icons/download/{ident}/?operation=download'

    def get_url(self, icon_id):
        ident = icon_id.split('-')[-1]
        request_url = self.ICON_JSONURL_FMT.format(ident=ident)
        with self.session.get(request_url) as response:
            json = response.json()

        assert json['result'] == 'success' and json['humane_id'] == ident
        url = json['download_asset_url']

        log.debug('Found URL for asset %s : %s -> %s', type(self).__name__, icon_id, url)
        return url

    def download(self, icon_id, outfile):
        url = self.get_url(icon_id)
        ext = '.' + url.split('.')[-1]

        outfile = pth.Path(outfile)
        if outfile.suffix != ext:
            outfile = outfile.with_suffix(ext)

        total = 0
        with self.session.get(url) as response, open(outfile, 'wb') as file:
            for chunk in response.iter_content():
                total += file.write(chunk)

        log.debug('Written %s bytes to %s', total, outfile)
        return total, outfile


RESOLVERS['reshot'] = ReshotDownloader


def process(filename, builddir, verbose=True, *, log=log):
    icons = yaml.load(filename)
    log.debug('Loaded icons\n\t%s', icons)

    entries = [IconEntry.from_data(icon_name=icon_name, data=data) for icon_name, data in icons.items()]

    log.debug('Got entries\n\t%s', entries)

    resources = {e.resource for e in entries}
    log.debug('Found resources: %s', resources)

    groups = {res: tuple([e for e in entries if e.resource == res]) for res in resources}
    log.debug('Built groups:\n\t%s', groups)

    # Make downloader
    resolvers = {group: RESOLVERS[group] for group in groups}

    # Make build directory if needed
    bdir = pth.Path(builddir)
    bdir.mkdir(exist_ok=True)

    # Start downloading
    for group, cls in resolvers.items():
        resolver = cls()  # instantinate resolver

        log.info('Resource "%s":', group)
        for item in groups[group]:
            log.debug('\tResolving item %s', item)
            icon_id = item.icon_id
            outfile = bdir.joinpath(item.icon_name)
            total, out = resolver.download(icon_id=icon_id, outfile=outfile)

            log.info('\t[ok] %s\t(%s bytes)', out, total)


def parse_args(args):
    prog, *args = args
    p = argparse.ArgumentParser(prog=prog, description=__doc__)

    p.add_argument('-f',
                   '--def-file',
                   help='Input file containing icon definitions in YAML format',
                   default=DEFAULTS['filename'],
                   dest='filename',
                   type=pth.Path)

    p.add_argument('-o',
                   '--out-dir',
                   help='Output directory (aka build directory)',
                   default=DEFAULTS['builddir'],
                   dest='builddir',
                   type=pth.Path)

    p.add_argument('-v', '--verbose', default=DEFAULTS['verbose'], action='store_true')

    namespace = p.parse_args(args)
    return vars(namespace)  # make dict out of it


if __name__ == '__main__':
    import sys
    args = parse_args(sys.argv)

    log_level = logging.DEBUG if args['verbose'] else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    log.debug(f'Parsed args:\n\t{args}')

    process(**args)
