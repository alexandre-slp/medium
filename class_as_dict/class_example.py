class Class(dict):
    foo = 'foo'
    bar = 'bar'

    def __repr__(self):
        self.__setitem__('foo', self.foo)
        self.__setitem__('bar', self.bar)
        return super().__repr__()

c = Class()
c
# Output:
{'foo': 'foo', 'bar': 'bar'}
