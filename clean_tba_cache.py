import logging
import sys

import tba_cache

def main(argv):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    with tba_cache.TBACache() as tba:
        cache = tba.cache

        dirty = False
        to_delete = []
        for k, v in cache.items():
            if k.endswith('/teams/simple'):
                logging.info("deleting %s", k)
                to_delete.append(k)
        for k in to_delete:
            dirty = True
            del cache[k]
        tba.cache_is_dirty = dirty


if __name__ == '__main__':
    main(sys.argv[1:])

