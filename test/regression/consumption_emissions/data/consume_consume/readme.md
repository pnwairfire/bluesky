The output files were created using Consume5 and the "natural" option like so:

```
Brians-MacBook-Pro:apps-consumeGIT briandrye$ python consume_batch.py -l 3 -o ~/repos/uw/bluesky/bluesky/test/regression/consumption_emissions/data/consume5_regression/scen_1_out.csv natural ~/repos/uw/bluesky/bluesky/test/regression/consumption_emissions/data/consume5_regression/scen_1.csv
```

## Update - 3/21/2018

I [Joel] had to rerun consume_batch.py in order to generate the feps emissions input files (which weren't updated in the repo when the output files were updated).  I did so with the following

```
docker run --rm -ti -v $HOME/code/pnwairfire-fera-apps-consume/:/consume/ \
    -v $HOME/code/pnwairfire-bluesky/test/regression/consumption_emissions/data/consume_consume/:/data/ \
    -w /consume/ bluesky bash
for i in `find /data/ -maxdepth 1 -path "*scen_*" ! -path "*out.csv" ! -path "*feps*"|sed -e 's/\.csv//g'`; do
    echo "---------";
    python3 consume_batch.py -l 3 -o ${i}_out.csv natural $i.csv ;
    mv feps_emissions_input.csv /data/feps_input_em_`echo $i|sed -e 's/\/data\///g'`.csv;
done
exit
```
