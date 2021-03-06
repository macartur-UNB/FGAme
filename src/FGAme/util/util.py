# -*- coding: utf8 -*-


class lazy(object):

    '''Implementa uma propriedade "preguiçosa": ela é calculada apenas durante o
    primeiro uso e não durante a inicialização do objeto.'''

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        value = self.func(obj)
        setattr(obj, self.func.__name__, value)
        return value


class delegate_to(property):

    '''Sincroniza com um attributo de contido em um sub-attributo da classe.

    Exemplo
    -------

    >>> class Foo(object):
    ...     def __init__(self):
    ...         self._data = []
    ...
    ...     add = delegate_to('_data.append')

    Agora criamos um objeto

    >>> x = Foo()
    >>> x.add(1); x.add(2); x._data
    [1, 2]
    '''

    def __init__(self, delegate, read_only=False):
        self.delegate = delegate
        attrs = delegate.split('.')
        delegate = attrs.pop(0)

        if len(attrs) == 0:
            def fget(self):
                return getattr(self, delegate)

            def fset(self, value):
                setattr(self, delegate, value)

            def fdel(self):
                delattr(self, delegate)

        elif len(attrs) == 1:
            attr = attrs[0]

            def fget(self):
                delegate_obj = getattr(self, delegate)
                return getattr(delegate_obj, attr)

            def fset(self, value):
                delegate_obj = getattr(self, delegate)
                setattr(delegate_obj, attr, value)

            def fdel(self):
                delegate_obj = getattr(self, delegate)
                delattr(delegate_obj, attr)

        else:
            raise NotImplementedError('more than one dot')

        if read_only:
            super(delegate_to, self).__init__(fget)
        else:
            super(delegate_to, self).__init__(fget, fset, fdel)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
