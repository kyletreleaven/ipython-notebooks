
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

    STOCKS = ['A','B','C']
    STORES = [ 1, 2, 3, 4 ]

    # stock of priority x must be inducted to a store of priority >= x
    stock_priority = { 'A': 1, 'B': 2, 'C': 3 }
    store_priority = { 1: 1, 2: 1, 3: 2, 4: 3 }

    # parameters
    current_stock = [
        { 'stock': 'A', 'store': 1, 'quantity': 2. },
        { 'stock': 'B', 'store': 1, 'quantity': 3. },
        { 'stock': 'C', 'store': 4, 'quantity': 1. }
        ]

    current_stock = pd.DataFrame.from_records(current_stock, index=('stock','store'))['quantity']

    #store_capacity = [ { 'store': store, 'capacity': 10. * np.random.rand() } for store in STORES ]
    store_capacity = [
            { 'store': 1, 'capacity': 100. },
            { 'store': 2, 'capacity': 100. },
            { 'store': 3, 'capacity': 10. },
            { 'store': 4, 'capacity': 10. } ]

    store_capacity = pd.DataFrame.from_records(store_capacity, index=('store'))['capacity']

    # problem variables
    inventory_multiplier = cvxpy.Variable(name='alpha')
    
    # helper variables  
    additional_stock = [
        { 'stock': stock, 'store': store, 'quantity': cvxpy.Variable(name='x[%s,%d]' % (stock,store) ) }
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
    p.solve(solver=cvxpy.CVXOPT)

    if True :
        to_readable = lambda x : '%.2f' % x.value

        print 'inventory multiplier: ', inventory_multiplier.value
        print 'additional stock:'
        print additional_stock.apply( to_readable )

        print 'total stock by store:'
        print pd.concat([ total_stock_by_store.apply( to_readable), store_capacity ], axis=1)
        #print total_stock_by_store.apply( to_readable )


        print 'C doesn\'t saturate ', total_stock['C',4].value < store_capacity[4]


