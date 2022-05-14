from django.contrib.auth.hashers import SHA1PasswordHasher, PBKDF2PasswordHasher, PBKDF2SHA1PasswordHasher

class HMACPasswordHasher(SHA1PasswordHasher):

    def encode_sha1_hash(self, sha1_hash, salt, iterations=None):
        return super().encode(sha1_hash, salt, iterations)

    def encode(self, password, salt, iterations=None):
        iterations = None
        _, _, sha1_hash = SHA1PasswordHasher().encode(password, salt).split('$', 2)
        return self.encode_sha1_hash(sha1_hash, salt, iterations)

class OneIterationOnlyPBKDF2SHA1PasswordHasher(PBKDF2SHA1PasswordHasher):
    """
    A subclass of PBKDF2PasswordHasher that uses 100 times more iterations.
    """
    
    iterations = 1