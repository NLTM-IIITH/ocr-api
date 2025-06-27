"""
An implementation of trie for the IndicOCR postprocessing algorithm
Implementation is based on https://github.com/TheAlgorithms/Python/blob/1cfca52db73ee18b9e9e08febe9e7d42f96e43db/data_structures/trie/trie.py
"""

blank_char = "blank"

class Node:
    def __init__(self, word: str = None, character: str = None) -> None:
        self.word: str = word
        self.character: str = character
        self.children: dict[str, Node] = {}
        self.is_end: bool = False
        self.suffix_count: int = 0

    def insert_list(self, words: list[str]) -> None:
        for word in words:
            self.insert_single(word)

    def insert_single(self, word: str) -> None:
        curr = self
        cur_string = ""
        for i in range(len(word)):
            curr.suffix_count += 1
            letter = word[i]
            cur_string = cur_string + letter
            if letter not in curr.children:
                curr.children[letter] = Node(word=cur_string, character=letter)
            curr = curr.children[letter]
        curr.suffix_count += 1
        curr.is_end = True

    def in_trie(self, word: str) -> bool:
        curr = self
        for letter in word:
            if letter in curr.children:
                curr = curr.children[letter]
            else:
                return False
        return curr.is_end

    def view_trie(self) -> None:
        if self.is_end:
            print(self.word)
        for child in self.children:
            self.children[child].view_trie()
