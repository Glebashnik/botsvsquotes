# -*- coding: utf-8 -*-

from scorer import gensim_similarity_score_full
import utils
from cards import io
from os import path
import operator
import re
import numpy as np
from gensim.models import Word2Vec



class Contribution(object):
    
    def __init__(self, traind_model, quote_context, quote_filler, player_name, player_data):
        self.trained_model = traind_model
        self.quote_context = quote_context
        self.quote_filler = quote_filler
        self.player_ref = player_name
        self.player_data_set = player_data


    def score_contributions(self):
        
        return gensim_similarity_score_full(
                                            (
                                             self.quote_context, 
                                             self.quote_filler
                                             ),
                                            self.player_data_set,
                                            self.trained_model
                                            )

    

    def humourise(self, scored_contributions):
        
        """
        Structure of dictionary entries of scored constributions:
         (
          (quoter's sentence context, player's sentence context), 
          (quoter's sentence filler, player's sentence filler), 
          score
         )
        """
        
        plyrs_scores_dict = {}

        (ctxts,fills)  = scored_contributions

        for c_k,c_v in ctxts.items():
            for f_k,f_v in fills.items():
                    tmp_res = (c_v - f_v)
                    if isinstance(tmp_res, np.ndarray):
                        tmp_res = np.ndarray.mean(tmp_res)
                        if tmp_res == np.nan:
                            tmp_res = 0.0
                    else:
                        tmp_res = np.float64(tmp_res)
                    plyrs_scores_dict[(c_k,f_k)] = tmp_res


        # Sort dictionary
        plyrs_scores_dict = sorted(plyrs_scores_dict.items(), key=operator.itemgetter(1), reverse=True)
        # Select topmost result 
        res = plyrs_scores_dict[0]
        # Select only player's filler
        res = res[0][1][1]
        # Do some final NLP-related adjustments to the output form (e.g. fixing case of pronoun)
        res = utils.Surface_Tweaker(res, self.quote_context, self.quote_filler).make_filler()

        return res

    
#    def printer(self, contrs_object):
#        print "Quoter:",self.quoter_dict["name"]
#        print "Context:",self.quoter_dict["context"]
#        for contr in contrs_object.items():
#            print "\nPlayer contexts:"
#            for k,v in contr[1][0].items():
#                print k[1],"=",v
#            print "\nPlayer fills:"
#            for k,v in contr[1][1].items():
#                print k[1],"=",v



if __name__ == '__main__':
    
    #player_type = "fictional"
    #quoter_type = "real"
    
    player_name = "Coco Chanel"
    cards_data = "E:\\Dropbox\\Code\\eclipse-workspace-luna\\botsvsquotes\\cards\\data\\"
    player_cards = io.load_character_cards(player_name, path=cards_data)
    
    quoter_dict = {
              "name": "Darth Vader",
              "context":"Don't underestimate the power of _", 
              "filler":"the Force"}
    
    # Load data
    black_cards_list = [c.black_string() for c in player_cards]
    white_cards_list = [c.white_string() for c in player_cards]
    #black_cards_pth = path.join("E:\\Dropbox\\Data\\ProseccoCodeCamp", "fictional_black_cards.json")
    #white_cards_pth = path.join("E:\\Dropbox\\Data\\ProseccoCodeCamp", "fictional_white_cards.json")
    #black_cards_dict = json.load(open(black_cards_pth, "r"))
    #white_cards_dict = json.load(open(white_cards_pth, "r"))
    data_set = zip(black_cards_list, white_cards_list)
    
    # Load models
    trained_medium_model_path = path.join("E:\Dropbox\Data\WordVecModels","w2v_103.model")
    trained_medium_model = Word2Vec.load(trained_medium_model_path)
    #trained_big_model_path = path.join("E:\Dropbox\Data\WordVecModels","1-billion-word-language-modeling-benchmark-r13output.bin.gz")
    #trained_big_model = Word2Vec.load_word2vec_format(trained_big_model_path, binary=True)

    # Taking care of sparse data problems, by retraining model to include sentences from player's data set.
    #
    ## Warning from http://radimrehurek.com/2014/02/word2vec-tutorial/:
    ## "Note that it’s not possible to resume training with models generated by the C tool, 
    ## load_word2vec_format(). You can still use them for querying/similarity, but information 
    ## vital for training (the vocab tree) is missing there." 
    #
    # 1. Construct list of sentences
    data_set_sentences_list = [
                           re.compile("[.!?]").split(re.sub("_+", j, i))
                           for i,j in data_set
                          ]
    # 2. Flatten this list, and remove duplicates    
    data_set_sentences_list[:] = list(set(l.strip().lower() for lst in data_set_sentences_list for l in lst if l))
    # 3. Retrain model to include player's sentences
    trained_medium_model.train(data_set_sentences_list)
            
    # Collect scores for player's contributions vs. quoter's context and filler
    contrs = Contribution(trained_medium_model, quoter_dict["context"], quoter_dict["filler"], player_name, data_set)
    scored_constributions = contrs.score_contributions()

    # Print results
    #contrs.printer(test_quoter, scoring_results)

    # Humourise
    print quoter_dict["name"],"poses the quote:",quoter_dict["context"]
    print player_name,"replies with:",contrs.humourise(scored_constributions)

    