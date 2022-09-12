import math
import os

import matplotlib.pyplot as plt
import numpy as np

from matplotlib import cm

import examplefunctions as ef
from context import hotspin


def plot2Dsweep(summary_file, save=True, plot=True, title=None,
    col_x=None, col_y=None, name_x=None, name_y=None, transform_x=None, transform_y=None):
    ''' The file <summary_file> should be one that is generated by Sweep.load_results(). '''
    data = hotspin.utils.Data.load(summary_file)
    colnames = [group[0] for group in data.metadata["sweep"]["groups"]]
    var_x = colnames[1] if col_x is None else col_x
    var_y = colnames[0] if col_y is None else col_y
    df = data.df.sort_values([var_y, var_x], ascending=[True, True])
    y_vals, x_vals = df[var_y].unique(), df[var_x].unique()
    K, G = [], []
    for val_y, dfi in data.df.groupby(var_y):
        Ki, Gi = [], []
        for val_x, dfj in dfi.groupby(var_x):
            Ki.append(int(dfj["K"].iloc[0]))
            Gi.append(int(dfj["G"].iloc[0]))
        K.append(Ki)
        G.append(Gi)
    K, G = np.asarray(K), np.asarray(G)
    Q = K - G

    ## PLOTTING
    cmap = cm.get_cmap('viridis').copy()
    # cmap.set_under(color='black')
    hotspin.plottools.init_fonts()
    fig = plt.figure(figsize=(10, 4))

    if transform_x is not None: x_vals = transform_x(x_vals)
    if transform_y is not None: y_vals = transform_y(y_vals)
    if name_x is None: name_x = var_x
    if name_y is None: name_y = var_y
    x_lims = [(3*x_vals[0] - x_vals[1])/2] + [(x_vals[i+1] + x_vals[i])/2 for i in range(len(x_vals)-1)] + [3*x_vals[-1]/2 - x_vals[-2]/2]
    y_lims = [(3*y_vals[0] - y_vals[1])/2] + [(y_vals[i+1] + y_vals[i])/2 for i in range(len(y_vals)-1)] + [3*y_vals[-1]/2 - y_vals[-2]/2]
    X, Y = np.meshgrid(x_vals, y_vals)


    # PLOT 1: K
    ax1 = fig.add_subplot(1, 3, 1)
    ax1.set_xlabel(name_x)
    ax1.set_ylabel(name_y)
    ax1.set_title("K")
    im1 = ax1.pcolormesh(X, Y, K, vmin=1.01, vmax=max(2, np.max(K)), cmap=cmap)
    plt.colorbar(im1, extend='min')

    # PLOT 2: G
    ax2 = fig.add_subplot(1, 3, 2)
    ax2.set_xlabel(name_x)
    ax2.set_ylabel(name_y)
    ax2.set_title("G")
    im2 = ax2.pcolormesh(X, Y, G, vmin=1.01, vmax=max(2, np.max(G)), cmap=cmap)
    plt.colorbar(im2, extend='min')

    # PLOT 3: Q
    ax3 = fig.add_subplot(1, 3, 3)
    ax3.set_xlabel(name_x)
    ax3.set_ylabel(name_y)
    ax3.set_title("Q")
    im3 = ax3.pcolormesh(X, Y, Q, vmin=1.01, vmax=max(2, np.max(Q)), cmap=cmap)
    plt.colorbar(im3, extend='min')

    plt.suptitle(f'K, G and Q sweep' if title is None else title)
    plt.gcf().tight_layout()

    if save:
        save_path = os.path.splitext(summary_file)[0]
        hotspin.plottools.save_plot(save_path, ext='.pdf')
    if plot:
        plt.show()


def main_kernelquality():
    mm = hotspin.ASI.IP_Pinwheel(1e-6, 25, T=300, V=3.5e-22, energies=(hotspin.DipolarEnergy(), hotspin.ZeemanEnergy())) # Same volume as in 'RC in ASI' paper
    datastream = hotspin.io.RandomBinaryDatastream()
    inputter = hotspin.io.PerpFieldInputter(datastream, magnitude=1e-4, angle=math.pi/180*7, n=2)
    outputreader = hotspin.io.RegionalOutputReader(2, 2, mm)
    experiment = hotspin.experiments.KernelQualityExperiment(inputter, outputreader, mm)
    values = 11

    filename = f'results/{type(experiment).__name__}/{type(inputter).__name__}/{type(outputreader).__name__}_{mm.nx}x{mm.ny}_out{outputreader.nx}x{outputreader.nx}_in{values}values.npy'
    
    experiment.run(values, save=filename, verbose=True)
    print(experiment.results['rank'])
    np.set_printoptions(threshold=np.inf)

    result = np.load(filename)
    plt.imshow(result, interpolation='nearest')
    plt.title(f'{mm.nx}x{mm.ny} {type(mm).__name__}\nField {inputter.magnitude*1e3}\u2009mT $\\rightarrow$ rank {np.linalg.matrix_rank(result)}')
    plt.xlabel('Output feature')
    plt.ylabel(f'Input # ({values} values each)')
    plt.savefig(f'{os.path.splitext(filename)[0]}.pdf')
    plt.show()


if __name__ == "__main__":
    plot2Dsweep("results/Sweeps/Sweep_RC_ASI_sweep256_out50_in10_minimize.json",
        name_x="H [mT]", transform_x = lambda x: x*1e3,
        name_y="Interaction [a.u.]", transform_y = lambda x: x**-3/1.00060554e20
    )
    # main_kernelquality()
