
set STOCKS;
set STORES;

param stock_priority{STOCKS}, integer ;
param store_priority{STORES}, integer ;

param current_stock {STOCKS,STORES} >= 0, default 0;
param store_capacity {STORES} >= 0;

var additional_stock {STOCKS,STORES} >= 0;

var inventory_multiplier >= 0;


maximize multiplier: inventory_multiplier;

s.t. scaling_constraints {i in STOCKS} :
	sum {j in STORES} ( current_stock[i,j] + additional_stock[i,j] ) = inventory_multiplier * sum {j in STORES} current_stock[i,j];

s.t. capacity_constraints {j in STORES} :
	sum {i in STOCKS} ( current_stock[i,j] + additional_stock[i,j] ) <= store_capacity[j];

s.t. priority_constraints {i in STOCKS, j in STORES : store_priority[j] < stock_priority[i] } :
	additional_stock[i,j] <= 0;


solve;

display inventory_multiplier;
display additional_stock;




data;

set STOCKS := S M T ;
set STORES := 1 2 3 4 ;

param stock_priority :=
S 1
M 2
T 3;

param store_priority :=
1 1
2 1
3 2
4 3;

param store_capacity :=
1 10
2 10
3 10
4 10;

param current_stock :=
S 1 1.5
S 2 2
S 3 6
M 1 1
T 4 5;




end;
