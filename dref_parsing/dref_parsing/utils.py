# Is char a digit 0-9?
def is_digit(c):
    return c >= '0' and c<='9'

# If char is neither lower or upper case, it is not a letter
def is_char_a_letter(c):
    return c.islower() or c.isupper()

# removes all given symbols from a string
def remove_symbols(s, symbols=[' ']):
    return ''.join([c for c in s if not c in symbols])

# Returns substring preceeding a number
def before_number(s):
    for i in range(len(s)):
        if is_digit(s[i]):
            return s[:i]
    return s

# Returns substring after a number
def after_number(s):
    for i in range(len(s)-1,-1,-1): 
        if is_digit(s[i]):
            return s[i+1:]
    return s

# Does it have substrings like '1.5', typical for section numbers
def has_digit_dot_digit(s):
    for i in range(len(s)-2):
        if is_digit(s[i]):
            if (s[i+1]=='.') and is_digit(s[i+2]):
                return True
    return False