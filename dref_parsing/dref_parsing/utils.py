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

# split a string into list of words
def get_words_from_string(s):
    ww = s.lower().split(' ')
    ww = [w.strip('-').strip(' ') for w in ww]
    ww = [w for w in ww if w!='']
    return ww 

# Finds common words in 2 strings
def get_common_words(s1,s2):
    w1 = get_words_from_string(s1)
    w2 = get_words_from_string(s2)
    common = set(w1).intersection(set(w2))
    return common

# ****************************************************************************************
# Finding Text
# ****************************************************************************************

# Alternative findall can be done using:
# https://docs.python.org/3/library/re.html
# http://www.learningaboutelectronics.com/Articles/How-to-search-for-a-case-insensitive-string-in-text-Python.php

# import re
# re.finditer(pattern, s, flags=re.IGNORECASE)
#>>> text = "He was carefully disguised but captured quickly by police."
#>>> for m in re.finditer(r"\w+ly", text):
#...     print('%02d-%02d: %s' % (m.start(), m.end(), m.group(0)))
#07-16: carefully
#40-47: quickly

# ****************************************************
# Simple case-sensitive version, not used anymore
def findall0(pattern, s, region=True, n=30, nback=-1, pattern2=''):
    if nback<0: nback=n
    ii = []
    i = s.find(pattern)
    while i != -1:
        if region:
            t = s[i-nback : i+n]
            if pattern2!='' and t.count(pattern2)>0:
                t = t.split(pattern2)[0]
            ii.append((i,t))
        else:
            ii.append(i)
        i = s.find(pattern, i+1)
    return ii

# ****************************************************
# Finds all positions of the pattern p in the string s,
# if region=True also outputs the next n chars (and previous nback chars) 
# The text output is cut at pattern2
def findall(pattern, s, region=True, n=30, nback=-1, pattern2='', ignoreCase=True):

    if nback<0: nback=n
    ii = []
    if ignoreCase:
        i = s.lower().find(pattern.lower())
    else:
        i = s.find(pattern)
    while i != -1:
        if region:
            t = s[max(0,i-nback) : i+n]   
            
            # Stop string at pattern2
            
            if pattern2 != '':
                if ignoreCase: index2 = t.lower().find(pattern2.lower())
                else:          index2 = t.find(pattern2)
                if index2 != -1:
                    t = t[:index2]

            ii.append((i,t))
        else:
            ii.append(i)
        i = s.find(pattern, i+1)
    return ii    

# **************************************************************************************
# Wrapper: allows calling findall with a list of patterns 
# (by replacement, i.e. the string fragments can be modified)
def findall_patterns(patterns, s0, region=True, n=30, nback=-1, pattern2='', ignoreCase=True):
    if type(patterns) != list:
        # prepare for usual call 
        pattern = patterns
        s = s0
    else:
        # Replace in s all other patterns with the 0th pattern and then call
        pattern = patterns[0]
        s = s0
        for p in patterns[1:]:
            s = s.replace(p,pattern)
    return findall(pattern=pattern, s=s, region=region, n=n, nback=nback, pattern2=pattern2, ignoreCase=ignoreCase)