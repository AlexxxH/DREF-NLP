import re

all_bullets = ('•','●','▪','-')

# Returns substring preceeding a number
def before_number(s):
    for i in range(len(s)):
        if s[i].isdigit():
            return s[:i]
    return s

# Returns substring after a number
def after_number(s):
    for i in range(len(s)-1,-1,-1): 
        if s[i].isdigit():
            return s[i+1:]
    return s

# Does it have substrings like '1.5', typical for section numbers
def has_digit_dot_digit(s):
    for i in range(len(s)-2):
        if s[i].isdigit():
            if (s[i+1]=='.') and s[i+2].isdigit():
                return True
    return False

# ****************************************************************************************
# STRING OPERATIONS
# ****************************************************************************************

def replace_texts(oldvalues, newvalue, string):
    for oldvalue in oldvalues:
        string = string.replace(oldvalue, newvalue)
    return string

# get the bottom line, i.e. text after the last linebreak
def get_bottom_line(s, drop_spaces=False, drop_empty=True):
    if drop_spaces:
        s = s.replace(' ', '')
    lines = s.split('\n')
    if drop_empty:
        lines = [line for line in lines if line.strip(' ')!='']
    return lines[-1]

# True if there exist at least 2 letters after each other, otherwise it's not a text
def exist_two_letters_in_a_row(ch):
    if len(ch)<2:
        return False
    for i in range(len(ch) - 1):
        if ch[i].isalpha() and ch[i+1].isalpha():
            return True
    return False

# Strip string of special symbols and sequences (from beginning & end)
def strip_all(s, left=True, right=True):
    symbols=[' ','\n']+list(all_bullets)
    start_sequences = ['.','1.','2.','3.','4.','5.','6.','7.','8.','9.']
    
    for i in range(20):
        for symb in symbols:
            if left:  s = s.lstrip(symb)
            if right: s = s.rstrip(symb)
            
        for seq in start_sequences:
            if s.startswith(seq):
                s = s[len(seq):]
    return s

# Return bullet char if the string starts with a bullet.
# Otherwise - returns an empty string
def starts_with_bullet(s0, bullets=all_bullets):
    s = s0.lstrip()
    if len(s)==0:
        return ''
    if s[0] in bullets:
        return s[0]
    else:
        return ''

# -------------------------------------------
def drop_spaces_between_linebreaks(txt):
    return re.sub('\n[ \t]+\n', '\n\n', txt)

# ****************************************************************************************
# Finding Text
# ****************************************************************************************


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

# ************************************************************************
# TODO: other bulets ???
def is_same_bullet_type(c1, c2):
    c2 = c2.lstrip('\n ')
    bullet = '• '
    if c1.startswith(bullet) and c2.startswith(bullet):
        return True
    return False

#*********************************************************************************************
# Removes a piece of text that presumably is an image caption 
# because it contains one of 'patterns"
def drop_image_caption(a, patterns = ['(Photo:', '(Image:', 'Source:'] ):
    for patt in patterns:
        a = drop_image_caption_one(a, pattern = patt)
    # Do it again, in case there are two captions 
    for patt in patterns:
        a = drop_image_caption_one(a, pattern = patt)
    return a

# Remove a piece of text that presumable is an image caption because it contains 'pattern"
def drop_image_caption_one(a, pattern = '(Photo:'):
    if pattern not in a:
        return a
    # Find where the pattern occurs, and the caption ends
    i0 = findall(pattern, a)[0][0]
    if a[i0:].count('\n\n')==0:
        end_caption = len(a)
    else:
        end_caption = i0 + findall('\n\n', a[i0:])[0][0]
    
    # Search for double linebreaks backwards.
    # Choose those that are followed by a sentence start.
    # It gives the start of the caption
    dlbs = findall('\n\n', a[:i0])
    start_caption = 0
    for dlb in dlbs[::-1]:
        txt_after_dlb = a[dlb[0]:][:20]
        if is_sentence_start(txt_after_dlb):
            start_caption = dlb[0]
            break
    return a[:start_caption] +  a[end_caption:]

#*********************************************************************************************

# Loops over list and splits each element by separator(s)
# Possible extra_separators: "In addition,"  but it's not always separator.
def split_list_by_separator(
        chs, 
        seps = ['\n\n','\n \n','\n  \n','\n   \n', '\n●','\n•','\n-','\n2.','\n3.','\n4.','\n5.'], 
        extra_sep=['\nOutput 1','\nOutput 2','\nOutcome 1','\nOutcome 2']
    ):
    new_chs = []
    for ch in chs:
        cc = ch[1]
        for e in extra_sep:
            cc = cc.replace(e, seps[0]+e)
        splitted = split_text_by_separator(cc, seps = seps)

        # Drop all starting with an element that must be rejected
        for i,spl in enumerate(splitted):
            if reject_excerpt(spl):
                splitted = splitted[:i]
                break

        for spl in splitted:
            new_chs.append((ch[0],spl))
    return new_chs 


#****************************************************************************************
# Returns text splitted by at least one of separators (but only if they separate sentences)
def split_text_by_separator(cc0, seps = ['\n\n'], bullets=['\n●','\n•','\n-']):
    splitted = []
    # replace other separators by 0th separator
    cc = cc0
    for sep in seps[1:]:
        cc = cc.replace(sep,seps[0])
    sep = seps[0]
    nsep = cc.count(sep)
    # Presence of bullets adds confidence that we should split
    splitted_by_bullets = split_by_seps(cc0, bullets)

    current_piece = cc.split(sep)[0]
    for i in range(nsep):
        
        # Separator is ok only if it looks like it separates sentences
        ends_ok   = is_sentence_end(cc.split(sep)[i])
        starts_ok = is_sentence_start(cc.split(sep)[i+1])
        not_strange = not is_smth_strange(cc.split(sep)[i], cc.split(sep)[i+1])
        # if both fragment - after and before - coincide with fragments obtained
        # by splitting with bullets only, then it's likely to be correctly
        # splitted fragments:
        bullet_borders = ((cc.split(sep)[i  ] in splitted_by_bullets) + 
                          (cc.split(sep)[i+1] in splitted_by_bullets))
        sep_ok = ends_ok + starts_ok + not_strange + bullet_borders*0.5 >= 2
        if sep_ok:
            splitted.append(current_piece)
            current_piece = ''
        current_piece += cc.split(sep)[i+1]
    splitted.append(current_piece)     
    return splitted

# ****************************************************************************************
# replaces all separators by 0th separator and then splits
def split_by_seps(cc, seps):
    for sep in seps[1:]:
        cc = cc.replace(sep, seps[0])
    return cc.split(seps[0])

# ****************************************************************************************
# Does the string s start from the start of a sentence, or is it from part way through
def is_sentence_start(s):
    for i, char in enumerate(s):
        # Lowercase
        if char.islower() and (not char.isupper()):
            return 0
        # Uppercase
        if char.isupper() and (not char.islower()):
            # Last character
            if i+1>=len(s): 
                return 0
            # Two capital letters (abbreviation). Cannot tell if this is a sentence start
            if s[i+1].isupper() and (not s[i+1].islower()):
                return 0.5
            # Capital letter then small letter
            else:
                return 1
        # bullet point is like a start of sentence
        if char in all_bullets: 
            return 1
    # if no letters found - lower or upper - then it's not a sentence, hence not a sentence start
    return 0


def is_sentence_end(s, endings=['.', '?', '!']):
    s = s.rstrip('\n ')
    if len(s)==0:
        return False
    return s[-1] in endings

# ****************************************************************************************
# If smth strange i.e. 'and' just before the separator
def is_smth_strange(s1, s2, min_len = 10):
    strange_end = s1.rstrip(' ').split(' ')[-1] in ['and','the']
    too_short = (len(s2) < min_len) 
    # adding (len(s1) < min_len) breaks down some excerpts in ID015, VU008, not clear why
    return strange_end or too_short


# If it looks like smth different, e.g. a typical heading,
# then it is not an excerpt
def reject_excerpt(cc):
    if cc.count('Output')>0 and has_digit_dot_digit(cc):
        # it is typical heading
        return True
    if cc.count('\nOutcome 1')>0 or cc.count('\nOutcome 2')>0:
        # it is typical heading
        return True
    return False

# ****************************************************************************************
# Locate & Process Challenges
# ****************************************************************************************

# Skip challenge when it is basically absent
def skip_ch(ch): 
    if len(ch)<3:
        return True
    if not exist_two_letters_in_a_row(ch):
        return True
    if strip_all(ch).startswith('None') and (len(ch)<30):
        return True
    if strip_all(ch).startswith('Nothing') and (len(ch)<30):
        return True
    if ch.startswith('No challenge') and (len(ch)<30):
        return True
    if ch.startswith('No lesson') and (len(ch)<30):
        return True
    if ch.startswith('Not applicable') and (len(ch)<30):
        return True
    if ch.strip(' \n.').lower() in ['none', 'n/a']:
        return True
    if ch.startswith('Similar challenges as') and (len(ch)<70):
        return True
    if ch.strip(' \n\t').startswith('Not enough reporting') and (len(ch)<105):
        return True
    return False


# True if there is no text (except possibly spaces) when searching for LB backwards
def are_there_only_spaces_before_LB(s):
    before_LB = s.split('\n')[-1]
    return before_LB.strip(' ') == ''