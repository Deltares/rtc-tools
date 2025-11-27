def cached(f):
    def wrapper(self, ensemble_member=None):
        def call():
            if ensemble_member is not None:
                return f(self, ensemble_member)
            else:
                return f(self)

        # Add a check so that caching is applied to the 'toplevel'
        # method implementation in the class hierarchy only.
        call_in_progress = "__" + f.__name__ + "_in_progress"
        if hasattr(self, call_in_progress):
            return call()
        cache_name = "__" + f.__name__
        if ensemble_member is not None:
            cache_name = f"{cache_name}[{ensemble_member}]"
        if hasattr(self, cache_name):
            return getattr(self, cache_name)
        setattr(self, call_in_progress, True)
        value = call()
        setattr(self, cache_name, value)
        delattr(self, call_in_progress)
        return value

    return wrapper
