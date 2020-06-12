from functools import lru_cache, update_wrapper


# Create a class that is a decorator used for caching the seaice filesystem
class SeaiceFsCache(object):
    def __init__(self, fn):
        self.func = fn
        update_wrapper(self, fn)

    # Default uses lru_cache
    @lru_cache(maxsize=4)
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def cache_clear(self):
        """Method for calling cache_clear() on lru_cache."""
        self.__call__.cache_clear()


def define_seaice_fs_cache(func):
    """Function used to set a decorator that wraps calls to
    locator._find_all_nasateam_ice_files

    The wrapped function must take a function `func` as it's first argument, and
    pass all other *args and **kwargs down to `func`. The return value from
    `func` must be returned. It is up to the wrapped function to implement
    whatever caching mechanism is desired.
    """
    def bound_func(self, *args, **kwargs):
        return func(self.func, *args, **kwargs)

    # Remove the cache_clear method. lru_cache is not being used.
    if hasattr(SeaiceFsCache, 'cache_clear'):
        del SeaiceFsCache.cache_clear

    setattr(SeaiceFsCache, '__call__', bound_func)
