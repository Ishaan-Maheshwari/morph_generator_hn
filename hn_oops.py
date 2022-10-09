import re
import sys
from typing import List,Type


class Dependence:
    def __init__(self,depStr):
        assert ':' in depStr, 'Parameter given is not properly formatted.'

        d = depStr.split(':')
        self.atIndex = d[0]
        self.name = d[1]
    
    def default_postposition(self):
        #TODO: Provide implementation for calculating default pp.
        pass

    def get_postposition(self):
        return '0'

class DiscourseElement:
    def __init__(self, disstr):
        assert ':' in disstr, 'Parameter given is not properly formatted.'

        d = disstr.strip().split(':')
        self.name = d[1]
        self.atIndex = d[0]

class POS:

    @classmethod
    def clean(cls,rawword):
        return rawword
    
    @classmethod
    def create_pos(cls,word_data:List):
        raw_pos = POS(word_data)
        if Indeclinables.check(raw_pos) :
            return Indeclinables(word_data)
        elif Pronoun.check(raw_pos):
            return Pronoun(word_data)
        elif Noun.check(raw_pos):
            return Noun(word_data)
        elif Adjective.check(raw_pos):
            return Adjective(word_data)
        elif Verb.check(raw_pos):
            return Verb(word_data)
        else:
            return Other(word_data)

    def __init__(self,word_data:List):
        self.raw_concept = word_data[0]
        self.concept = POS.clean(word_data[0])
        self.index = int(word_data[1])
        self.semantic = word_data[2]
        gnp_info = word_data[3].strip('][').split(' ') if word_data[3] != '' else None
        if gnp_info != None and len(gnp_info) == 3 :
            self.gender = gnp_info[0]
            self.number = gnp_info[1]
            self.person = gnp_info[2]
        else:
            self.gender = self.number = self.person = None
        self.dependency = Dependence(word_data[4]) if word_data[4] != '' else None
        if word_data[5] != '':
            self.discourse = DiscourseElement(word_data[5])
        else:
            self.discourse = None
    
    def generate_morph_input(self):
        return f"{self.concept}"


class Sentence:

    def __init__(self,type="affirmative"):
        self.type = type
    
    def __init__(self,pos:Type[POS],type="affirmative"):
        self.__init__(self,type)
        self.words = [pos]
    
    def __init__(self,pos_list:List,type="affirmative"):
        self.__init__(self,type)
        self.words = pos_list
        self.sort()
    
    def getwordByIndex(self,index:int):
        for word in self.words :
            if word.index == index :
                return word
        return None

    def sort(self):
        #sort words according to index number
        pass

    def add_words(self,new_pos:Type[POS]):
        self.words.append(new_pos)
        self.sort()

class Noun(POS):

    @classmethod
    def check(cls,posobj:POS):
        '''Check if word is a noun by the USR info'''
        if posobj.gender != None or posobj.number != None or posobj.person != None :
            return True
        else:
            return False

    def __init__(self,word_data:Type[List]):
        super().__init__(word_data)
        self.category = "n"
        self.IsProper = False
        self.case = 'o'
        if re.search("_[0-9]",self.raw_concept) is None :
            self.IsProper = True
    
    def process_case(self):
        if self.dependency.name == 'k1':
            self.case = 'd'
        elif self.dependency.name == 'k2' and self.semantic != 'anim' :
            self.case = 'd'
        else:
            self.case = 'o'

    def process(self):
        self.process_case(self)
        pass

    def generate_morph_input(self):
        if self.IsProper:
            instr = f"{self.concept}"
        else:
            instr = f"^{self.concept}<cat:{self.case}><case:{self.case}><gen:{self.gender}><num:{self.number}>$"
        return instr

class Pronoun(POS):

    @classmethod
    def check(cls,posobj:POS):
        '''check if word is a pronoun by the USR info.'''
        if posobj.concept in ('addressee', 'speaker','kyA', 'Apa', 'jo', 'koI', 'kOna', 'mEM', 'saba', 'vaha', 'wU', 'wuma', 'yaha'):
            return True
        elif posobj.discourse != None:
            if posobj.discourse.name == 'coref' :
                return True
        else:
            return False
    
    def __init__(self,word_data):
        super().__init__(word_data)
        self.category = "p"
        self.fnum = None
        self.case = 'o'
    
    def generate_morph_input(self):
        if self.fnum != None :
            instr = f"^{self.concept}<cat:{self.category}><parsarg:{self.parsarg}><fnum:{self.fnum}><case:{self.case}><gen:{self.gender}><num:{self.number}><per:{self.number}>$"
        else:
            instr = f"^{self.concept}<cat:{self.category}><case:{self.case}><parsarg:{self.dependency.get_postposition()}><gen:{self.gender}><num:{self.number}><per:{self.number}>$"
        
        return instr

class Adjective(POS):

    @classmethod
    def check(cls,posobj:POS):
        if posobj.dependency.name in ('card','mod','meas','ord','intf'):
            return True
        return False

    def __init__(self,word_data):
        super().__init__(word_data)
        self.category = "adj"
    
    def generate_morph_input(self):
        return f"^{self.concept}<cat:{self.case}><case:{self.case}><gen:{self.gender}><num:{self.number}>$"

class Verb(POS):
    
    @classmethod
    def check(cls,posobj:POS):
        if '-' in posobj.raw_concept:
            #Check root word in TAM dictionary
            return True
        return False

    def __init__(self,word_data):
        super().__init__(word_data)
        self.category = "v"
        #calculate tam
        #calculate auxillary verbs

    def generate_morph_input(self):
        return f"{self.concept}" #Todo

class Other(POS):

    @classmethod
    def check(cls,raw_pos:POS):
        if Indeclinables.check(raw_pos) :
            return False
        elif Pronoun.check(raw_pos):
            return False
        elif Noun.check(raw_pos):
            return False
        elif Adjective.check(raw_pos):
            return False
        elif Verb.check(raw_pos):
            return False
        else:
            return True

    def __init__(self,word_data):
        super().__init__(word_data)
        self.category = "other"
    
    def generate_morph_input(self):
        return f"{self.concept}" 

class Indeclinables(POS):

    @classmethod
    def check(cls,posobj:POS):
        indeclinable_words = (
            'waWA,Ora,paranwu,kinwu,evaM,waWApi,Bale hI,'
            'wo,agara,magara,awaH,cUMki,cUzki,jisa waraha,'
            'jisa prakAra,lekina,waba,waBI,yA,varanA,anyaWA,'
            'wAki,baSarweM,jabaki,yaxi,varana,paraMwu,kiMwu,'
            'hAlAzki,hAlAMki,va,Aja'
        )
        indeclinable_list = indeclinable_words.split(",")
        if posobj.concept in indeclinable_list :
            return True
        return False

    def __init__(self,word_data:List):
        super().__init__(word_data)
        self.category = "indec"
    
    def generate_morph_input(self):
        return f"{self.concept}" 

class Compounds(POS):
    pass

def read_file(file_path):
    '''Returns array of lines for data given in file'''

    try:
        with open(file_path, 'r') as file:
            data = file.read().splitlines()

    except FileNotFoundError:
        sys.exit()
    return data

def generate_rulesinfo(file_data):
    '''Return list all 10 rules of USR as list of lists'''
    if len(file_data) < 10 :
        sys.exit()
    
    src_sentence = file_data[0]
    root_words = file_data[1].strip().split(',')
    index_data = file_data[2].strip().split(',')
    seman_data = file_data[3].strip().split(',')
    gnp_data = file_data[4].strip().split(',')
    depend_data = file_data[5].strip().split(',')
    discourse_data = file_data[6].strip().split(',')
    spkview_data = file_data[7].strip().split(',')
    scope_data = file_data[8].strip().split(',')
    sentence_type = file_data[9].strip()

    return [src_sentence, root_words, index_data, seman_data, gnp_data, depend_data, discourse_data, spkview_data, scope_data, sentence_type]

def generate_wordinfo(root_words, index_data, seman_data, gnp_data, depend_data, discourse_data, spkview_data, scope_data):
    '''Generates an array of tuples comntaining word and its USR info.
        USR info word wise.'''
    return list(zip(root_words,index_data, seman_data, gnp_data, depend_data, discourse_data, spkview_data, scope_data))


if __name__ == "__main__":
    
    try:
        path = sys.argv[1]
    except IndexError:
        sys.exit()
    
    file_data = read_file(path)
    rules_info = generate_rulesinfo(file_data)
    #Extracting Information
    src_sentence = rules_info[0]
    root_words = rules_info[1]
    index_data = [int(x) for x in rules_info[2]]
    seman_data = rules_info[3]
    gnp_data = rules_info[4]
    depend_data = rules_info[5]
    discourse_data = rules_info[6]
    spkview_data = rules_info[7]
    scope_data = rules_info[8]
    sentence_type = rules_info[9]
    
    words_info = generate_wordinfo(root_words, index_data, seman_data, 
                    gnp_data, depend_data, discourse_data, spkview_data, scope_data)
    print(words_info)
    for word_data in words_info:
        mypos = POS.create_pos(list(word_data))
        print(type(mypos))
        print(vars(mypos))
        print(mypos.category)
        if mypos.category == 'n' :
            print(mypos.generate_morph_input())
