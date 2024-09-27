## General

 - area - acres
 - consumption output - tons
 - emissions output - tons (all models, FEPS, CONSUME, Prichard-Oneill)
 - heat output - BTUs
 - FRP - Megawatts


## Notes About Specific Modules

### CONSUME

#### CONSUME Consumption Output

The consume package lets you specify consumption output units as well as area,
but regardless of what you specify, the output units seem to always be in
'tons_ac'.  So, for example, the following

```
    fc = consume.FuelConsumption()
    ...
    fc.area = [1000]
    fc.output_units = 'tons'
```

has the same results as

```
    fc = consume.FuelConsumption()
    ...
    fc.area = [1]
    fc.output_units = 'tons_ac'
```

The pipeline sets area to 1 and units to tons_ac, so that there's
no confusion, and then corrects the output by multiplying by area

#### CONSUME Emissions Output

Unlike with consume consumption results, emissions results do reflect how
you set area and output_units.  So, we set area to the true area and
output units to 'tons'.
