
import itertools
from collections import defaultdict

import cvxpy

import numpy as np
import pandas as pd

idx = pd.IndexSlice

# just for some semantic representation
# import networkx as nx




if __name__ == '__main__' :
    """
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
    # digraph = nx.DiGraph()
    # digraph.add_edges_from( itertools.combinations_with_replacement(HEIGHTS,2) )    # just lucky they have nice structure
    
    LEVELS = [ 1,2,3,4 ]
    LEVEL_TYPE = { 1 : 'S', 2 : 'S', 3 : 'M', 4 : 'T' }

    # parameters
    current_stock = [
        { 'level': lvl, 'height': h, 'stock': np.random.rand() }
        for lvl, h in itertools.product(LEVELS,HEIGHTS)
        if HEIGHTS.index(h) <= HEIGHTS.index(LEVEL_TYPE[lvl]) ]
    current_stock = pd.DataFrame.from_records(current_stock, index=('level','height'))['stock']

    stock_capacity = [ { 'level': lvl, 'capacity': 10. } for lvl in LEVELS ]
    stock_capacity = pd.DataFrame.from_records(stock_capacity, index=('level'))['capacity']

    # problem variables
    inventory_multiplier = cvxpy.Variable(name='alpha')
    
    # helper variables  
    additional_stock = [ { 'level': lvl, 'height': h, 'stock': cvxpy.Variable(name='x_{%d,%s}' % (lvl,h)) } for lvl, h in itertools.product(LEVELS,HEIGHTS) ]
    additional_stock = pd.DataFrame.from_records(additional_stock, index=('level','height'))['stock']

    # derived
    total_stock = current_stock.add(additional_stock, fill_value=0.)

    current_stock_by_height = current_stock.reset_index().groupby('height')['stock'].sum()
    total_stock_by_height = total_stock.reset_index().groupby('height')['stock'].sum()
    total_stock_by_level = total_stock.reset_index().groupby('level')['stock'].sum()

    current_stock_by_height_scaled = current_stock_by_height.apply( lambda x : x * inventory_multiplier )
    
    # problem setup
    objective = cvxpy.Maximize(inventory_multiplier)
    
    constr = []

    # scaling constraints
    vec_eq = np.vectorize( lambda a,b : a == b )
    constr.extend( c for c in vec_eq( total_stock_by_height, current_stock_by_height_scaled ) )

    # non-neg: no, see if we can reproduce the bullshit result
    vec_geq = np.vectorize( lambda a,b : a >= b )
    constr.extend( c for c in vec_geq( additional_stock, 0. ) )

    # total capacity constraints
    vec_leq = np.vectorize( lambda a,b : a <= b )
    constr.extend( c for c in vec_leq( total_stock_by_level, stock_capacity ) )

    # categorical constraints
    for lvl in LEVELS :
        level_height = LEVEL_TYPE[lvl]
        level_height_idx = HEIGHTS.index(level_height)

        for stock_height in HEIGHTS :
            if HEIGHTS.index(stock_height) > level_height_idx :
                constr.append( total_stock[lvl,stock_height] <= 0. )

    p = cvxpy.Problem(objective, constr)
    
    if True :
        #p.solve(solver=cvxpy.CVXOPT)
        p.solve()

        soln = defaultdict( lambda : defaultdict(float) )
        for lvl, h in itertools.product(LEVELS,HEIGHTS) :
            soln[h][lvl] = total_stock[lvl,h].value

            