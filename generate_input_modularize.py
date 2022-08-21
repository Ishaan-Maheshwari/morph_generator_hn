"""
This module is related to the NLP.
It generates the input for morph generator.
Pass the input through morph genetor to collect output.
Collect the Hindi text from the output text
Write the output data into a file.
"""


from logging import root
import sys
import re
import subprocess
from xmlrpc.client import FastMarshaller


from wxconv import WXC


def read_file(file_path):
    """Read data from text file"""

    with open(file_path, 'r') as file:
        data = file.read().splitlines()
    return data


def pre_process(data):
    """Process and Filterize the file data"""

    root_words = data[1]
    index_data = data[2]
    gnp_values = data[4]
    case_data = data[5]
    respect_info = data[7]
    semantic_data = data[3]
    indeclinable_words = (
        '"waWA,Ora,paranwu,kinwu,evaM,waWApi,Bale hI,'
        'wo,agara,magara,awaH,cUMki,cUzki,jisa waraha,'
        'jisa prakAra,lekina,waba,waBI,yA,varanA,anyaWA,'
        'wAki,baSarweM,jabaki,yaxi,varana,paraMwu,kiMwu,'
        'hAlAzki,hAlAMki,va"'
    )
    return (root_words, index_data,
            semantic_data, gnp_values,
            case_data, respect_info,
            indeclinable_words
            )


def process_root_words(words):
    """Put all the root words into a single list"""

    root_words = words.split(",")
    return root_words


def process_index_data(info):
    """Process the index infos"""

    index_data = info.split(",")
    return index_data


def process_semantic_data(words):
    """Put all the semantic data into a single list"""

    semantic_data = words.split(",")
    return semantic_data


def process_gnp_values(words):
    """Put all the gnp values into a single list"""

    gnp_values = words.split(",")
    return gnp_values


def process_case_info(words):
    """Put all the case infos into a single list"""

    case_data = words.split(",")
    return case_data


def process_respect_info(words):
    """Put all the respect infos into a single list"""

    respect_info = words.split(",")
    return respect_info


def process_indeclinable_words(words):
    """Put all the indeclinable words into a single list"""

    indeclinable_words = words.split(",")
    return indeclinable_words

def extract_tamdict_hin():
    extract_tamdict = []
    with open('tam_mapping.dat','r') as tamfile:
        for line in tamfile.readlines():
            hin_tam = line.split('  ')[1].strip()
            extract_tamdict.append(hin_tam)
    return extract_tamdict

def extract_aux_root(aux_word):
    root = tam = ''
    with open('auxillary_mapping.txt','r') as auxfile:
        for line in auxfile.readlines():
            aux_info = line.split(',')
            if aux_info[0] == aux_word :
                root = aux_info[1]
                tam = aux_info[2].replace('\n','')
                break
    if root == '' or tam == '' :
        return False
    else:
        return (root,tam)

def preprocess_verbs(words, index_data):
    """
    Find among all concept_words if it is a verb
    and pass the result as (root,tam) to be processed futher.
    """
    verbs = []
    word_list = words.split(',')
    tam_dict = extract_tamdict_hin()
    for word in range(len(word_list)):
        if '-' in word_list[word]:
            w = word_list[word].split('-')
            if w[1] in tam_dict:
                verbs.append((int(index_data[word]),w[0], w[1]))    #(root_word , tam)
    return verbs

def process_verbs(verblist, case_infos, noun_info_list):
    """
    Todo
    """
    verbs = []
    for verb in verblist :
        index, vroot, vtam = verb
        cat = 'v'
        tams = vtam.split('_')
        gnp_case = 'k1'
        gnp_index = 0
        gender = number = ''
        if tams[0] == 'yA' :
            gnp_case = 'k2'
        for i in range(len(case_infos)):
            if gnp_case in case_infos[i]:
                gnp_index = i+1
        for noun_info in noun_info_list:
            if noun_info[0] == gnp_index :
                gender = noun_info[4]
                number = noun_info[5]
        word = vroot+tams[0]
        clword = re.sub(r'[^a-zA-Z]+', '', word)
        verbs.append((index,clword,cat,tams[0],gender,number))
        if len(tams) > 1:
            for k in range(1,len(tams)):
                #find root , tam
                aux_word = re.sub(r'[^a-zA-Z]', '', tams[k])
                root_tam = extract_aux_root(aux_word)
                if root_tam != False:
                    verbs.append((index+(0.1*k),root_tam[0],cat,root_tam[1],gender,number))
    return verbs

# def process_verb_words_old(words):
#     """
#     Take the verb word from the root words &
#     Filterize it into a proper format"""

#     verb_word = []
#     if '0' in words:
#         words = words.split("_")
#         for char in words:
#             if char.isalpha():
#                 verb_word.append(char)
#     else:
#         res1 = re.sub(r'[^a-zA-Z]', ' ', words).split(" ")
#         for char in res1:
#             if len(char) >= 1:
#                 verb_word.append(char)
#         verb_word = [verb_word[0]+verb_word[1]] + verb_word[2:]
#     return " ".join(verb_word)
def getNextNounId(fromIndex, gnp_value, case_info, index_data):
    index = fromIndex
    for i in range(len(index_data)) :
        if gnp_value[index] != '' and index != fromIndex:
            return index
        else:
            case = case_info[index]
            if ':' not in case :
                return -1
            nextIndex = case.split(':')[0]
            if nextIndex == '0':
                return -1
            else:
                index = int(index_data.index(nextIndex))
    return -1 #return False coinciding with index 0

def checkPostPosition(index, case_info, IS_ANIM, TAM_YA):
    if ':' not in case_info[index]:
        return False
    case = case_info[index].split(':')[1]
    if case in ['k3', 'k4', 'k5', 'k7p', 'k7t' ,'k7', 'r6'] :
        return True
    elif case == 'k1' and IS_ANIM :
        return True
    elif case == 'k2' and TAM_YA :
        return True
    else:
        False
    return False

def handle_noun(root_words, gnp_value, case_info, seman_data, index_data, respect_data, indeclinable_words_info):
    """Look the data from the root words and gnp values to get noun info"""

    noun_info = []
    adj_info = []
    ind_info = []
    for word in range(len(root_words[:(len(gnp_value) - 1)])):
        if root_words[word] in indeclinable_words_info:
            ind_info.append((int(index_data[word]), root_words[word], 'ind'))
            continue
        
        data = gnp_value[word].strip('][').split(' ')
        root_word = (root_words[word].split("_")[0]).strip()
        if len(data) > 1:
            gender = 'm' if data[0].lower(
            ) == 'm' else 'f' if data[0].lower() == 'f' else 'm'
            number = 's' if data[1].lower(
            ) == 'sg' else 'p' if data[1].lower() == 'pl' else 's'
            category = 'n'
            case = 'o'
            if "k1" in case_info[word]:
                case = "d"
            elif "k2" in case_info[word] :
                if 'anim' in seman_data[word]:
                    root_word = root_word + ' ko'  #added for vibhakti
                else:
                    case = 'd'
            elif "k3" in case_info[word] :
                root_word = root_word + ' se'
            elif "k4" in case_info[word] :
                root_word = root_word + ' ko'
            elif "k5" in case_info[word] :
                root_word = root_word + ' se'
            elif "r6" in case_info[word] :
                case = 'o'
                nextNounIndex = getNextNounId(word, gnp_value, case_info, index_data)
                if nextNounIndex != -1 :
                    gnp_nextNoun = gnp_value[nextNounIndex].strip('][').split(' ')
                    if gnp_nextNoun[0] == 'f':
                        root_word = root_word + ' kI'
                    else :
                        is_anim = True if ('anim' in seman_data[nextNounIndex]) else False
                        if checkPostPosition(nextNounIndex, case_info, IS_ANIM = is_anim, TAM_YA = False):
                            root_word = root_word + ' ke'
                        elif gnp_nextNoun[1] == 'pl':
                            root_word = root_word + ' ke'
                        else:
                            root_word = root_word + ' kA'
            elif "k7p" in case_info[word] :
                root_word = root_word + ' meM'
            elif "k7t" in case_info[word] :
                root_word = root_word + ' ko'
            elif "k7" in case_info[word] :
                root_word = root_word + ' meM'
            elif "mk1" in case_info[word] :
                root_word = root_word + ' se'
            elif "jk1" in case_info[word] :
                root_word = root_word + ' ko'
            else:
                pass
            if root_word == 'addressee':
                addr_map = {'respect':'Apa', 'informal':'wU'}
                root_word = addr_map.get(respect_data[word], 'wuma')
                category = 'p'
            elif root_word == 'speaker' :
                spk_map = {'p':'hama', 's':'mEM'}
                root_word = spk_map.get(number,'hama')
                category = 'p'
            else:
                pass
            noun_info.append(
                (int(index_data[word]),
                    root_word, category,
                    case, gender, number))
        else :
            if(case_info[word] != ''):
                dependency_info = case_info[word].split(':')[1]
                if dependency_info in ['card', 'ord', 'mod', 'meas', 'intf'] :
                    adj_info.append( (int(index_data[word]), root_word, case_info[word]) )
            
    return noun_info, adj_info, ind_info


def handle_adjective(adj_list, noun_info):
    """ Look the data from the noun infos
        and collect the adjective information"""
    adj_data = []
    if len(adj_list) >= 1 and len(noun_info) >= 1:
        for data in adj_list:
            index_data = int(data[-1].split(":")[0])
            for noun_data in noun_info:
                if index_data in noun_data:
                    case, gender, number,  = noun_data[3:]
                    adj_data.append(
                        (data[0], data[1], 'adj', case, gender, number))
    return adj_data


def analyze_data(noun_infos, adj_infos, VERB_INFO, ind_list):
    """
    Analyze the data from inputs and filterize it.
    After filterization create the input for morph generator."""
    
    data = noun_infos + adj_infos + VERB_INFO + ind_list
    data.sort()
    return data


def generate_input_for_morph_generator(input_data):
    """Process the input and generate the input for morph generator"""
    morph_input_data = []
    for data in input_data:
        if data[2] == 'ind':
            morph_data = f'^{data[1]}$'
        elif data[2] == 'v' :
            morph_data = f'^{data[1]}<cat:{data[2]}><tam:{data[3]}><gen:{data[4]}><num:{data[5]}>$'
        else:
            morph_data = f'^{data[1]}<cat:{data[2]}><case:{data[3]}><gen:{data[4]}><num:{data[5]}>$'
        morph_input_data.append(morph_data)
    return morph_input_data


def write_data(noun_adj_data):
    """Write the Morph Input Data into a file"""

    final_input = " ".join(noun_adj_data)
    with open("morph_input.txt", 'w', encoding="utf-8") as file:
        file.write(final_input + "\n")
    return "morph_input.txt"


def run_morph_generator(input_file):
    """ Pass the morph generator through the input file"""
    fname = f'{input_file}-out.txt'
    f = open(fname,'w')
    subprocess.run(f"sh ./run_morph-generator.sh {input_file}",stdout = f, shell=True)
    return "morph_input.txt-out.txt"


def read_output_data(output_file):
    """Check the output file data for post processing"""

    with open(output_file, 'r') as file:
        data = file.read()
    return data


def analyze_output_data(output_data, morph_input, adj_infos):
    """Post process the output data if there is some error"""

    output_data = output_data.split(" ")
    combine_data = list(zip(output_data, morph_input))
    adj_name_info = []
    if len(adj_infos) >= 1:
        for name in adj_infos:
            adj_name_info.append(name[1])
    for adj_name in adj_name_info:
        for data in combine_data:
            if "#" in data[0] or adj_name in data[0]:
                new_data = data[1][:4] + \
                    tuple(data[1][4].replace('m', 'f'))+data[1][5:]
                morph_input[morph_input.index(data[1])] = new_data
    return morph_input


def collect_hindi_output(output_text):
    """Take the output text and find the hindi text from it."""

    hindi_format = WXC(order="wx2utf", lang="hin")
    generate_hindi_text = hindi_format.convert(output_text)
    return generate_hindi_text


def write_hindi_text(hindi_text, output_file):
    """Append the hindi text into the file"""

    with open(output_file, 'a') as file:
        file.write(hindi_text)
    return "Output data write successfully"


if __name__ == "__main__":
    path = sys.argv[1]
    file_data = read_file(path)
    (root_words_info, index_data_info,
     semantic_data_info, gnp_values_info,
     case_data_info, respect_infos,
     indeclinable_words_info) = pre_process(file_data)
    root_info = process_root_words(root_words_info)
    index_info = process_index_data(index_data_info)
    semantic_info = process_semantic_data(semantic_data_info)
    gnp_info = process_gnp_values(gnp_values_info)
    case_infos = process_case_info(case_data_info)
    respect_data = process_respect_info(respect_infos)
    indeclinable_words_info = process_indeclinable_words(
        indeclinable_words_info
    )
    verbs = preprocess_verbs(root_words_info,index_info)
    noun_info_list, adj_data_list, ind_list = handle_noun(
        root_info[0:-1], gnp_info, case_infos, semantic_info, index_info, respect_data, indeclinable_words_info)
    VERB_INFO = process_verbs(verbs, case_infos, noun_info_list)
    adj_info_data = handle_adjective(adj_data_list, noun_info_list)
    generate_input_data = analyze_data(noun_info_list, adj_info_data, VERB_INFO, ind_list)
    morph_input_info = generate_input_for_morph_generator(generate_input_data)
    MORPH_INPUT_FILE = write_data(morph_input_info)
    OUTPUT_DATA = run_morph_generator(MORPH_INPUT_FILE)
    read_output = read_output_data(OUTPUT_DATA)
    analyze_output = analyze_output_data(
        read_output, generate_input_data, adj_data_list)
    generate_post_process_input = generate_input_for_morph_generator(
        analyze_output)
    WRITE_POST_OUTPUT = write_data(generate_post_process_input)
    POST_PROCESS_OUTPUT = run_morph_generator(WRITE_POST_OUTPUT)
    read_post_output = read_output_data(POST_PROCESS_OUTPUT)
    hindi_text_info = collect_hindi_output(read_post_output)
    WRITE_HINDI_OUTPUT = write_hindi_text(hindi_text_info, POST_PROCESS_OUTPUT)
    print(WRITE_HINDI_OUTPUT)
