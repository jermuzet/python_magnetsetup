# Basic usage

To get a magnet from the magnetdb:

```bash
python -m python_magnetdb.app --displaymagnet HL-34
```

or use option `--magnet` when running magnetsetup

| | This requires that the magnetdb is up and running |
| :bulb: | See magnetdb for details |
| | See `settings.env` for default configuration |

This will create a json file holding geometrical and material data for  magnet HL-34.
You can use this file to create a setup for Axi Fully coupled model, using

```bash
python -m python_magnetsetup.cli \
   --wd data --datafile HL-34-data.json \
   --method cfpdes --time static --geom Axi --model thmagel [--nonlinear] --cooling mean
```

| | To run simulation with Feelpp, we still need to create: |
| :bulb: |
* a mesh file ( see magnetgeo)
* a cfg file for
  |


You can also use directly the magnetdb. To do so:

```bash
python -m python_magnetsetup.cli --magnet HL-test --method cfpdes --time static --geom Axi --model thmagel  --cooling mean
python -m python_magnetsetup.cli --magnet M9Bitters --method cfpdes --time static --geom Axi --model thmagel  --cooling mean
```

| :bulb:  |To use the magnetdb directly, you shall update environment variables in `settings.env` to reflect your configuration.
| |
| ```bash
URL_API = 'http://localhost:8000/api'
MATGNETSETUP_PATH = "/usr/share/magnetsetup/magnetsetup.json"
DATA_REPO = "/data"
COMPUTE_SERVER = kelvin
VISU_SERVER = kelvin
``` |

