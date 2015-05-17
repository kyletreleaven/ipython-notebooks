
import itertools
from collections import defaultdict

import numpy as np
import networkx as nx

#import pandas
#idx = pandas.IndexSlice

import cvxpy


if __name__ == '__main__' :
    """
    work in progress:
    
    Given:
        -Current stock, by height category and storage level
        -Stock capacity, by level
        -Height category, per level
        
    Find:
        -Additional stock, per height category and storage level
        -a scalar inventory multiplier
    
    Such that:
        -Total stock fits in storage
        -Total stock and current stock are proportional (by height category)
        -Inventory multiplier is maximum
    """
    
    # domain
    HEIGHTS = ['S','M','T']
    # cat1 -> cat2 => stock of cat1 can be stored on level of cat2
    digraph = nx.DiGraph()
    digraph.add_edges_from( itertools.combinations_with_replacement(HEIGHTS,2) )    # just lucky
    
    LEVELS = [ 1,2,3,4 ]
    LEVEL_TYPE = { 1 : 'S', 2 : 'S', 3 : 'M', 4 : 'T' }
    
    # parameters
    current_stock = defaultdict( lambda : defaultdict(float) )
    for lvl, h in itertools.product(LEVELS,HEIGHTS) :
        current_stock[h][lvl] = np.random.rand()
        
    stock_capacity = { lvl : 10. for lvl in LEVELS }
    
    # problem variables
    inventory_multiplier = cvxpy.Variable(name='alpha')
    
    # helper variables  
    additional_stock = defaultdict( lambda : defaultdict(float) )
    for lvl, h in itertools.product(LEVELS,HEIGHTS) :
        additional_stock[h][lvl] = cvxpy.Variable(name = 'x_{%d,%s}' % (lvl,h) )
        
    
    
    # derived
    total_stock = defaultdict( lambda : defaultdict(float) )
    for lvl, h in itertools.product(LEVELS,HEIGHTS) :
        total_stock[h][lvl] = current_stock[h][lvl] + additional_stock[h][lvl]  
        
    current_stock_by_height = { h : sum(byLevel.itervalues()) for h, byLevel in current_stock.iteritems() }
    #current_stock_by_height_scaled = { h : inventory_multiplier * stock for h, stock in current_stock_by_height.iteritems() }
    
    total_stock_by_height = { h : sum(byLevel.itervalues()) for h, byLevel in total_stock.iteritems() }
    
    total_stock_by_level = defaultdict(float)
    for h, byLevel in total_stock.iteritems() :
        for lvl, stock in byLevel.iteritems() :
            total_stock_by_level[lvl] += stock
            
    # problem setup
    objective = cvxpy.Maximize(inventory_multiplier)
    
    constr = []
    
    # non-neg
    for lvl, h in itertools.product(LEVELS,HEIGHTS) :
        continue
        constr.append( additional_stock[h][lvl] >= 0. ) 
    
    # scaling constraint
    for h in HEIGHTS :
        constr.append( total_stock_by_height[h] == inventory_multiplier * current_stock_by_height[h] )
    
    # capacity constraints
    for lvl in stock_capacity :
        constr.append( total_stock_by_level[lvl] <= stock_capacity[lvl] )
        
        storage_height = LEVEL_TYPE[lvl]
        for stock_height in HEIGHTS :
            if not digraph.has_edge(stock_height,storage_height) :  # height category doesn't fit in category of the level
                constr.append( total_stock[stock_height][lvl] <= 0. )
                
                
    p = cvxpy.Problem(objective, constr)
    
    if True :
        p.solve()
        
        soln = defaultdict( lambda : defaultdict(float) )
        for lvl, h in itertools.product(LEVELS,HEIGHTS) :
            soln[h][lvl] = total_stock[h][lvl].value

