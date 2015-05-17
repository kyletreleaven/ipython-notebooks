
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
        -Stock types and stores
        -Current stock, by stock type and store
        -Stock capacity, per store
        -Priorities, see below.
        
    Find:
        -Additional stock, by stock type and store
        -a scalar inventory multiplier
    
    Such that:
        -Total stock fits in storage
        -Total stock and current stock are proportional (by type)
        -Inventory multiplier is maximum
        -Additional stock satisfies priority constraints
    """

    STOCKS = ['S','M','T']
    STORES = [ 1,2,3,4 ]

    stock_priority = { 'S': 1, 'M': 2, 'T': 3 }
    store_priority = { 1: 1, 2: 1, 3: 2, 4: 3 }

    # parameters
    current_stock = [
        { 'stock': stock, 'store': store, 'quantity': np.random.rand() }
        for stock in STOCKS for store in STORES ]
        #if HEIGHTS.index(h) <= HEIGHTS.index(LEVEL_TYPE[lvl]) ]
    current_stock = pd.DataFrame.from_records(current_stock, index=('stock','store'))['quantity']

    #store_capacity = [ { 'store': store, 'capacity': 10. * np.random.rand() } for store in STORES ]
    store_capacity = [ { 'store': store, 'capacity': 10. } for store in STORES ]
    store_capacity = pd.DataFrame.from_records(store_capacity, index=('store'))['capacity']

    # problem variables
    inventory_multiplier = cvxpy.Variable(name='alpha')
    
    # helper variables  
    additional_stock = [
        { 'stock': stock, 'store': store, 'quantity': cvxpy.Variable(name='x_{%s,%d}' % (stock,store) ) }
        for stock in STOCKS for store in STORES ]
    additional_stock = pd.DataFrame.from_records(additional_stock, index=('stock','store'))['quantity']

    # derived
    total_stock = current_stock.add(additional_stock, fill_value=0.)

    current_stock_by_type = current_stock.reset_index().groupby('stock')['quantity'].sum()
    total_stock_by_type = total_stock.reset_index().groupby('stock')['quantity'].sum()
    total_stock_by_store = total_stock.reset_index().groupby('store')['quantity'].sum()

    current_stock_by_type_scaled = current_stock_by_type.apply( lambda x : x * inventory_multiplier )
    
    # problem setup
    objective = cvxpy.Maximize(inventory_multiplier)
    
    constr = []

    # scaling constraints
    vec_eq = np.vectorize( lambda a,b : a == b )
    constr.extend( c for c in vec_eq( total_stock_by_type, current_stock_by_type_scaled ) )

    # non-neg: no, see if we can reproduce the bullshit result
    vec_geq = np.vectorize( lambda a,b : a >= b )
    constr.extend( c for c in vec_geq( additional_stock, 0. ) )

    # total capacity constraints
    vec_leq = np.vectorize( lambda a,b : a <= b )
    constr.extend( c for c in vec_leq( total_stock_by_store, store_capacity ) )

    # categorical constraints
    constr.extend( additional_stock[stock,store] <= 0.
        for stock in STOCKS for store in STORES
        if store_priority[store] < stock_priority[stock] )

    p = cvxpy.Problem(objective, constr)
    
    if True :
        #p.solve(solver=cvxpy.CVXOPT)
        p.solve()

        soln = { stock: { store: total_stock[stock,store].value for store in STORES } for stock in STOCKS }
        print soln
            