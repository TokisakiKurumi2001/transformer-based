import argparse
import time
import torch
from Models import get_model
from Process import *
import torch.nn.functional as F
from Optim import CosineWithRestarts
from Batch import create_masks
import pdb
import dill as pickle
import argparse
from Models import get_model
from Beam import beam_search
from nltk.corpus import wordnet
from torch.autograd import Variable
import re
import random

def get_synonym(word, SRC):
    syns = wordnet.synsets(word)
    for s in syns:
        for l in s.lemmas():
            if SRC.vocab.stoi[l.name()] != 0:
                return SRC.vocab.stoi[l.name()]
            
    return 0

def multiple_replace(dict, text):
  # Create a regular expression  from the dictionary keys
  regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))

  # For each match, look-up corresponding value in dictionary
  return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text) 

def translate_sentence(sentence, model, opt, SRC, TRG):
    
    model.eval()
    indexed = []
    sentence = SRC.preprocess(sentence)
    for tok in sentence:
        if SRC.vocab.stoi[tok] != 0 or opt.floyd == True:
            indexed.append(SRC.vocab.stoi[tok])
        else:
            indexed.append(get_synonym(tok, SRC))
    sentence = Variable(torch.LongTensor([indexed]))
    if opt.device == 0:
        sentence = sentence.cuda()
    
    sentence = beam_search(sentence, model, SRC, TRG, opt)

    return  multiple_replace({' ?' : '?',' !':'!',' .':'.','\' ':'\'',' ,':','}, sentence)

def translate(opt, model, SRC, TRG):
    sentences = opt.text.lower().split('.')
    translated = []

    for sentence in sentences:
        translated.append(translate_sentence(sentence + '.', model, opt, SRC, TRG).capitalize())

    return (' '.join(translated))

def randomizeTranslate(opt, model, SRC, TRG):
    txtVi = "vi-0203-no-augment-shuffle.txt"
    txtBana = "bana-0203-no-augment-shuffle.txt"
    txtViFile = open('data' + '/' + txtVi, encoding='utf-8', errors='ignore').read()
    txtBanaFile = open('data' + '/' + txtBana, encoding='utf-8', errors='ignore').read()
    splitsVi = txtViFile.split('\n')
    splitsBana = txtBanaFile.split('\n')
    txtViNew = ''
    txtBanaTranslated = ''
    txtBanaNew = ''
    num_rows = len(splitsVi)
    for i in range(200):
        try:
            randNum = random.randint(0, num_rows - 1)
            print('[VI] ' + splitsVi[randNum] + '\n')
            opt.text = splitsVi[randNum]
            phrase = translate(opt, model, SRC, TRG)
            txtBanaTranslated += phrase + '\n'
            txtViNew += splitsVi[randNum] + '\n'
            txtBanaNew += splitsBana[randNum] + '\n'
            print('[BANA] ' + phrase + '\n')
            print('-----------------------------------------')
        except:
            print('An exception occured')
        
    with open('data' + '/test-sentences-vi.txt', 'w', encoding='utf-8') as f:
        f.write(txtViNew)
    with open('data' + '/test-sentences-bana.txt', 'w', encoding='utf-8') as f:
        f.write(txtBanaTranslated)
    with open('data' + '/truth-sentences-bana.txt', 'w', encoding='utf-8') as f:
        f.write(txtBanaNew)

def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-load_weights', required=True)
    parser.add_argument('-k', type=int, default=3)
    parser.add_argument('-max_len', type=int, default=80)
    parser.add_argument('-d_model', type=int, default=512)
    parser.add_argument('-n_layers', type=int, default=6)
    parser.add_argument('-src_lang', required=True)
    parser.add_argument('-trg_lang', required=True)
    parser.add_argument('-heads', type=int, default=8)
    parser.add_argument('-dropout', type=int, default=0.1)
    parser.add_argument('-no_cuda', action='store_true')
    parser.add_argument('-floyd', action='store_true')
    
    opt = parser.parse_args()

    opt.device = 0 if opt.no_cuda is False else -1
 
    assert opt.k > 0
    assert opt.max_len > 10

    SRC, TRG = create_fields(opt)
    model = get_model(opt, len(SRC.vocab), len(TRG.vocab))
    randomizeTranslate(opt, model, SRC, TRG)
    # while True:
    #     opt.text =input("Nhập một câu để dịch: (nhập 'q' để thoát):\n")
    #     if opt.text=="q":
    #         break
    #     phrase = translate(opt, model, SRC, TRG)
    #     print('> '+ phrase + '\n')

if __name__ == '__main__':
    main()