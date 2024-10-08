# Hotspice
<!-- markdownlint-disable MD033 -->

Hotspice is a kinetic Monte Carlo simulation package for thermally active artificial spin ices, using an Ising-like approximation: the axis and position of each spin is fixed, only their binary state can switch.
The time evolution can either follow the Néel-Arrhenius law of switching over an energy barrier in a chronological manner, or alternatively use Metropolis-Hastings to model the statistical behavior while making abstraction of the time variable.

## Dependencies

To create a new conda environment which only includes the necessary modules for hotspice, one can use the [`environment.yml`](environment.yml) file through the command

```shell
conda env create -n hotspice310 -f environment.yml
```

where `hotspice310` is the name of the new environment (because it was developed using Python 3.10).

### CuPy (GPU calculation, optional)

*By default, Hotspice runs on the CPU. To use the GPU, see [choosing between GPU or CPU](#choosing-between-gpu-or-cpu).*

On systems with CUDA support, Hotspice can run on the GPU. For this, it relies on the `CuPy` library to provide GPU-accelerated array computing for NVIDIA GPUs. When creating a conda environment as shown above, CuPy will be installed automatically.

If this fails, see the [CuPy installation guide](https://docs.cupy.dev/en/stable/install.html): the easiest method is likely to use the following `conda` command, as this automatically installs the appropriate version of the CUDA toolkit:

```shell
conda install -c conda-forge cupy
```

## Getting started

Hotspice is designed as a Python module, and can therefore simply be imported through `import hotspice`.
Several submodules provide various components, most of which are optional.
All of the strictly crucial classes and functions are provided in the default `hotspice` namespace, but other modules like `hotspice.ASI` provide wrappers and examples for ease of use.

### Creating a simple spin ice

To create a simulation, the first thing one has to do is to create a spin ice. This can be done by instantiating any of the ASI subclasses from the `hotspice.ASI` submodule, for example a 'diamond' pinwheel geometry:

```python
import hotspice
mm = hotspice.ASI.IP_Pinwheel(1e-6, 100) # Create the spin ice object
hotspice.gui.show(mm) # Display a GUI showing the current state of the spin ice
```

The meaning of the values `1e-6` and `100` requires a small introduction on how the spin ices are stored in memory.
Most data and parameters of a spin ice are stored as 2D arrays, for efficient calculation.
However, this also implies that the possible spin ice geometries are restricted to those that can be represented as a periodic structure on a square grid.
The geometry is then defined by leaving some spots on this grid empty, while filling others with a magnet and its relevant parameters like magnetic moment $M_{sat} V$ (`mm.moment`), energy barrier $E_B$ (`mm.E_B`), temperature $T$ (`mm.T`), orientation...

- The first parameter (`a=1e-6`) specifies a typical distance between two magnets. The exact meaning of this depends on the spin ice geometry being used: see [Available spin ices](#available-spin-ices) for the definition of `a` in the default ASI lattices.

- The second parameter in the initialization call (`n=100`) specifies the length of each axis of these underlying 2D arrays.
Hence, the spin ice in the example above will have 10000 available grid-points on which to put a magnet.
However, this 'diamond' pinwheel geometry can only be represented on a grid by leaving half of the available cells empty, so the simulation above actually contains 5000 magnets (see `mm.n`).

- Additional parameters can be used, for which we refer to the docstring of `hotspice.Magnets()`. In particular, the `params` parameter accepts a `hotspice.SimParams` instance which can set technical details for the spin ice, e.g. the update/sampling scheme to use, whether to use a reduced kernel...

Examples of usage for each of the ASI lattices, as well as examples of functions operating on these ASI objects, are provided in the 'examples' directory.

### Stepping in time

To perform a single simulation step, call `mm.update()`. The scheme used to perform this single step is determined by `mm.params.UPDATE_SCHEME` (possible schemes: `'Néel'`, `'Metropolis'`, `'Wolff'`).

To relax the magnetization to a (meta)stable state, call `mm.relax()` or `mm.minimize()` (the former is faster for large simulations but less accurate, the latter is faster for small simulations and follows the real relaxation order more closely).

### Applying input and reading output

More complex input-output simulations, e.g. for reservoir computing, can be performed using the `hotspice.io` and `hotspice.experiments` modules.

The `hotspice.io` module contains classes that apply external stimuli to the spin ice, or read the state of the spin ice in some manner.

The `hotspice.experiments` module contains classes to bundle many input/output runs and calculate relevant metrics from them, as well as classes to perform parameter sweeps.

### Performing a parameter sweep on multiple GPUs/CPUs

The `hotspice/scripts/ParallelJobs.py` script can be used to run a `hotspice.experiments.Sweep` on multiple GPUs or CPU cores. This sweep should be defined in a file that follows a structure similar to `examples/SweepKQ_RC_ASI.py`. Running `ParallelJobs.py` can be done

- either from the command line by calling `python ParallelJobs.py <sweep_file>`,
- or from an interactive python shell by calling `hotspice.utils.ParallelJobs(<sweep_file>)`.

### Choosing between GPU or CPU

*By default, hotspice runs on the CPU.* One can also choose to run hotspice on the GPU instead, e.g. for large simulations with over a thousand magnets, where the parallelism of GPU computing becomes beneficial.

At the moment when hotspice is imported through `import hotspice`, it

1) checks if the command-line argument `--hotspice-use-cpu` or `--hotspice-use-gpu` is present, and act accordingly. Otherwise,
2) the environment variable `'HOTSPICE_USE_GPU'` (default: `'False'`) is checked instead, and either the GPU or CPU is used based on this value.

*When invoking a script* from the command line, the cmd argument can be used. *Inside a python script*, however, it is discouraged to meddle with `sys.argv`. In that case, it is better to set the environment variable as follows:

```python
import os
os.environ['HOTSPICE_USE_GPU'] = 'True' # Must be type 'str'
import hotspice # Only import AFTER setting 'HOTSPICE_USE_GPU'!
```

*Note that the CPU/GPU choice must be made **BEFORE** the `import hotspice` statement* (and can thus be made only once)! <sub><sup>This is because behind-the-scenes, this choice determines which modules are imported by hotspice (either NumPy or CuPy), and it is not possible to re-assign these without significant runtime issues.</sup></sub>

## GUI

A graphical user interface is available to display and interact with the ASI. As shown earlier, it can be run by calling `hotspice.gui.show(mm)`, with `mm` the ASI object.

Buttons in the right sidebar allow the user to interact with the ASI by progressing through time. It is also possible to interact with the ASI at a granular level by clicking on the ASI plot directly (for more info on this, click the blue circled `i` to the bottom right of the ASI). The bottom left panel shows the elapsed time. The bottom central panel is used to change the main ASI view: it is possible to show the magnetization, domains, various energy contributions and barriers, as well as spatially resolved parameters like temperature, anisotropy and magnetic moment.

![Screenshot of GUI for a Pinwheel ASI with various domains.](./figures/GUI_Pinwheel_squarefour.PNG)

## Available spin ices

Several predefined geometries are available in hotspice.
They are listed below with a small description of their peculiarities.
They all follow the pattern `hotspice.ASI.<class>(a, n, nx=None, ny=None, **kwargs)`, where `n` is only required if either `nx` or `ny` is not specified.

### In-plane

| Class | Lattice | Parameters |
|---|:---:|---|
| `IP_Ising` | <img src="./figures/ASI_lattices/IP_Ising_8x8.png" alt="IP_Ising_8x8" width="200"/> | `a` is the distance between nearest neighbors. Full occupation. |
| `IP_Square` or `IP_Square_Closed` | <img src="./figures/ASI_lattices/IP_Square_5x5.png" alt="IP_Square_5x5" width="200"/> | `a` is the side length of a square, i.e. the side length of a unit cell. 1/2 occupation. |
| `IP_Square_Open` | <img src="./figures/ASI_lattices/IP_Square_Open_4.5x4.5.png" alt="IP_Square_Open_4.5x4.5" width="200"/> | Same as `IP_Square`, but with different edges, because the grid as a whole is rotated 45°. Full occupation. |
| `IP_Pinwheel` or `IP_Pinwheel_Diamond` | <img src="./figures/ASI_lattices/IP_Pinwheel_5x5.png" alt="IP_Pinwheel_5x5" width="200"/> | Same as `IP_Square`, but with each magnet rotated 45°. |
| `IP_Pinwheel_LuckyKnot` | <img src="./figures/ASI_lattices/IP_Pinwheel_LuckyKnot_4.5x4.5.png" alt="IP_Pinwheel_LuckyKnot_4.5x4.5" width="200"/> | Same as `IP_Square_Open`, but with each magnet rotated 45°. |
| `IP_Kagome` | <img src="./figures/ASI_lattices/IP_Kagome_5x3.png" alt="IP_Kagome_5x3" width="200"/> | `a` is the distance between opposing edges of a hexagon. 3/8 occupation. |
| `IP_Triangle` | <img src="./figures/ASI_lattices/IP_Triangle_5x3.png" alt="IP_Triangle_5x3" width="200"/> | Same as `IP_Kagome`, but with all magnets rotated 90°. |
| `IP_Cairo` | <img src="./figures/ASI_lattices/IP_Cairo_3x3.png" alt="IP_Cairo_3x3" width="200"/> | `a` is the side length of a pentagon. `beta` transforms the ice to Shakti, but this is not recommended in the Ising approximation. 1/5 occupation. |

### Out-of-plane

| Class | Lattice | Parameters |
|---|:---:|---|
| `OOP_Square` | <img src="./figures/ASI_lattices/OOP_Square_11x11.png" alt="OOP_Square_11x11" width="200"/> | `a` is the distance between nearest neighbors. Full occupation. |
| `OOP_Triangle` | <img src="./figures/ASI_lattices/OOP_Triangle_7x4.png" alt="OOP_Triangle_7x4" width="200"/> | `a` is the distance between nearest neighbors. 1/2 occupation. |
| `OOP_Honeycomb` | <img src="./figures/ASI_lattices/OOP_Honeycomb_4x7.png" alt="OOP_Honeycomb_4x7" width="200"/> | `a` is the distance between nearest neighbors. 2/5 occupation. |
| `OOP_Cairo` | <img src="./figures/ASI_lattices/OOP_Cairo_3x3.png" alt="OOP_Cairo_3x3" width="200"/> | `a` is the distance between nearest neighbors. 3/16 occupation. |
