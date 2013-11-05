import nltk

def search_builder(verb_regex, corp=Corpus('/home/aaronsteven/Ubuntu One/software/TreeSift/childes.parsed')):
    search_list = ['VP', ['VB.*', verb_regex]]
    return ImmediateDominationSearch(corp, search_list, filtered=True)

verb_regexes = ['.*',
                'hit.*',
                'pull.*',
                'push.*',
                'throw.*|threw',
                'tickle.*',
                'touch.*',
                'wash.*',
                'wipe.*']

# comp_regexes = [[],
#                 ['NP'],
#                 ['PP'],
#                 [['PP', ['IN', 'with']]],
#                 [['PP', ['IN', 'on']]],
#                 ['NP', 'PP'],
#                 [['NP', 'N.*'], ['PP', ['IN', 'with']]],
#                 [['NP', 'N.*'], ['PP', ['IN', 'on']]]]

searches = {verb : search_builder(verb) for verb in verb_regexes}
#counts = {verb : map(lambda x: len(list(x)), search) for verb, search in searches.iteritems()}

productions = {verb : map(lambda x: x.productions(), search) for verb, search in searches.iteritems()}

np = nltk.tree.Nonterminal('NP')
pp = nltk.tree.Nonterminal('PP')

np_only = {verb : [prods for prods in prods_lists if (np in prods[0]._rhs and pp not in prods[0]._rhs)] for verb, prods_lists in productions.iteritems()}
pp_only = {verb : [prods for prods in prods_lists if (pp in prods[0]._rhs and np not in prods[0]._rhs)] for verb, prods_lists in productions.iteritems()}
np_pp = {verb : [prods for prods in prods_lists if (np in prods[0]._rhs and pp in prods[0]._rhs)] for verb, prods_lists in productions.iteritems()}

prep = nltk.tree.Nonterminal('IN')

pp_prods = {verb : [filter(lambda x: prep == x._lhs, prods) for prods in prods_lists] for verb, prods_lists in pp_only.iteritems()}
