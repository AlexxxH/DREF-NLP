all_bullets = ['•','●','▪','-']

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

# ****************************************************************************************
# STRING OPERATIONS
# ****************************************************************************************

# get the bottom line, i.e. text after the last linebreak
def get_bottom_line(s, drop_spaces=False, drop_empty=True):
    if drop_spaces:
        s = remove_symbols(s, symbols=[' '])
    lines = s.split('\n')
    if drop_empty:
        lines = [line for line in lines if line.strip(' ')!='']
    return lines[-1]

# True if there exist at least 2 letters after each other, otherwise it's not a text
def exist_two_letters_in_a_row(ch):
    if len(ch)<2:
        return False
    is_previous_letter = is_char_a_letter(ch[0])
    for c in ch[1:]:
        is_current_letter = is_char_a_letter(c)
        if is_previous_letter and is_current_letter:
            return True
        is_previous_letter = is_current_letter
    return False

# Removes all text after the LAST occurence of pattern, including the pattern
def rstrip_from(s, pattern):
    return s[:s.rfind(pattern)]

# Strip string from special symbols and sequences (from beginning & end)
def strip_all(s, left=True, right=True, symbols=[' ','\n']+all_bullets, 
              start_sequences = ['.','1.','2.','3.','4.','5.','6.','7.','8.','9.']):
    for i in range(20):
        for symb in symbols:
            if left:  s = s.lstrip(symb)
            if right: s = s.rstrip(symb)
            
        for seq in start_sequences:
            if s.startswith(seq):
                s = s[len(seq):]                
    return s        

# Strip string from spaces and linebreaks
def strip_all_empty(s, left=True, right=True):
    return strip_all(s, left=left, right=right, symbols=[' ','\n'], start_sequences = [])       

# Return bullet char if the string starts with a bullet.
# Otherwise - returns an empty string
def starts_with_bullet(s0, bullets=all_bullets):
    s = strip_all_empty(s0, right=False)
    if len(s)==0:
        return ''
    if s[0] in bullets:
        return s[0]
    else:
        return ''

# -------------------------------------------
def drop_spaces_between_linebreaks(txt):
    out = txt
    for i in range(5):
        out = out.replace('\n \n','\n\n')
        out = out.replace('\n  \n','\n\n')
        out = out.replace('\n   \n','\n\n')
        out = out.replace('\n    \n','\n\n')
        out = out.replace('\n     \n','\n\n')
    return out    
