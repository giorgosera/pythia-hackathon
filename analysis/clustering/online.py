'''
Created on 2 Mar 2012

@author: george
'''
import heapq, operator, scipy, nltk, numpy
import Orange#!@UnresolvedImport
from analysis.clustering.abstract import AbstractClusterer
from analysis.clustering.structures import kernel_dist
from tools.orange_utils import construct_orange_table, add_metas_to_table
from analysis.clustering.structures import OnlineCluster
import time

class OnlineClusterer(AbstractClusterer):
    '''
    This class implements a basic online clustering algorithm. The code is adapted from
    http://gromgull.net/blog/2009/08/online-clustering-in-python/ . Thanks gromgull. 
    For the theoretical background check out http://dl.acm.org/citation.cfm?id=1044332 and http://www.cs.huji.ac.il/~werman/Papers/guedalia_etal99.pdf
    '''

    def __init__(self, N, window):
        """
        N-1 is the largest number of clusters that can be detected.
        window is the sliding window width.
        """
        super(OnlineClusterer, self).__init__(filter_terms=False)#Force filter terms to be false cz not yet supported
        self.N=N        
        self.clusters=[]
        # cache inter-cluster distances
        self.dist=[]
        self.cluster_id_counter = 0 #It holds the id of the cluster to be created
        self.dim=0 
        self.window = window
        
    def add_document(self, document):
        '''
        Overrides the parent method add_document to facilitate
        the needs of online clustering. Basically, it adds the new document 
        normally and then 
        '''
        index = super(OnlineClusterer, self).add_document(document)
        return index

    def construct_term_doc_matrix(self, index, document):
        '''
        Overrides the parent method for constructing a td_matrix. The reason is 
        because we want to construct the matrix based on a sliding window approach.
        '''        
        if index < self.window:
            documents = self.document_dict.values()
        else:
            window=(index-self.window+1, index)
            documents = self.document_dict.values()[window[0]:window[1]]
        
        #Online clustering doesn't support term filtering yet     
        corpus = nltk.TextCollection([document.tokens for document in documents])
        
        terms = list(set(corpus))
        term_vector = numpy.zeros(len(set(corpus)))
        
        text = nltk.Text(document.tokens)
        for item in document.word_frequencies:
            term_vector[terms.index(item.word)] = corpus.tf_idf(item.word, text)
                
        self.attributes = terms
        self.td_matrix = term_vector
    
    def resize(self):
        for c in self.clusters:
            c.resize(self.attributes)
    
    def cluster(self, document):
        '''
        Performs clustering for a new document. It takes as input 
        a document object from the db and finds the closer cluster for it.
        '''
        doc_index = self.add_document(document)
        doc_id = str(document.id)
        doc_content = document.content

        self.construct_term_doc_matrix(index=doc_index, document=doc_content)
        
        print 'N', len(self.clusters)
        print 'clustering', doc_index
        if doc_index > 0: #ignore the first document
            #e = doc_index
            e = self.td_matrix
            newc=OnlineCluster(a=e, cluster_id=self.cluster_id_counter, doc_id=doc_id, doc_content=doc_content, term_vector=self.attributes) 
            
            #If the new term vector is larger then change all the cluster centers
            #However, if the new term vector is smaller then pad the new cluster's center
            if len(self.clusters) > 0:
                if len(newc.term_vector) > len(self.clusters[0].term_vector):
                    self.resize()
                else:
                    newc.resize(self.clusters[0].term_vector)
                    e = newc.center
                
            if len(self.clusters)>0: 
                # Compare the new document to each existing cluster
                c=[ ( i, kernel_dist(x.center, e) ) for i,x in enumerate(self.clusters)]
                closest_cluster = min( c , key=operator.itemgetter(1))
                if closest_cluster[1] < 1.0:
                    closest=self.clusters[closest_cluster[0]]
                    closest.add(e, doc_id, doc_content)
                    # invalidate dist-cache for this cluster
                    self.updatedist(closest)
                else:
                    # make a new cluster for this point
                    self.clusters.append(newc)
                    self.updatedist(newc)
    
            if len(self.clusters)>=self.N and len(self.clusters)>1:
                # merge closest two clusters. It doesn't matter which ones, Only the closest
                m=heapq.heappop(self.dist)
                m.x.merge(m.y)
                self.clusters.remove(m.y)
                self.removedist(m.y)
                self.updatedist(m.x)
                self.cluster_id_counter += 1
        else:
            newc=OnlineCluster(a=self.td_matrix, cluster_id=self.cluster_id_counter, doc_id=doc_id, doc_content=doc_content, term_vector=self.attributes) 
            self.clusters.append(newc)
            self.updatedist(newc)
                
    def removedist(self,c):
        """
        Invalidate intercluster distance cache for c
        """
        r=[]
        for x in self.dist:
            if x.x==c or x.y==c: 
                r.append(x)
        for x in r: self.dist.remove(x)
        heapq.heapify(self.dist)
        
    def updatedist(self, c):
        """
        Cluster c has changed, re-compute all intercluster distances
        """
        self.removedist(c)

        for x in self.clusters:
            if x==c: continue
            d=kernel_dist(x.center,c.center)
            t=Dist(x,c,d)
            heapq.heappush(self.dist,t)
                
    def trimclusters(self):
        """Return only clusters over threshold"""
        t= scipy.mean([x.size for x in filter(lambda x: x.size>0, self.clusters)])*0.5
        self.clusters = filter(lambda x: x.size>=t, self.clusters)
        return self.clusters

    def plot_scatter(self):
        '''
        Overrides the parent class method. Plots all the data points in 2D.
        '''
        #Create a clusterer document list to get the index of a doc (horrible hack I know)
        clusterer_document_list = [key for key in self.document_dict.keys()] 
        corpus = nltk.TextCollection([document.tokens for document in self.document_dict.values()])
        all_terms_vector = list(set(corpus))
        table = construct_orange_table(all_terms_vector)
        meta_col_name="cluster_id"
        table = add_metas_to_table(table, meta_col_name=meta_col_name)

        instances = []
        for cluster in self.clusters:
            for doc_id, doc_content in cluster.document_dict.iteritems():
                index = clusterer_document_list.index(doc_id)
                
                #We use index = 1 to force the function to construct the vector according to all the documents in the collection
                self.construct_term_doc_matrix(index, doc_content)
                oc = OnlineCluster(self.td_matrix, 1, doc_id, doc_content, self.attributes)
                oc.resize(all_terms_vector)
                inst = Orange.data.Instance(table.domain, list(oc.center))
                inst[meta_col_name] = str(cluster.id)
                instances.insert(index, inst)

        #we have a table with the clusters ids as metas.                
        table.extend(instances)        
        from visualizations.mds import MDS
        mds = MDS(table)
        classes_list = []
        for c in self.clusters:
            classes_list.append(c.id)   
                     
        mds.plot(classes_list=classes_list, class_col_name="cluster_id")

################################################
#HELPER CLASSES AND METHODS
################################################

class Dist(object):
    """
    This is just a tuple, but we need an object so we can define cmp for heapq
    """
    def __init__(self,x,y,d):
        self.x=x
        self.y=y
        self.d=d
    def __cmp__(self,o):
        return cmp(self.d,o.d)
    def __str__(self):
        return "Dist(%f)"%(self.d)  



if __name__=="__main__": 
    
    import random

    try:
        import pylab#!@UnresolvedImport
        import scipy
        plot=True
    except:
        plot=False

    points=[]
    # create three random 2D gaussian clusters
    for i in range(3):
        x=random.random()*3
        y=random.random()*3
        c=[scipy.array((x+random.normalvariate(0,0.1), y+random.normalvariate(0,0.1))) for j in range(100)]
        points+=c

    
    if plot: pylab.scatter([x[0] for x in points], [x[1] for x in points])

    random.shuffle(points)
    n=len(points)

    start=time.time()
    # the value of N is generally quite forgiving, i.e.
    # giving 6 will still only find the 3 clusters.
    # around 10 it will start finding more
    c=OnlineClusterer(N=6, window=0)
    while len(points)>0: 
        c.cluster(points.pop(), 1, "test")

    clusters=c.trimclusters()
    print "I clustered %d points in %.2f seconds and found %d clusters."%(n, time.time()-start, len(clusters))

    if plot: 
        cx=[x.center[0] for x in clusters]
        cy=[y.center[1] for y in clusters]
    
        pylab.plot(cx,cy,"ro")
        pylab.draw()
        pylab.show()