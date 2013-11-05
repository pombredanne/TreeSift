import sys, os
import re

from itertools import chain, permutations

from nltk.tree import Tree
from nltk.corpus.reader.bracket_parse import BracketParseCorpusReader
from nltk.util import ngrams

class Corpus(object):

    def __init__(self, root, fids='.*', tag_taxonomy=None, headship=None):
        self.corpus = BracketParseCorpusReader(root=root, fileids=fids)

        self._corpus_iter = (sent for sent in self.corpus.parsed_sents())

    def __iter__(self):
        return self

    def next(self):
        try:
            return self._corpus_iter.next()
        except StopIteration:
            self._corpus_iter = (sent for sent in self.corpus.parsed_sents())
            raise

class Search(object):

    def __init__(self, corpus, filtered=False):
        self.corpus = corpus
        self.filtered = filtered
        self._search_iter = self._iter_creator()

    def __iter__(self):
        return self

    def next(self):
        try:
            return self._search_iter.next()
        except StopIteration:
            self._search_iter = self._iter_creator()
            raise

    def __call__(self, tree):
        return [tree]

    def _iter_creator(self):
        if self.filtered:
            return (tree for trees in (self(tree) for tree in self.corpus if self(tree)) for tree in trees)
        else:
            return (tree for tree in self.corpus if self(tree))

    @staticmethod
    def subtrees_rooted_by(tree, roots):
        if not isinstance(roots, list):
            roots = [roots]

        test_func = lambda match_func: lambda from_tree: any([match_func(root, from_tree) for root in roots])

        nonleaf_test = test_func(lambda root, from_tree: root.match(from_tree.node))
        nonleaves = list(tree.subtrees(nonleaf_test))

        leaf_test = test_func(lambda root, from_tree: root.match(from_tree))

        try:
            leaves = [leaf for leaf in tree.leaves() if leaf_test(leaf)]
        except TypeError:
            return nonleaves

        return nonleaves + leaves

    @staticmethod
    def children_of_root(tree):
        for child in tree:
            try:
                yield child.node
            except AttributeError:
                yield child


class ContainmentSearch(Search):

    def __init__(self, corpus, contained, filtered=False):
        Search.__init__(self, corpus, filtered)
        self.contained = ContainmentSearch._convert_leaves_to_re(contained)

    def __call__(self, tree):
        return Search.subtrees_rooted_by(tree, self.contained)

    @staticmethod
    def _convert_leaves_to_re(list_tree):
        converted = []

        for node in list_tree:
            if isinstance(node, basestring):
                re_node = re.compile(node)
                converted.append(re_node)
            elif isinstance(node, list):
                re_tree = ContainmentSearch._convert_leaves_to_re(node)
                converted.append(re_tree)
            else:
                raise TypeError, 'list_tree must be lists (of lists) of (base)strings'

        return converted

class DominationSearch(ContainmentSearch):

    def __call__(self, tree, dom_chain=None):
        if not dom_chain:
            dom_chain = self.contained
            starting = Search.subtrees_rooted_by(tree, dom_chain[0])
        else:
            starting = self.__class__._sub_filter(tree, dom_chain[0])

        current = [list(enumerate(starting))]

        for i, node in enumerate(dom_chain[1:]):
            current.append([])

            if current[i]:
                for j, subtree in current[i]:
                    if not isinstance(node, list):
                        filtered = self.__class__._sub_filter(subtree, node)
                        if filtered:
                            current[i+1].extend([(j, st) for st in filtered])
                    else:
                        if self(subtree, node):
                            current[i+1].append((j, subtree))
            else:
                break

        if current[-1]:
            indices = set([st[0] for st in current[-1]])
            return [current[0][i][1] for i in indices]

    @staticmethod
    def _sub_filter(subtree, node):
        return Search.subtrees_rooted_by(subtree, node)


class ImmediateDominationSearch(DominationSearch):

    @staticmethod
    def _sub_filter(subtree, node):
        children = Search.children_of_root(subtree)

        return [subtree[i] for i, child in enumerate(children) if node.match(child)]

class SisterSearch(ContainmentSearch):

    def __call__(self, tree):
        children = self.__class__._child_set_finder(tree)

        for sisters in children:
            for seq in sisters:
                matched = [subtree[j] for j, child in enumerate(seq) if self.contained[j].match(child)]
                if matched:
                    return matched

    @staticmethod
    def _child_set_finder(tree):
        children = (permutations(Search.children_of_root(subtree), len(self.contained)) for subtree in tree.subtrees())

        return children

class ImmediateSisterSearch(SisterSearch):

    @staticmethod
    def _child_set_finder(tree):
        child_seqs = [list(ngrams(Search.children_of_root(subtree), len(self.contained))) for subtree in tree.subtrees()]

        child_seqs = child_seqs + map(lambda seq: map(reversed, seq), child_seqs)

        return child_seqs

if __name__ == '__main__':

    def create_nonfinite_corpus():
        c = Corpus('/media/aaronsteven/FD16-60D8/gigaword/english/parsed/NYT')

        for match in ImmediateDominationSearch(c, ['VP', ['VB.*', '.*'], ['VP', 'TO']], filtered=True):
            i = [i for i, child in enumerate(Search.children_of_root(match)) if 'VB' == child[:2]][0]
            v = match[i][0]

            try:
                f = open('verbs/' + v.lower(), 'a')

                for j, subtree in enumerate(match):
                    if j != i:
                        f.write(subtree.pprint())
                        f.write('\n\n')

                f.close()
            except:
                pass

    def nonfinite_corpus_generator(root, typ='all'):

        numverbs = len(os.listdir(root))

        for i, verb in enumerate(os.listdir(root)):
            print verb, '({0})'.format(str(i) + '/' + str(numverbs))

            s = ImmediateDominationSearch(Corpus(root=root, fids=verb), ['VB.*', '.*'], filtered=True)

            for tree in s:
                try:
                    if typ == 'all':
                        for item in chain(tree.leaves(), tree.productions()):
                            print '\t', item
                            yield (verb, item)
                    elif typ == 'leaves':
                        for item in tree.leaves():
                            print '\t', item
                            yield (verb, item)
                    elif typ == 'productions':
                        for item in tree.productions():
                            print '\t', item
                            yield (verb, item)
                    else:
                        raise Exception, 'parameter typ must be in {"all", "leaves", "productions"}'

                except AttributeError:
                    pass
