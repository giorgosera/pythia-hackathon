'''
Created on 29 Jan 2012

@author: george
'''
import itertools, nltk, tools.utils, numpy, scipy, math
from database.warehouse import WarehouseServer
from analysis.semantic import TwitterSemanticAnalyser
from collections import OrderedDict
from analysis.summarization.summarization import CentroidSummarizer, LexRankSummarizer

class Cluster(object):
    '''
    This is a structure responsible for representing a cluster after the 
    clustering has been performed. This class is used by the clusterers.
    '''
    def __init__(self, id, document_dict, top_patterns = None):
        '''
        Id specifies the id of this cluster and document_dict 
        is a dictionary storing all the relevant documents for this
        cluster.
        '''
        self.id = id
        self.document_dict = document_dict
        self.top_patterns = top_patterns
        self.locations = []
        self.persons = []
        self.users = []
        
    def get_documents(self):
        '''
        Returns a dictionary of the documents in the cluster.
        '''
        return self.document_dict
    
    def get_most_frequent_terms(self, N=5):
        '''
        Returns the top N occuring terms in this cluster.
        '''
        if self.top_patterns != None:
            return self.top_patterns
        else:
            corpus = nltk.TextCollection([document.tokens for document in self.document_dict.values()])
            return nltk.FreqDist(corpus).items()[:N]     
    
    def get_size(self):
        '''
        The size of the cluster is defined by the number of its documents.
        '''   
        return len(self.document_dict.keys())
    
    def summarize(self):
        '''
        Performs cluster summarization. It returns a list of ranked documents.
        '''
        cs = LexRankSummarizer(self.document_dict)
        sorted_documents = cs.summarize()
        return sorted_documents
    
    def analyse(self):
        '''
        Analyses the cluster to extract meta-information such as 
        locations, persons, users and relations.
        '''
        text_collection = []
        for document in self.document_dict.values():
            raw = nltk.WordPunctTokenizer().tokenize(document.raw)
            for token in raw:
                if token not in nltk.corpus.stopwords.words('english') and token not in tools.utils.ignorewords:
                    text_collection.append(token)
        tagged_corpus = nltk.pos_tag(text_collection)

        for chunk in nltk.ne_chunk(tagged_corpus): 
            if hasattr(chunk, 'node'):    
                if chunk.node == 'GPE':
                    self.locations.append(' '.join(c[0] for c in chunk.leaves()))
                elif chunk.node == 'PERSON':
                    self.persons.append(' '.join(c[0] for c in chunk.leaves()))
        
    def get_locations(self, N=1):
        '''
        Returns a list with the top N locations mentioned in the docs in this cluster.
        '''
        corpus = nltk.text.TextCollection([self.locations])
        return nltk.FreqDist(corpus).items()[:N]
    
    def get_persons(self, N=1):
        '''
        Returns the top N persons mentioned in the docs in this cluster.
        '''
        corpus = nltk.text.TextCollection([self.persons])
        return nltk.FreqDist(corpus).items()[:N]
    
    def get_authors(self):
        '''
        Returns the authors of the documents that appear in this cluster.
        '''
        ws = WarehouseServer()
        authors = set(ws.get_document_authors(self.document_dict.keys()))
        return list(authors)
    
    def get_relations(self):
        '''
        Returns the main relations detected in this cluster
        '''
        pass
    
    def get_sentiment(self, cumulative=False):
        '''
        Calculates the sentiment of the cluster. It returns 
        a list of tuples (date, value) where date value is the accumulated sentiment
        of that date.
        '''
        emotional_rollercoaster = []
        tsa = TwitterSemanticAnalyser()
        for document in self.document_dict.values():
            sentiment = tsa.extract_sentiment(' '.join(token for token in document.tokens))
            emotional_rollercoaster.append( (document.date, sentiment) )

        #It's important to sort this list otherwise itertools will npt work.
        #The we group emotion scores by date. t[1][1] is the score of a document at time d.
        x = sorted(emotional_rollercoaster)
        grouped_emotions = [(d, sum([float(t[1][1]) for t in g])) for d, g in itertools.groupby(x, lambda x: x[0])]
        return grouped_emotions
            
    def get_collocations(self, n=2, N=5):
        '''
        Returns the top collocations of the cluster corpus 
        based on Jaccard index. The collocations correspond 
        to n-grams and more specifically we limited the options
        to bigrams (n=2) and trigrams (n=3) ( n defaults to 2 ). 
        '''
        corpus = nltk.TextCollection([document.tokens for document in self.document_dict.values()])
        finder = nltk.BigramCollocationFinder.from_words(corpus)
        scorer = nltk.metrics.BigramAssocMeasures.jaccard
        #finder.apply_freq_filter(3)
        finder.apply_word_filter(lambda w:w in nltk.corpus.stopwords.words('english'))
        collocations = finder.nbest(scorer, N)
        
        #print "Cluster",self.id,"collocations:"
        #for collocation in collocations:
            #print ' '.join(str(i) for i in collocation)

####################################
# Online clustering algos
####################################
def kernel_linear(x,y):
    return scipy.dot(x,y)

def kernel_poly(x,y,a=1.0,b=1.0,p=2.0):
    return (a*scipy.dot(x,y)+b)**p
     
def kernel_gauss(x,y, sigma=0.00001):
    v=x-y
    l=math.sqrt(scipy.square(v).sum())
    return math.exp(-sigma*(l**2))

def kernel_dist(x,y):
    # if gaussian kernel:
    return 2-2*kernel(x,y)
    # if not
    #return kernel(x,x)-2*kernel(x,y)+kernel(y,y)   
def kernel_normalise(k): 
    return lambda x,y: k(x,y)/math.sqrt(k(x,x)+k(y,y))

kernel=kernel_normalise(kernel_poly)

class OnlineCluster(Cluster):
    '''
    This the data structure which is used by the online clustering
    algorithm. It inherits the cluster structure and adds to extra
    arguments center and size. 
    '''
    def __init__(self, a, cluster_id, doc_id, doc_content, term_vector): 
        super(OnlineCluster, self).__init__(id=cluster_id, document_dict=OrderedDict([(doc_id, doc_content)])) #Creates a new Cluster with empty document dict
        self.center=a
        self.size=0
        self.term_vector = term_vector
        
    def add(self, e, doc_id, doc_content):
        self.size+= kernel(self.center, e)
        self.center+=(e-self.center)/self.size
        self.document_dict[doc_id] = doc_content
        
    def merge(self, c):        
        self.center=(self.center*self.size+c.center*c.size)/(self.size+c.size)
        self.size+=c.size
        self.document_dict.update(c.document_dict)
        
    def resize(self,new_term_vector):
        '''
        This function resizes the center vector of this cluster according to
        a new term vector. 
        '''       
        new_center = numpy.zeros(len(new_term_vector))
        new_vector = []
        
        #assert(len(new_term_vector) >= len(self.term_vector) )
        #Iterates over the new term vector (either smaller or bigger)
        #and modifies the existing one.
        for new_index, term in enumerate(new_term_vector):
            if term in self.term_vector: 
                old_index = self.term_vector.index(term)
                old_value = self.center[old_index]
                new_center[new_index] = old_value
                new_vector.insert(new_index, term)
            else:
                new_vector.insert(new_index, term)
                new_center[new_index]= 0.0
        self.center = new_center
        self.term_vector = new_vector
        
    def __str__(self):
        return "Cluster( %s, %f )"%(self.center, self.size)

class Bicluster(object):
    '''
    A bicluster class. 
    '''
    
    def __init__(self, vector, left=None, right=None, similarity=0.0, id=None):
        '''
        Constructs a bicluster
        '''
        #AbstractClusterer.__init__(self)
        self.left = left
        self.right = right
        self.vector = vector
        self.similarity = similarity
        self.id = id 
        
    def get_height(self):
        '''
        Returns the height of a cluster. Endpoints have a height of 1 and 
        then all other points have height equal to the sum of all their branches.
        '''    
        if self.left == None and self.right == None:
            return 1
        
        return self.left.get_height() + self.right.get_height()
        
    def get_depth(self):
        '''
        Returns the depth of the error.
        '''
        if self.left == None and self.right == None:
            return 0 
        
        return max(self.left.get_depth(), self.right.get_depth()) + self.similarity

    def print_it(self, labels=None, n=0):
        '''
        This method outputs the clusters in a human readable form.
        '''
        # For each new cluster have a small indentation to make it look hierarchical  
        for i in range(n): 
            print ' ',
        if self.id<0:
            # This is a branch
            print '->'
        else:
            # This is an root node
            if labels==None: print self.id
            else: print labels[self.id]
            
        # Recursively traverse the left and right branches
        if self.left!=None: 
            self.left.print_it(labels=labels,n=n+1)
        if self.right!=None: 
            self.right.print_it(labels=labels,n=n+1)