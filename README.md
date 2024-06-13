# LIBRA
***L****ightcurve* ***I****nvestigation* *for* ***B****inary* *o****R****bital period* ***A****nalysis*


### Query
```
    SELECT *
    FROM mean_param
    JOIN magnitudes ON mean_param.iau_name = magnitudes.iau_name
    WHERE magnitudes.i < 18;
```
