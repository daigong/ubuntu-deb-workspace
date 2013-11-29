#encoding:utf-8 
import re
import os

here = os.path.abspath(os.path.dirname(__file__))

class TrieNode(object):  
    def __init__(self):  
        self.value = None  
        self.children = {}  
  
class Trie(object):  
    def __init__(self):  
        self.root = TrieNode()  
  
    def add(self, key):  
        node = self.root  
        for char in key:  
            if char not in node.children:  
                child = TrieNode()  
                node.children[char] = child  
                node = child  
            else:  
                node = node.children[char]  
        node.value = key  
  
    def search(self, key):  
        node = self.root  
        matches = []  
        matched_length = 0  
        for char in key:  
            if char not in node.children:  
                break  
            node = node.children[char]  
            if node.value:  
                matches.append(node.value)  
        return matches  
  
class ScanPos(object):  
    def __init__(self, pos, token = None, parent = None):  
        self.pos = pos  
        self.token = token  
        self.parent = parent


class PinyinTokenizer(object):

    def __init__(self, dict_path=os.path.join(here,"data/pinyin_tokenizer.txt")):
        trie = Trie()
        with open(dict_path) as f:
            for pinyin in f:
                trie.add(pinyin[0:-1])
        self.trie = trie

    def tokenize(self, content):  
        total_length = len(content)  
        candidate_pos = [ScanPos(0)]  
        spell_pos = None
        while True:
	    if not candidate_pos:
		break
            p = candidate_pos.pop()  
            if p.pos == total_length:  
                spell_pos = p
                break
            matches = self.trie.search(content[p.pos:])  
            for m in  matches:  
                new_pos = ScanPos(len(m) + p.pos, m, p)  
                candidate_pos.append(new_pos)  

        tokens = []
        while spell_pos:  
            if spell_pos.parent:  
                tokens.insert(0, spell_pos.token)  
            spell_pos = spell_pos.parent  
        return tokens


tokenizer = PinyinTokenizer()
tokenize = tokenizer.tokenize

class PinyinConverter(object):
    def __init__(self, dict_path=os.path.join(here,"data/chinese_to_pinyin.txt")):
        self.word_dict = {}
        with file(dict_path) as f_obj:
            for f_line in f_obj.readlines():
                line = f_line.split('\t')
                self.word_dict[line[0]] = line[1]


    def chinese_to_pinyin(self, string=""):
        result = []
        if not isinstance(string, unicode):
            string = string.decode("utf-8")
        
        for char in string:
            key = '%X' % ord(char)
            value = self.word_dict.get(key, char).split()
            if len(value) == 0:continue
            result.append(value[0][:-1].lower())

        return result


chinese_to_pinyin = PinyinConverter().chinese_to_pinyin
is_pinyin = re.compile('^[a-zA-Z]+[*?]*$').match
