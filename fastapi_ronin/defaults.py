class _NotSet:
    def __repr__(self):
        return '<fastapi_ronin.defaults.NOT_SET>'


NOT_SET = _NotSet()

# Cache
CACHE_DEFAULT_TTL = NOT_SET
CACHE_DEFAULT_NAMESPACE = 'ronin'
