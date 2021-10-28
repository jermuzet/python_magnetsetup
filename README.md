= Basic usage

To get a magnet from the magnetdb:

```
python -m python_magnetdb.app --displaymagnet HL-34
```

[NOTE]
====
See magnetdb for details
====

This will create a json file holding geometrical and material data for  magnet HL-34.
You can use this file to create a setup for Axi Fully coupled model, using

```
python -m python_magnetsetup.python_magnetsetup HL-34-data.json --method cfpdes --time static --geom Axi --model thmagel --phytype linear --cooling mean
```

[NOTE]
====
To run simulation with Feelpp, we still need to create:

* a mesh file ( see magnetgeo)
* a cfg file for
====
