"""
DREF Document Class
"""
import io
import re
import copy
import requests
from functools import cached_property

import tika.parser
import numpy as np
import pandas as pd

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTImage, LTFigure, LTTextBox, LTTextBoxHorizontal

from dref_parsing import utils, definitions


class AppealDocument:
    """
    Parameters
    ----------
    """
    def __init__(self, created_at, document, document_url, appeal, document_type, iso, description, id, name, translation_module_original_language):

        # Set attributes from params
        self.created_at = created_at
        self.document = document
        self.document_url = document_url
        self.appeal = appeal
        self.mdr_code = appeal['code']
        self.document_type = document_type
        self.iso = iso
        self.description = description
        self.id = id
        self.name = name
        self.translation_module_original_language = translation_module_original_language


    @cached_property
    def content_bytes(self):
        """
        """
        pdf_data = requests.get(self.document_url).content
        return io.BytesIO(pdf_data)

    
    @cached_property
    def content(self):
        """
        """
        pdf_data = requests.get(self.document_url).content
        content_bytes = io.BytesIO(pdf_data)
        parsed = tika.parser.from_buffer(content_bytes)
        return parsed['content']


    @cached_property
    def headers_footers_postheaders(self):
        """
        Get headers, footers, and postheaders from the document.
        """
        headers = []
        footers = []
        postheaders = []

        # Loop through pages
        for page_layout in extract_pages(self.content_bytes):
            postheader_now = False
            header_now = True
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    if utils.strip_all_empty(element.get_text()) != '':
                        element_text = element.get_text()

                        if postheader_now:
                            postheader = element_text
                            postheader_now = False

                        if header_now:
                            header = element_text
                            header_now = False
                            postheader_now = True

            headers.append(header)
            postheaders.append(postheader)
            footers.append(element_text)

        return {
            'headers': headers,
            'footers': footers, 
            'postheaders': postheaders
        }


    def get_challenges_lessons_learned(self):
        """
        Extract the Challenges and Lessons Learned from the document.
        """
        # Copy self, and process the copy
        document = copy.deepcopy(self)

        # Remove headers and footers
        document.remove_content(
            document.repeatable_element_auto(document.headers_footers_postheaders['headers']), 
            n=300,
            before = 'stop_at_linebreak', 
            after = 'stop_at_linebreak'
        )
        document.remove_content(
            document.repeatable_element_auto(document.headers_footers_postheaders['footers']), 
            n=300,
            before = 'stop_at_linebreak',
            after = 'stop_at_linebreak'
        )

        # Get challenges and lessons learned
        challenges = [
            (
                ch[0], 
                ch[1], 
                'Challenges'
            ) for ch 
            in document.get_CHs_from_text()
        ]
        lessons_learned = [
            (
                ch[0], 
                ch[1], 
                'Lessons Learnt'
            ) for ch 
            in document.get_LLs_from_text()
        ]
        parsed = challenges + lessons_learned

        # Add section names
        exs_parsed = [
            (
                ch[0], 
                ch[1], 
                ch[2], 
                document.get_section_from_position(ch[0])
            ) for ch 
            in parsed
        ]
        exs_parsed = pd.DataFrame(exs_parsed, columns=['position','Modified Excerpt','Learning','section'])

        # Convert section name to full and short DREF_sector:
        exs_parsed['DREF_Sector_id'] = exs_parsed['section'].apply(lambda x: document.shorten_sector(x))
        exs_parsed['DREF_Sector'] = exs_parsed['DREF_Sector_id'].apply(lambda x: document.full_sector_name(x))

        exs_parsed['lead'] = document.mdr_code

        return exs_parsed, parsed


    def repeatable_element(self, footers0, threshold=0.5, numbers=''):
        
        if numbers == '':
            footers = footers0
        if numbers == 'stop_before':
            footers = [utils.before_number(f) for f in footers0]
        if numbers == 'stop_after':
            footers = [utils.after_number(f) for f in footers0]
            
        vc = pd.DataFrame({'footer':footers}).footer.value_counts()
        if vc[0] > threshold * len(footers):
            return vc.index[0].rstrip('\n')
        else:
            return ''


    def repeatable_element_auto(self, footers0, threshold=0.3):
        output1 = self.repeatable_element(footers0=footers0, threshold=threshold, numbers='')
        output2 = self.repeatable_element(footers0=footers0, threshold=threshold, numbers='stop_before')
        output3 = self.repeatable_element(footers0=footers0, threshold=threshold, numbers='stop_after')
        if len(output1)>len(output2) and len(output1)>len(output3):
            return output1 
        else:
            return output2 if len(output2)>len(output3) else output3


    def remove_content(self, footer, n=300, after='', before=''):

        if len(footer)<=1: return self.content
        pbflag = '!!!Page_Break!!!'
    
        cc = utils.findall(footer, self.content, region=True, n=n, ignoreCase=False)
        # Loop over footers, start from the end so that indices are not changed
        # when later footers are removed
        for c in cc[::-1]:
            s = c[1]; k=c[0]
            
            # Search backwards from footer
            i = k
            if before == 'drop_linebreaks':
                # extend footer with nearest 'empty' characters
                while self.content[i-1] in [' ','\n']:
                    i = i - 1
                    if i==0: break
            if before == 'stop_at_linebreak':
                # extend footer until a linebreak is found
                while not self.content[i-1] in ['\n']:
                    i = i - 1
                    if i==0: break
            start = i
            
            # Search forward from footer, the same 2 options
            i = k + len(footer)
            if after == 'drop_linebreaks':
                while self.content[i] in [' ','\n']:
                    i = i + 1
                    if i==len(self.content): break
            if after == 'stop_at_linebreak':
                while not self.content[i] in ['\n']:
                    i = i + 1
                    if i==len(self.content): break
            finish = i
            self.content = self.content[:start] + pbflag + self.content[finish:]
        

    def get_CHs_from_text(self):
        patterns = ['\n\nChallenges', '\n \nChallenges', '\n  \nChallenges', 
        '\nChallenges \n', '\n\n Challenges']
        chs = utils.findall(
            pattern = patterns[0], 
            s = utils.replace_texts(patterns[1:], patterns[0], self.content),
            region=True, 
            n = 50000, 
            nback = 5, 
            pattern2 = '\nLessons '
        )

        # Leave only text after the word "Challenges"
        keyword = '\nChallenges'
        chs = [(ch[0], ch[1][len(ch[1].split(keyword)[0])+len(keyword):]) for ch in chs]

        # We must stop the fragment at linebreaks if:
        # 1. CH fragments overlap (i.e. LL section is missing)
        # 2. fragment is too long
        # 3. fragment is quite long and likely to stop at LBs
        for i,ch in enumerate(chs):
            overlaps_next = (i+1 < len(chs)) and (ch[0] + len(ch[1]) > chs[i+1][0])
            too_long = len(ch[1])>3500
            quite_long = len(ch[1])>1000
            if overlaps_next or too_long or (quite_long and self.stop_at_multiple_LBs(ch[1])):
                chs[i] = (ch[0], finish_LL_section(ch[1], stop='\n\n\n\n'))
        
        chs = [(ch[0], self.avoid_pagebreak(ch[1])) for ch in chs]
        chs = [ch for ch in chs if ch[1]!='']

        chs = self.split_and_clean_CHLL(chs)   
        return chs


    def get_LLs_from_text(self):
        lls = utils.findall(
            pattern = '\nLessons', 
            s = self.content, 
            region = True, 
            n = 7000, 
            nback = 0
        )
        lls = [(ll[0], self.strip_LL_section_start(ll[1])) for ll in lls]
        lls = [(ll[0], self.avoid_pagebreak(ll[1])) for ll in lls]
        lls = [(ll[0], self.finish_LL_section(ll[1])) for ll in lls]
        lls = [ll for ll in lls if ll[1]!='']

        lls = self.split_and_clean_CHLL(lls)
        lls = self.stop_at_capital(lls)
        return lls


    @cached_property
    def sections(self):
        """
        Get a list of all Section names from PDF text
        """
        # "Classic" sections, by markers:
        prs1 = self.find_sections_classic()

        # "Strategy" sections, by names:
        prs2 = self.find_sections_strategy()

        # New-template sections, by markers:
        prs3 = self.find_sections_new()

        # Return all combined
        return prs1 + prs2 + prs3


    def find_sections_classic(self):
        """
        Get a list of section names based on 'classic' section markers
        """
        # Find text that precedes classic section_markers
        section_markers =  [
            '\nPeople reached',
            '\nPeople targeted',
            '\nPopulation reached',
            '\nPopulation targeted',
            '\nTotal number of people reached'
        ]
        prs = utils.findall(
            pattern = section_markers[0], 
            s = utils.replace_texts(section_markers[1:], section_markers[0], self.content), 
            region = True, 
            n = 0, 
            nback = 100
        )

        # Several markers can come close to each other, 
        # e.g. 'People reached' & 'People targeted'
        # Then we should keep only the first one:
        pp = [pr[0] for pr in prs] # only positions
        too_close_indices = [i for i in range(1, len(pp)) if pp[i] < pp[i-1] + 100]
        prs = [pr for i,pr in enumerate(prs) if not i in too_close_indices]

        # Take only the bottom line of the text (search for LB backward)
        # assuming that the last line before the marker is section name
        prs = [(pr[0], utils.get_bottom_line(pr[1])) for pr in prs]
        return prs


    def find_sections_strategy(self):
        """
        Get a list of 'Strategic" sections
        """
        # Later sections that all correspond to 'Strategy' Sector
        strategy_sections = [
            sector['name'] for sector 
            in definitions.SECTORS 
            if sector['id'] == 'Strategies'
        ]
        prs = utils.findall(
            pattern = strategy_sections[0], 
            s = utils.replace_texts(strategy_sections[1:], strategy_sections[0], self.content), 
            region = True, 
            n = 0, 
            nback = 100
        )

        # Section Title is always preceeded by linebreak & possibly spaces after it.
        # If not, these are not sections (just plain text), exclude them
        prs = [pr for pr in prs if utils.are_there_only_spaces_before_LB(pr[1])]

        # Name them 'Strategies'
        prs = [(pr[0], 'Strategies') for pr in prs]
        return prs


    def find_sections_new(self):
        """
        Sections for the new template
        """
        # find what precedes pattern
        prs = utils.findall(
            pattern = "reached", 
            s = self.content, 
            region = True,
            n = 0, 
            nback = 100
        )

        # keep only if the previous line (or previous word) is 'Persons'
        prs = [pr for pr in prs if utils.get_bottom_line(pr[1], drop_spaces=True)=='Persons']

        prs_processed = []
        for pr in prs:
            # Process string:
            s = pr[1]

            # drop all text starting from 'Persons' 
            s = utils.rstrip_from(s,'Persons')

            s = utils.strip_all_empty(s, left=False)
            s = utils.drop_spaces_between_linebreaks(s)

            # keep what's after multiple linebreaks
            s = s[s.rfind("\n\n\n"):]
            # remove linebreaks
            s = utils.remove_symbols(s, symbols=['\n']).strip(' ')

            # Save string back to tuple:
            prs_processed.append( (pr[0], s) )

        return prs_processed


    def get_section_from_position(self, position):
        """
        Find section to which a given position in the text belongs (to determine Sector)
        """
        distances = [(position-sec[0],sec[1]) for sec in self.sections if position>sec[0]]
        if distances==[]:
            # position is BEFORE all sections
            return 'before'
        # index of the nearest section-start
        isec = np.argmin([dist[0] for dist in distances])
        return self.sections[isec][1]


    def shorten_sector(self, sector_name):
        sector_mapping = {
            'livelihoods': 'Live',
            'water': 'WASH',
            'shelter': 'Shelter',
            'inclusion': 'PGI',
            'protection': 'PGI',
            'disaster': 'Disaster',
            'health': 'Health'
        }
        for sector in sector_mapping:
            if sector_name.lower().count(sector)>0: 
                return sector_mapping[sector]

        for sector in definitions.SECTORS:
            if sector_name.strip().lower() == sector['id'].strip().lower():
                return sector['id']
        for sector in definitions.SECTORS:
            if sector_name.strip().lower() == sector['name'].strip().lower():
                return sector['id']
        
        return 'Unknown'


    def full_sector_name(self, sector_name):
        for sector in definitions.SECTORS:
            if sector['true name']:
                if sector_name.strip().lower() == sector['id'].strip().lower():
                    return sector['name']

        return 'Unknown'


    def avoid_pagebreak(self, c, stop='\n\n\n'):
        # Replaces possible double flags (from both header & footer) by one flag
        c = utils.remove_double_pbflag(c)
        pbflag = '!!!Page_Break!!!'

        if c.count(pbflag)==0:
            # if no pagebreaks, do nothing
            cout = c

        else:
            c1 = c.split(pbflag)[0]
            c2 = c.split(pbflag)[1]
            if utils.strip_all_empty(c1).count(stop)>0:
                # stops are found before pagebreak, hence ignore the next-page text
                cout = c1
            else:
                consistent = utils.is_sentence_end(c1) == utils.is_sentence_start(c2)
                must_go_on = utils.strip_all_empty(c1, left=False)[-1]==':'
                # NB: so far must_go_on is never used, i.e. can be dropped
                if consistent or must_go_on or c1=='':
                    # Looks like next-page text may be a continuation of previous-page
                    # Thus, we shall append the next-page text
                    if utils.is_same_bullet_type(c1, c2):
                        # the same bullets used before and after, hence it's likely
                        # the same block of text, thus lets remove linebreaks coming from the pagebreak
                        c1 = utils.strip_all_empty(c1, left=False)
                        c2 = utils.strip_all_empty(c2, right=False)
                    cout = c1 + '\n\n' + c2
                else:
                    cout = c1
        return cout


    # Find where LL section starts, i.e. strip away its title (smth like 'Lessons Learned:\n')
    # We use one linebreak as pattern, to be safe, even though in 99% of cases
    # there is a double-linebreak after 'Lessons Learned'
    def strip_LL_section_start(self, s, start =  '\nLessons', pattern='\n'):
        tmp = utils.drop_spaces_between_linebreaks(s.lstrip(start))
        # text between '\nLessons' and first linebreak:
        before_LB = tmp.split(pattern)[0]
        before_LB_strip = before_LB.strip(' ').strip(':').strip(' ')

        # OK section start means 'learned' or 'learnt' after 'Lessons'
        is_section_start_ok = before_LB_strip.lower() in ['learned', 'learnt']
        if is_section_start_ok:
            return tmp.lstrip(before_LB).lstrip(pattern)
        else:
            return ''

    # LL section ends when we meet several linebreaks at once.
    # With some exceptions.
    def finish_LL_section(self, s, stop='\n\n\n'):
        s2 = utils.drop_spaces_between_linebreaks(s)
        s2 = s2.lstrip('\n')    
        ss = s2.split(stop)
        # Often we stop at the first LBs
        output = ss[0]
        if len(ss)==1: #(especially if there's nothing after it)
            return output
        else:
            # remove empty splits
            ss = [s for s in ss if s!='']

        # This gives us the bullet type at the start (or '' if starts not with a bullet)
        bullet = utils.starts_with_bullet(ss[0])

        for i in range(1,len(ss)):
            if bullet != '':
                # if LL section started with a bullet
                if utils.starts_with_bullet(ss[i], bullets=[bullet]) != '' :
                    # if we meet the same bullet, it must be continuation of LL section
                    output += stop + ss[i] 
                    continue 
            after_stop_before_LB = ss[i].split('\n')[0]
            # LL section is sometimes divided into subsections with typical title
            if utils.strip_all_empty(after_stop_before_LB) == 'Recommendations':
                # we skip this title word and continue LL section
                skip_symbols = len(after_stop_before_LB)
                output = output + stop + ss[i][skip_symbols:]
                continue
            # If ends with ':', it's not the end of LL section
            if utils.strip_all_empty(output, left=False).endswith(":"):
                output += stop + ss[i] 
                continue 

            break # if no special reason to continue, then we stop LL section 

        # Should stop at least at Challenge section 
        # (if we came that far, it is a sign that LL section must be shortened even more)
        output = output.split('\nChallenges')[0] 
        return output


    # Splits CH (or LL) section into separate CHs, and cleans 
    def split_and_clean_CHLL(self, chs):
        # Strip away extra symbols
        chs = [(ch[0], utils.strip_all_empty(ch[1])) for ch in chs] 
        
        # Remove what looks like an image caption
        chs = [(ch[0], utils.drop_image_caption(ch[1])) for ch in chs] 

        # Split into challenges (based mainly on double-linebreaks)
        chs = utils.split_list_by_separator(chs)
        chs = [(ch[0], utils.strip_all(ch[1])) for ch in chs] 

        # Remove "N/A" etc indicating absence of challenges
        chs = [ch for ch in chs if not utils.skip_ch(ch[1])]

        # Remove too short ones
        chs = [ch for ch in chs if len(ch[1])>5]

        # Remove linebreaks (only single linbreaks are left)
        chs = [(ch[0], ch[1].replace('\n','')) for ch in chs]

        # Remove double spaces
        chs = [(ch[0], ch[1].replace('  ',' ').replace('  ',' ')) for ch in chs]
        return chs  

    # In some cases a multiple linebreak means the end
    # of Challenge section, e.g. if it contains 
    # only "N/A-like" text
    def stop_at_multiple_LBs(self, s0, stop='\n\n\n\n\n'):
        s = utils.drop_spaces_between_linebreaks(s0)
        i = s.find(stop)
        if i<0: # 'stop' was not found
            return False
        s_before = s.split(stop)[0]
        s_after = s.split(stop)[1].split('\n\n')[0]
        NA_challenge = skip_ch(utils.strip_all_empty(s_before))
        other_section_after = utils.strip_all_empty(s_after).startswith('Strategies for Implementation') 
        #TODO: add other section names e.g. Health, see CU006
        return NA_challenge or other_section_after


    # If we have a list item with only capital letters,
    # this element and all sunsequent elements are excluded
    # (capital letters means it's a section title rather than LL)
    def stop_at_capital(self, lls):
        lls_new = []
        for ll in lls:
            if ll[1].upper() == ll[1]:
                break
            lls_new.append(ll)
        return lls_new