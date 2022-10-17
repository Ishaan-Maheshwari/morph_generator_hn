import sys
from common import *

if __name__ == "__main__":
    import doctest
    doctest.testmod()
    
    log("Program Started", "START")
    try:
        path = sys.argv[1]
    except IndexError:
        log("No argument given. Please provide path for input file as an argument.", "ERROR")
        sys.exit()
    
    file_data = read_file(path)
    rules_info = generate_rulesinfo(file_data)
    run_test()
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
    indeclinables_data,pronouns_data,nouns_data,adjectives_data,verbs_data,others_data = analyse_words(words_info)
    
    #Pre-Processing
    processed_indeclinables = process_indeclinables(indeclinables_data)
    processed_nouns = process_nouns(nouns_data)
    processed_pronouns = process_pronouns(pronouns_data,processed_nouns)
    processed_adjectives = process_adjectives(adjectives_data, processed_nouns)
    processed_others = process_others(others_data)
    processed_verbs, processed_auxverbs, processed_others = process_verbs(verbs_data, depend_data, processed_nouns, processed_pronouns,processed_others)
    print(processed_verbs, processed_auxverbs)
    #Todo : extract nouns / adjectives from verbs with +
    processed_pronouns,_ = preprocess_postposition(processed_pronouns, words_info, processed_verbs)
    print(processed_pronouns)
    #Todo : process nouns / adjectives got from verbs and add to processed_noun / processed_adjectives
    processed_words = collect_processed_data(processed_pronouns,processed_nouns,processed_adjectives,
                                            processed_verbs,processed_auxverbs,processed_indeclinables,processed_others)
    processed_words,processed_postpositions = preprocess_postposition(processed_words, words_info,processed_verbs)
    OUTPUT_FILE = generate_morph(processed_words)

    #Pre-processing(2) for ungenerated data
    outputData = read_output_data(OUTPUT_FILE)
    print(processed_nouns)
    has_changes,processed_nouns = handle_unprocessed(outputData, processed_nouns)
    print(processed_nouns)
    if has_changes:
        #Reprocessing adjectives and verbs based on new noun Info
        processed_adjectives = process_adjectives(adjectives_data, processed_nouns)
        processed_verbs, processed_auxverbs, processed_others = process_verbs(verbs_data, depend_data, processed_nouns, processed_pronouns, processed_others, re = True)
        processed_words = collect_processed_data(processed_pronouns,processed_nouns,processed_adjectives,processed_verbs,processed_auxverbs,processed_indeclinables,processed_others)
        OUTPUT_FILE = generate_morph(processed_words)
    
    #Post-Processing
    print("Line after post processing start")
    outputData = read_output_data(OUTPUT_FILE)
    transformed_data = analyse_output_data(outputData, processed_words)
    # transformed_fulldata = join_indeclinables(transformed_data, processed_indeclinables, processed_others)
    # PP_fulldata = process_postposition(transformed_data, words_info, processed_verbs)
    transformed_data = join_compounds(transformed_data)
    PP_fulldata = add_postposition(transformed_data,processed_postpositions)
    POST_PROCESS_OUTPUT = rearrange_sentence(PP_fulldata)
    hindi_output = collect_hindi_output(POST_PROCESS_OUTPUT)
    write_hindi_text(hindi_output, POST_PROCESS_OUTPUT, OUTPUT_FILE)
    #write_hindi_test(hindi_output, POST_PROCESS_OUTPUT, src_sentence, OUTPUT_FILE, path)
