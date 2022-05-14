import hmac
import hashlib
import base64

def hmac_it(message):
    """
    Source: https://stackoverflow.com/questions/39767297/how-to-use-sha256-hmac-in-python-code
    Output is like the one that generated with that calculator: https://www.freeformatter.com/hmac-generator.html#ad-output
    """

    key = bytes("Banana", "UTF-8")
    message = message.encode()
    h = hmac.new(key, message, hashlib.sha1)

    return h.hexdigest()

def validate_password(userID, password):
    # In real life should be the result of getting the saved hmac for that user from the db.
    currentUserHmacPassword = userID
    
    hmacedPassword = hmac_it(password)

    return (currentUserHmacPassword == hmacedPassword)