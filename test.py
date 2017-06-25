import simulationData as sim
from simulationData import Tools
import matplotlib.pyplot as plt
import numpy as np
import os


path = "./"
data = sim.SimulationData()

for current_file in os.listdir(path):
    if current_file.endswith(".h5"):
        data.loadData(os.path.join(path, current_file))
        data.loadGridData()
        frame = current_file.split('.')[1]
        print("Plotting for frame " + frame)

        Tools.interpolateRadialGrid(data, np.linspace(0.4, 49.5, 500))
        Tools.plotVariable(data, data.variables["rho"], "sonic_" + frame, log=True)
        Tools.plotSonicBarrier(data, "sonic_" + frame)
        Tools.plotVariable(data, data.variables["rho"], "field_" + frame, log=True)
        Tools.plotVelocityField(data, "field_" + frame, dx1=7, dx2=5, scale=60, width=0.001, overlay=True, x1_start=10)
        Tools.interpolateRadialGrid(data, np.linspace(0.4, 10.0, 500))
        Tools.plotVariable(data, data.variables["rho"], "field_zoom_" + frame, log=True)
        Tools.plotVelocityField(data, "field_zoom_" + frame, dx1=7, dx2=5, scale=50, width=0.002, overlay=True, x1_start=10)