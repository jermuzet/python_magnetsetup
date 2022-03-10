= Basic usage

To get a magnet from the magnetdb:

```
python -m python_magnetdb.app --displaymagnet HL-34
```

or use option `--magnet` when running magnetsetup

[NOTE]
====
This requires that the magnetdb is up and running
See magnetdb for details
See `settings.env` for default configuration
====

This will create a json file holding geometrical and material data for  magnet HL-34.
You can use this file to create a setup for Axi Fully coupled model, using

```
python -m python_magnetsetup.cli \
   --wd data --datafile HL-34-data.json \
   --method cfpdes --time static --geom Axi --model thmagel [--nonlinear] --cooling mean
```

[NOTE]:
====
To run simulation with Feelpp, we still need to create:

* a mesh file ( see magnetgeo)
* a cfg file for
====

You can also use directly the magnetdb. To do so:

```
python -m python_magnetsetup.cli --wd data --magnet HL-test --method cfpdes --time static --geom Axi --model thmagel  --cooling mean
python -m python_magnetsetup.cli --wd data --magnet M9Bitters --method cfpdes --time static --geom Axi --model thmagel  --cooling mean
```

[NOTE]:
====
To use the magnetdb directly, you shall update environment variables in `settings.env` to reflect your configuration.
====