# -*- coding: utf-8 -*-
'''
Created on 23 Jan 2012

@author: george

My playground!
'''
import unittest, os
from analysis.index import Index
from database.warehouse import WarehouseServer
from database.model.tweets import TwoGroupsTweet

BASE_PATH = os.path.expanduser("~/virtualenvfyp/pythia/data/")
index_path = BASE_PATH + "test_index"
ws = WarehouseServer()
sample_docs = ws.get_n_documents(100, type=TwoGroupsTweet)

index = Index(index_path)
for doc in sample_docs:
    index.add_document(doc)
index.finalize()

class TestPlayground(unittest.TestCase):
  
    def test_searching(self):        
        results = index.search_by_term("sales")
        
        calculated = []
        for doc in results:
            calculated.append(doc.get('id'))
            
        expected = ['4f2d602780286c38a7000013', '4f2d603280286c38a700001e']
        self.assertEqual(expected, calculated)
    
    def test_top_terms_index(self):
        results = index.get_top_terms(10)
        expected = [(52, u'uk'), (8, u'us'), (8, u'new'), (6, u'week'), (5, u'last'), (5, u'host'), (4, u'yeah'), (4, u'want'), (4, u'presid'), (4, u'nation')]
        self.assertEquals(expected, results)

    def test_search_limit(self):
        results = index.search_by_term("sales", limit=1)
        self.assertEquals(1, len(results))
        
    def test_search_by_author(self):
        results = index.search_by_author("islandrecordsuk")
        expected = '4f2d5ff580286c38a7000000'
        self.assertEquals(expected, results[0].get('id'))
        
    def test_filtered_docs(self):
        self.assertEquals(92, len(index.get_top_documents(lowestf=0.01, highestf=0.4)))
            
if __name__ == "__main__":
    unittest.main()




