def docstring_decorator(s):
    """
    动态修改docstring装饰器
    >>> a = "test"
    >>> @docstring_decorator(f"a={a}")
    >>> def f():
    >>>     pass
    >>> print(f.__doc__)  # a=test
    """

    def _decorator(obj):
        obj.__doc__ = str(s)
        return obj

    return _decorator
