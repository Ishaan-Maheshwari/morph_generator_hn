import sys
import re
import subprocess
import constant
from wxconv import WXC


def log(mssg, logtype = 'OK'):
    '''Generates log message in predefined format.'''
    print(f'[{logtype}] : {mssg}')

def clean(word, inplace = ''):
    '''Clean concept words by removing numbers and special characters from it.'''
    clword = re.sub(r'[^a-zA-Z]+', inplace, word)
    return clword

def has_tam_ya():
    '''Check if USR has verb with TAM "yA"'''
    global HAS_TAM
    if HAS_TAM == True:
        return True
    else:
        return False

def getDataByIndex(value:int, searchList:list, index = 0):
    '''search and return data by index in an array of tuples.
        Index should be first elememt of tuples.
        Return False when index not found.'''
    try:
        for dataele in searchList:
            if dataele[index] == value:
                return dataele
    except IndexError:
        log(f'Index out of range while searching index:{value} in {searchList}','WARNING')
        return False
    return False

def findValue(value:int, searchList:list, index = 0):
    '''search and return data by index in an array of tuples.
        Index should be first elememt of tuples.
        Return False when index not found.'''
    try:
        for dataele in searchList:
            if value in dataele[index]:
                return (True, dataele)
    except IndexError:
        log(f'Index out of range while searching index:{value} in {searchList}','WARNING')
        return (False, None)
    return (False, None)

def getVerbGNP(tam, depend_data, processed_nouns, processed_pronouns):
    k1exists = False
    k2exists = False
    for cases in depend_data:
        k1exists = (depend_data.index(cases)+1) if 'k1' in cases else k1exists
        k2exists = (depend_data.index(cases)+1) if 'k2' in cases else k2exists
    if k1exists == False:
        log('K1 relation not present in USR. Cannot determine GNP for verb.','ERROR')
        sys.exit()

    searchIndex = k1exists
    searchList = processed_nouns + processed_pronouns
    if tam == 'yA':
        searchIndex = k2exists if k2exists != False else k1exists
    
    casedata = getDataByIndex(searchIndex,searchList)
    if(casedata == False):
        log('Something went wrong. Cannot determine GNP for verb.','ERROR')
        sys.exit()
    return casedata[4], casedata[5], casedata[6]

def read_file(file_path):
    '''Returns array of lines for data given in file'''

    log(f'File ~ {file_path}')
    try:
        with open(file_path, 'r') as file:
            data = file.read().splitlines()
            log('File data read.')
    except FileNotFoundError:
        log('No such File found.', 'ERROR')
        sys.exit()
    return data

def generate_rulesinfo(file_data):
    '''Return list all 10 rules of USR as list of lists'''
    if len(file_data) < 10 :
        log('Invalid USR. USR does not contain 10 lines.','ERROR')
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

    log('Rules Info extracted succesfully fom USR.')
    return [src_sentence, root_words, index_data, seman_data, gnp_data, depend_data, discourse_data, spkview_data, scope_data, sentence_type]

def generate_wordinfo(root_words, index_data, seman_data, gnp_data, depend_data, discourse_data, spkview_data, scope_data):
    '''Generates an array of tuples comntaining word and its USR info.
        USR info word wise.'''
    return list(zip(index_data, root_words, seman_data, gnp_data, depend_data, discourse_data, spkview_data, scope_data))

def extract_tamdict_hin():
    extract_tamdict = []
    try:
        with open(constant.TAM_DICT_FILE,'r') as tamfile:
            for line in tamfile.readlines():
                hin_tam = line.split('  ')[1].strip()
                extract_tamdict.append(hin_tam)
        return extract_tamdict
    except FileNotFoundError:
        log('TAM Dictionary File not found.', 'ERROR')
        sys.exit()

def auxmap_hin(aux_verb):
    '''Finds auxillary verb in auxillary mapping file. Returns its root and tam.'''
    try:
        with open(constant.AUX_MAP_FILE,'r') as tamfile:
            for line in tamfile.readlines():
                aux_mapping = line.strip().split(',')
                if aux_mapping[0] == aux_verb :
                    return aux_mapping[1], aux_mapping[2]
        log(f'"{aux_verb}" not found in Auxillary mapping.', 'WARNING')
        return False
    except FileNotFoundError:
        log('Auxillary Mapping File not found.', 'ERROR')
        sys.exit()

def check_noun(word_data):
    '''Check if word is a noun by the USR info'''
    try:
        if word_data[3] != '':
            return True
        return False
    except IndexError:
        log(f'Index Error for GNP Info. Checking noun for {word_data[1]}','ERROR')
        sys.exit()

def check_pronoun(word_data):
    '''Check if word is a pronoun by the USR info'''
    try:
        if word_data[1] in ('addressee', 'speaker', 'vaha', 'kOna_1', 'kyA_1'):
            return True
        elif 'coref' in word_data[5]:
            return True
        else:
            return False
    except IndexError:
        log(f'Index Error for GNP Info. Checking pronoun for {word_data[1]}','ERROR')
        sys.exit()

def check_adjective(word_data):
    '''Check if word is an adjective by the USR info'''
    if word_data[4] != '':
        rel = word_data[4].strip().split(':')[1]
        if rel in ('card','mod','meas','ord','intf'):
            return True
    return False

def check_verb(word_data):
    '''Check if word is a verb by the USR info'''
    if '-' in word_data[1]:
        rword = word_data[1].split('-')[0]
        if rword in extract_tamdict_hin() :
            return True
        else:
            log(f'Verb "{rword}" not found in TAM dictionary','WARNING')
            return True
    return False

def check_indeclinable(word_data):
    '''Check if word is in indeclinable word list'''
    indeclinable_words = (
        'waWA,Ora,paranwu,kinwu,evaM,waWApi,Bale hI,'
        'wo,agara,magara,awaH,cUMki,cUzki,jisa waraha,'
        'jisa prakAra,lekina,waba,waBI,yA,varanA,anyaWA,'
        'wAki,baSarweM,jabaki,yaxi,varana,paraMwu,kiMwu,'
        'hAlAzki,hAlAMki,va,Aja'
    )
    indeclinable_list = indeclinable_words.split(",")
    if clean(word_data[1]) in indeclinable_list :
        return True
    return False

def analyse_words(words_list):
    '''Checks word for its type to process accordingly.'''
    indeclinables = []
    pronouns = []
    nouns = []
    adjectives = []
    verbs = []
    others = []
    for word_data in words_list:
        if check_indeclinable(word_data):
            log(f'{word_data[1]} identified as indiclinable.')
            indeclinables.append(word_data)
        elif check_pronoun(word_data):
            log(f'{word_data[1]} identified as pronoun.')
            pronouns.append(word_data)
        elif check_noun(word_data):
            log(f'{word_data[1]} identified as noun.')
            nouns.append(word_data)
        elif check_adjective(word_data):
            log(f'{word_data[1]} identified as adjective.')
            adjectives.append(word_data)
        elif check_verb(word_data):
            log(f'{word_data[1]} identified as verb.')
            verbs.append(word_data)
        else:
            log(f'{word_data[1]} identified as other word.')
            others.append(word_data)
    return indeclinables,pronouns,nouns,adjectives,verbs,others

def process_indeclinables(indeclinables):
    '''Processes indeclinable words'''
    processed_indeclinables = []
    for indec in indeclinables:
        processed_indeclinables.append( (indec[0],clean(indec[1]),'indec') )
    return processed_indeclinables

def process_others(other_words):
    '''Process other words'''
    processed_others = []
    for word in other_words:
        processed_others.append( (word[0], clean(word[1]), 'other') )
    return processed_others

def extract_gnp(gnp_info):
    '''Extract GNP info in (gender,number,person) format.'''
    gnp_data = gnp_info.strip('][').split(' ')
    if len(gnp_data) != 3:
        return 'm','s',''
    gender = 'm' if gnp_data[0].lower(
        ) == 'm' else 'f' if gnp_data[0].lower() == 'f' else 'm'
    number = 's' if gnp_data[1].lower(
        ) == 'sg' else 'p' if gnp_data[1].lower() == 'pl' else 's'
    person = '' if gnp_data[2] in ('-','') else gnp_data[2]

    return gender,number,person

def process_pronouns(pronouns):
    '''Process pronouns as (index, word, category, case, gender, number, person, parsarg)'''
    processed_pronouns = []
    for pronoun in pronouns:
        category = 'p'
        case = 'o'
        parsarg = 0
        gender, number, person = extract_gnp(pronoun[3])
        if "k1" in pronoun[4]:
            if clean(pronoun[1]) in ('kOna','kyA') and pronoun[2] in ('anim','per'):
                case = "d"
        else :
            if "k2" in pronoun[4] and pronoun[2] in ('anim','per'):
                case = 'd'
        if pronoun[1] == 'addressee':
            addr_map = {'respect':'Apa', 'informal':'wU'}
            word = addr_map.get(pronoun[6].strip().lower(), 'wuma')
        elif pronoun[1] == 'speaker' :
            word = 'mEM'
        elif pronoun[1] == 'vaha' :
            word = 'vaha'
        else:
            word = clean(pronoun[1])
        processed_pronouns.append( (pronoun[0], word, category, case, gender, number, person, parsarg) )
        log(f'{pronoun[1]} processed as pronoun with case:{case} par:{parsarg} gen:{gender} num:{number} per:{person}')
    return processed_pronouns

def process_nouns(nouns):
    '''Process nouns as (index, word, category, case, gender, number)'''
    processed_nouns = []
    for noun in nouns:
        category = 'n'
        case = 'o'
        gender, number, person = extract_gnp(noun[3])
        # if noun[1] == "kiwAba_1":
        #     gender = 'f'
        if "k1" in noun[4]:
                case = "d" 
        else :
            if "k2" in noun[4] and 'anim' not in noun[2]:
                case = 'd'
        processed_nouns.append( (noun[0], clean(noun[1]), category, case, gender, number, person) )
        log(f'{noun[1]} processed as noun with case:{case} gen:{gender} num:{number}.')
    return processed_nouns

def process_adjectives(adjectives, processed_nouns):
    '''Process adjectives as (index, word, category, case, gender, number)'''
    processed_adjectives = []
    
    for adjective in adjectives:
        relnoun = int(adjective[4].strip().split(':')[0])
        relnoun_data = getDataByIndex(relnoun, processed_nouns)
        category = 'adj'
        if relnoun_data == False:
            log(f'Associated Noun not found for adjective {adjective[1]}.','ERROR')
            sys.exit()
        case = relnoun_data[3]
        gender = relnoun_data[4]
        number = relnoun_data[5]

        processed_adjectives.append( (adjective[0],clean(adjective[1]),category,case,gender,number) )
        log(f'{adjective[1]} processed as an adjective with case:{case} gen:{gender} num:{number}')
    return processed_adjectives

def process_verbs(verbs, depend_data, processed_nouns, processed_pronouns):
    '''Process verbs as (index, word, category, gender, number, person, tam)'''
    processed_verbs = []
    processed_auxverbs = []
    aux_verbs = []
    for verb in verbs:
        category = 'v'
        v = verb[1].split('-')
        root = v[0]
        w = v[1].split('_')
        tam = w[0]
        for aux in w[1:]:
            if aux.isalpha():
                aux_verbs.append(aux)
        gender, number, person = getVerbGNP(tam, depend_data, processed_nouns, processed_pronouns)
        processed_verbs.append( (verb[0],clean(root),category,gender,number,person,tam) )
        log(f'{root} processed as verb with gen:{gender} num:{number} per:{person} tam:{tam}')
        for i in range(len(aux_verbs)):
            aux_info = auxmap_hin(aux_verbs[i])
            if aux_info != False:
                aroot, atam = aux_info
                gender, number, person = getVerbGNP(tam, depend_data, processed_nouns, processed_pronouns)
                aindex = verb[0] + ((i+1)*0.1)
                processed_auxverbs.append( (aindex,clean(aroot),category,gender,number,person,atam) )
                log(f'{aroot} processed as auxillary verb with gen:{gender} num:{number} per:{person} tam:{atam}')
    return processed_verbs,processed_auxverbs

def collect_processed_data(processed_pronouns,processed_nouns,processed_adjectives,processed_verbs,processed_auxverbs):
    '''collect sort and return processed data.'''
    return sorted(processed_pronouns+processed_nouns+processed_adjectives+processed_verbs+processed_auxverbs)

def generate_input_for_morph_generator(input_data):
    """Process the input and generate the input for morph generator"""
    morph_input_data = []
    for data in input_data:
        if data[2] == 'p':
            morph_data = f'^{data[1]}<cat:{data[2]}><case:{data[3]}><parsarg:{data[7]}><gen:{data[4]}><num:{data[5]}><per:{data[6]}>$'
        elif data[2] == 'n' :
            morph_data = f'^{data[1]}<cat:{data[2]}><case:{data[3]}><gen:{data[4]}><num:{data[5]}>$'
        elif data[2] == 'v' :
            morph_data = f'^{data[1]}<cat:{data[2]}><gen:{data[3]}><num:{data[4]}><per:{data[5]}><tam:{data[6]}>$'
        elif data[2] == 'adj':
            morph_data = f'^{data[1]}<cat:{data[2]}><case:{data[3]}><gen:{data[4]}><num:{data[5]}>$'
        elif data[2] == 'indec':
            pass
        else:
            morph_data = f'^{data[1]}$'
        morph_input_data.append(morph_data)
    return morph_input_data

def write_data(writedata):
    """Write the Morph Input Data into a file"""
    final_input = " ".join(writedata)
    with open("morph_input.txt", 'w', encoding="utf-8") as file:
        file.write(final_input + "\n")
    return "morph_input.txt"

def run_morph_generator(input_file):
    """ Pass the morph generator through the input file"""
    fname = f'{input_file}-out.txt'
    f = open(fname,'w')
    subprocess.run(f"sh ./run_morph-generator.sh {input_file}",stdout = f, shell=True)
    return "morph_input.txt-out.txt"


def generate_morph():
    '''Run Morph generator'''
    morph_input = generate_input_for_morph_generator(processed_words)
    MORPH_INPUT_FILE = write_data(morph_input)
    OUTPUT_FILE = run_morph_generator(MORPH_INPUT_FILE)
    return OUTPUT_FILE

def read_output_data(output_file):
    """Check the output file data for post processing"""

    with open(output_file, 'r') as file:
        data = file.read()
    return data

def analyse_output_data(output_data, morph_input):
    output_data = output_data.strip().split(" ")
    combine_data = []
    # combine_data = list(zip(output_data, morph_input))
    for i in range(len(output_data)):
        morph_input_list = list(morph_input[i])
        morph_input_list[1] = output_data[i]
        # morph_input[i] = tuple(morph_input_list)
        combine_data.append(tuple(morph_input_list))
    return combine_data

def join_indeclinables(transformed_data, processed_indeclinables, processed_others):
    '''Joins Indeclinable data with transformed data and sort it by index number.'''
    return sorted(transformed_data + processed_indeclinables + processed_others)

def process_postposition(transformed_fulldata, words_info,processed_verbs):
    '''Adds postposition to words wherever applicable according to rules.'''
    PPFulldata = []
    
    for data in transformed_fulldata:
        if data[2] not in ('p','n','other'):
            PPFulldata.append(data)
            continue
        data_info = getDataByIndex(data[0], words_info)
        try:
            data_case = False if data_info == False else data_info[4].split(':')[1].strip()
        except IndexError:
            data_case = False
        data = list(data)
        ppost = ''
        if data_case in ('k1','pk1') :
            if findValue('yA', processed_verbs, index=6)[0] : #has TAM "yA"
                if findValue('k2',words_info,index=4)[0] or findValue('k2p',words_info,index=4)[0]:
                    ppost = 'ne'
        elif data_case in ('k3','k5'):
            ppost = 'se'
        elif data_case in ('k4','k7t','jk1'):
            ppost = 'ko'
        elif data_case in ('k7','k7p'):
            ppost = 'meM'
        elif (data_case == 'k2') and data_info[2] in ("anim", "per"):
            ppost = 'ko'
        else:
            pass
        if data[2] == 'p' :
            data[7] = ppost if ppost != '' else 0
        if data[2] == 'n' or data[2] == 'other':
            data[1] = data[1] + ' ' + ppost
        PPFulldata.append(tuple(data))
    return PPFulldata

def rearrange_sentence(fulldata):
    '''Function comments'''
    finalData = sorted(fulldata)
    final_words = [x[1].strip() for x in finalData]
    print(final_words)
    return " ".join(final_words)

def collect_hindi_output(source_text):
    """Take the output text and find the hindi text from it."""

    hindi_format = WXC(order="wx2utf", lang="hin")
    generate_hindi_text = hindi_format.convert(source_text)
    return generate_hindi_text

def write_hindi_text(hindi_output, POST_PROCESS_OUTPUT, OUTPUT_FILE):
    """Append the hindi text into the file"""
    with open(OUTPUT_FILE, 'w') as file:
        file.write(POST_PROCESS_OUTPUT)
        file.write('\n')
        file.write(hindi_output)
        log('Output data write successfully')
    return "Output data write successfully"

def write_hindi_test(hindi_output, POST_PROCESS_OUTPUT, src_sentence, OUTPUT_FILE, path):
    """Append the hindi text into the file"""
    OUTPUT_FILE = 'TestResults.txt' #temporary for presenting
    with open(OUTPUT_FILE, 'a') as file:
        file.write(path.strip('verified_sent/')+',')
        file.write(src_sentence.strip('#')+',')
        file.write(POST_PROCESS_OUTPUT+',')
        file.write(hindi_output)
        file.write('\n')
        log('Output data write successfully')
    return "Output data write successfully"