install python_magnetsetup on machine or in singularity image
or install workflows on machine

```
scp -r python_magnetsetup/workflows machine
```

Then on machine:

```
singularity exec /home/singularity/feelpp-toolboxes-v0.110.0-alpha.3.sif \
    mpirun -np 2 python -m workflows.cli HL-test-cfpdes-thelec-Axi-sim.cfg --eps 1.e-5
```
