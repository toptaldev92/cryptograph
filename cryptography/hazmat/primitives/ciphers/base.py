# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function

from cryptography import utils
from cryptography.exceptions import (
    AlreadyFinalized, NotYetFinalized, AlreadyUpdated,
)
from cryptography.hazmat.primitives import interfaces


class Cipher(object):
    def __init__(self, algorithm, mode, backend):
        if not isinstance(algorithm, interfaces.CipherAlgorithm):
            raise TypeError("Expected interface of interfaces.CipherAlgorithm")

        self.algorithm = algorithm
        self.mode = mode
        self._backend = backend

    def encryptor(self):
        if isinstance(self.mode, interfaces.ModeWithAAD):
            return _AEADCipherContext(
                self._backend.create_symmetric_encryption_ctx(
                    self.algorithm, self.mode
                )
            )
        else:
            return _CipherContext(
                self._backend.create_symmetric_encryption_ctx(
                    self.algorithm, self.mode
                )
            )

    def decryptor(self):
        if isinstance(self.mode, interfaces.ModeWithAAD):
            return _AEADCipherContext(
                self._backend.create_symmetric_decryption_ctx(
                    self.algorithm, self.mode
                )
            )
        else:
            return _CipherContext(
                self._backend.create_symmetric_decryption_ctx(
                    self.algorithm, self.mode
                )
            )


@utils.register_interface(interfaces.CipherContext)
class _CipherContext(object):
    def __init__(self, ctx):
        self._ctx = ctx

    def update(self, data):
        if self._ctx is None:
            raise AlreadyFinalized("Context was already finalized")
        return self._ctx.update(data)

    def finalize(self):
        if self._ctx is None:
            raise AlreadyFinalized("Context was already finalized")
        data = self._ctx.finalize()
        self._ctx = None
        return data


@utils.register_interface(interfaces.AEADCipherContext)
@utils.register_interface(interfaces.CipherContext)
class _AEADCipherContext(object):
    def __init__(self, ctx):
        self._ctx = ctx
        self._tag = None
        self._updated = False

    def update(self, data):
        if self._ctx is None:
            raise AlreadyFinalized("Context was already finalized")
        self._updated = True
        return self._ctx.update(data)

    def finalize(self):
        if self._ctx is None:
            raise AlreadyFinalized("Context was already finalized")
        data = self._ctx.finalize()
        self._tag = self._ctx._tag
        self._ctx = None
        return data

    def add_data(self, data):
        if self._ctx is None:
            raise AlreadyFinalized("Context was already finalized")
        if self._updated:
            raise AlreadyUpdated("Update has been called on this context")
        self._ctx.add_data(data)

    @property
    def tag(self):
        if self._ctx is not None:
            raise NotYetFinalized("You must finalize encryption before "
                                  "getting the tag")
        return self._tag
