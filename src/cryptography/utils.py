# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import absolute_import, division, print_function

import abc
import binascii
import inspect
import struct
import sys
import warnings


DeprecatedIn09 = DeprecationWarning
DeprecatedIn10 = PendingDeprecationWarning


def read_only_property(name):
    return property(lambda self: getattr(self, name))


def register_interface(iface):
    def register_decorator(klass):
        verify_interface(iface, klass)
        iface.register(klass)
        return klass
    return register_decorator


if hasattr(int, "from_bytes"):
    int_from_bytes = int.from_bytes
else:
    def int_from_bytes(data, byteorder, signed=False):
        assert byteorder == 'big'
        assert not signed

        if len(data) % 4 != 0:
            data = (b'\x00' * (4 - (len(data) % 4))) + data

        result = 0

        while len(data) > 0:
            digit, = struct.unpack('>I', data[:4])
            result = (result << 32) + digit
            data = data[4:]

        return result


def int_to_bytes(integer):
    hex_string = '%x' % integer
    n = len(hex_string)
    return binascii.unhexlify(hex_string.zfill(n + (n & 1)))


class InterfaceNotImplemented(Exception):
    pass


if hasattr(inspect, "signature"):
    signature = inspect.signature
else:
    signature = inspect.getargspec


def verify_interface(iface, klass):
    for method in iface.__abstractmethods__:
        if not hasattr(klass, method):
            raise InterfaceNotImplemented(
                "{0} is missing a {1!r} method".format(klass, method)
            )
        if isinstance(getattr(iface, method), abc.abstractproperty):
            # Can't properly verify these yet.
            continue
        sig = signature(getattr(iface, method))
        actual = signature(getattr(klass, method))
        if sig != actual:
            raise InterfaceNotImplemented(
                "{0}.{1}'s signature differs from the expected. Expected: "
                "{2!r}. Received: {3!r}".format(
                    klass, method, sig, actual
                )
            )


if sys.version_info >= (2, 7):
    def bit_length(x):
        return x.bit_length()
else:
    def bit_length(x):
        return len(bin(x)) - (2 + (x <= 0))


class _DeprecatedValue(object):
    def __init__(self, value, message, warning_class):
        self.value = value
        self.message = message
        self.warning_class = warning_class


class _ModuleWithDeprecations(object):
    def __init__(self, module):
        self.__dict__["_module"] = module

    def __getattr__(self, attr):
        obj = getattr(self._module, attr)
        if isinstance(obj, _DeprecatedValue):
            warnings.warn(obj.message, obj.warning_class, stacklevel=2)
            obj = obj.value
        return obj

    def __setattr__(self, attr, value):
        setattr(self._module, attr, value)

    def __dir__(self):
        return ["_module"] + dir(self._module)


def deprecated(value, module_name, message, warning_class):
    module = sys.modules[module_name]
    if not isinstance(module, _ModuleWithDeprecations):
        sys.modules[module_name] = module = _ModuleWithDeprecations(module)
    return _DeprecatedValue(value, message, warning_class)
