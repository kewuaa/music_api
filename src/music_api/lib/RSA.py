import binascii

import rsa


class RSA:
    """ RSA."""

    def __init__(self, modulus: str, publicExponent: str):
        """ initialize.

        :param modulus: modulus of RSA
        :param publicExponent: exponent of public key
        """

        super(RSA, self).__init__()
        n = int(modulus, 16)
        e = int(publicExponent, 16)
        self.key = rsa.PublicKey(n, e)

    def encrypt(self, message: str):
        """ encrypt message.

        :param message: message to encrypt
        """

        result = rsa.encrypt(message.encode(), self.key)
        result = binascii.b2a_hex(result)
        return result.decode()
