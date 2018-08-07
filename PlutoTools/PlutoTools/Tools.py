import os
import pickle
import numpy as np
import scipy
from scipy import stats
from scipy.ndimage import map_coordinates
import matplotlib.pyplot as plt
from matplotlib import rc
# rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
rc('text', usetex=True)
np.set_printoptions(threshold=500)

from .Data import Data


class IonFraction:
    def __init__(self, t, zeta, nn, xe):
        self.t = t
        self.zeta = zeta
        self.nn = nn
        self.xe = xe
    def __str__(self):
        return "T: %e Zeta: %e nn: %e xe: %e" % (self.t, self.zeta, self.nn, self.xe)

class IonFractionCollection:
    def __init__(self):
        self.data = []
        self.n_temp = 0
        self.n_zeta = 0
        self.n_nn = 0
        self.d_temp = 0.0
        self.d_zeta = 0.0
        self.d_nn = 0.0
        self.start_temp = 0.0
        self.end_temp = 0.0
        self.start_zeta = 0.0
        self.end_zeta = 0.0
        self.start_nn = 0.0
        self.end_nn = 0.0
        self.temp_array = []
        self.zeta_array = []
        self.nn_array = []

    def loadIonData(self):
        loadedData = pickle.load(open("diff_results.p", "rb"))
        [self.temp_array.append(x.t) for x in loadedData]
        [self.zeta_array.append(x.zeta) for x in loadedData]
        [self.nn_array.append(x.nn) for x in loadedData]
        self.temp_array = np.array(sorted(list(set(self.temp_array))))
        self.zeta_array = np.array(sorted(list(set(self.zeta_array))))
        self.nn_array = np.array(sorted(list(set(self.nn_array))))

        self.data = np.zeros([20,20,20])
        for element in loadedData:
            i_t = np.where(self.temp_array == element.t)[0][0]
            i_zeta = np.where(self.zeta_array == element.zeta)[0][0]
            i_nn = np.where(self.nn_array == element.nn)[0][0]
            self.data[i_t][i_zeta][i_nn] = element.xe

        self.temp_array = np.log10(self.temp_array)
        self.zeta_array = np.log10(self.zeta_array)
        self.nn_array = np.log10(self.nn_array)
        self.n_temp = len(self.temp_array)
        self.n_zeta = len(self.zeta_array)
        self.n_nn = len(self.nn_array)
        self.d_temp = self.temp_array[1] - self.temp_array[0]
        self.d_zeta = self.zeta_array[1] - self.zeta_array[0]
        self.d_nn = self.nn_array[1] - self.nn_array[0]
        self.start_temp = self.temp_array[0]
        self.end_temp = self.temp_array[-1]
        self.start_zeta = self.zeta_array[0]
        self.end_zeta = self.zeta_array[-1]
        self.start_nn = self.nn_array[0]
        self.end_nn = self.nn_array[-1]

    def getIndicesForTempValue(self, x):
        l, r = 0, 0
        x = x - self.start_temp

        if x <= 0.0:
            l = 0
            r = 0
        elif x >= self.end_temp - self.start_temp:
            l = self.n_temp-1
            r = self.n_temp-1
        else:
            index = x / self.d_temp
            l = int(np.floor(index))
            r = int(np.ceil(index))

        return l, r

    def getIndicesForZetaValue(self, x):
        l, r = 0, 0
        x = x - self.start_zeta

        if x <= 0.0:
            l = 0
            r = 0
        elif x >= self.end_zeta - self.start_zeta:
            l = self.n_zeta-1
            r = self.n_zeta-1
        else:
            index = x / self.d_zeta
            l = int(np.floor(index))
            r = int(np.ceil(index))

        return l, r

    def getIndicesForNnValue(self, x):
        l, r = 0, 0
        x = x - self.start_nn

        if x <= 0.0:
            l = 0
            r = 0
        elif x >= self.end_nn - self.start_nn:
            l = self.n_nn-1
            r = self.n_nn-1
        else:
            index = x / self.d_nn
            l = int(np.floor(index))
            r = int(np.ceil(index))

        return l, r

    def interpolateIonFraction(self, temp, zeta, nn):
        x = np.log10(temp)
        y = np.log10(zeta)
        z = np.log10(nn)

        # Gives the adjacent indices
        xl, xr = self.getIndicesForTempValue(x)
        yl, yr = self.getIndicesForZetaValue(y)
        zl, zr = self.getIndicesForNnValue(z)


        # Corresponding values of the three variables
        x0 = self.temp_array[xl]
        x1 = self.temp_array[xr]
        y0 = self.zeta_array[yl]
        y1 = self.zeta_array[yr]
        z0 = self.nn_array[zl]
        z1 = self.nn_array[zr]

        # Computes the scaled difference coordinates between the lattice points
        x_d = (x - x0) / (x1 - x0)
        y_d = (y - y0) / (y1 - y0)
        z_d = (z - z0) / (z1 - z0)

        # Treating the boundary cases
        if x0 == x1:
            x_d = 0.0

        if y0 == y1:
            y_d = 0.0

        if z0 == z1:
            z_d = 0.0

        # Values of xe on the cube around the interpolation point
        c000 = self.data[xl][yl][zl]
        c001 = self.data[xl][yl][zr]
        c010 = self.data[xl][yr][zl]
        c011 = self.data[xl][yr][zr]
        c100 = self.data[xr][yl][zl]
        c101 = self.data[xr][yl][zr]
        c110 = self.data[xr][yr][zl]
        c111 = self.data[xr][yr][zr]

        # Interpolation along the temperature axis
        c00 = c000 * (1.0 - x_d) + c100 * x_d
        c01 = c001 * (1.0 - x_d) + c101 * x_d
        c10 = c010 * (1.0 - x_d) + c110 * x_d
        c11 = c011 * (1.0 - x_d) + c111 * x_d

        # Interpolation along the zeta axis
        c0 = c00 * (1.0 - y_d) + c10 * y_d
        c1 = c01 * (1.0 - y_d) + c11 * y_d

        # Interpolation along the nn axis
        c = c0 * (1.0 - z_d) + c1 * z_d

        return c



class Compute:

    def __init__(self, data):
        self.data = data

    def computeAbsoluteVelocities(self):
        return np.sqrt(self.data.variables["vx1"]**2 + self.data.variables["vx2"]**2)

    def computeMachNumbers(self):
        vabs = self.computeAbsoluteVelocities() * self.data.unitVelocity
        temp = self.computeTemperature()
        cs = np.sqrt(5.0/3.0 * self.data.kb * temp / (self.data.mu * self.data.mp))
        mach = vabs / cs
        return mach

    def computeAlfvenMachNumbers(self):
        vabs = self.computeAbsoluteVelocities()
        B = np.sqrt(self.data.variables["bx1"]**2 + self.data.variables["bx2"]**2)
        va = B / np.sqrt(self.data.variables["rho"])
        return vabs / va

    def computeSonicPoints(self):
        mach = self.computeMachNumbers()
        res = np.logical_and(mach > 0.995, mach < 1.005)
        res = np.where(res)
        x1 = self.data.x1[res[1]]
        x2 = self.data.x2[res[0]]
        x = x1 * np.sin(x2)
        y = x1 * np.cos(x2)
        sort = x.argsort()
        return x[sort], y[sort]

    def computeTemperature(self):
        kelvin = 1.072914e+05
        mu = 1.37125
        return self.data.variables["prs"] / self.data.variables["rho"] * kelvin * mu

    def computeElsasserNumbers(self, radius):

        collection = IonFractionCollection()
        collection.loadIonData()

        rho = self.data.variables["rho"] * self.data.unitNumberDensity
        r, th = np.meshgrid(self.data.x1, self.data.x2)
        dr, dth = np.meshgrid(self.data.dx1, self.data.dx2)
        rho_w = rho * dr * self.data.unitLength
        rho_column = np.copy(rho_w)
        for i in range(rho_w.shape[0]):
            for j in range(len(rho_w[i])):
                subc = np.sum(rho_w[i][:j])
                rho_column[i, j] = subc

        tau = np.exp(-rho_column * 2e-22)
        crossSection = 8.5e-23 * np.power(2.0, -2.81);
        absCoefficient = 0.686 * np.power(tau, -0.606) * np.exp(-1.778 * np.power(tau, -0.262));
        de = 37;
        xlum = 2.0e30 * 6.242e11
        xrayEnergy = 2e3
        zeta = 0.5 * xlum / (4.0 * np.pi * (r*self.data.unitLength)**2 * xrayEnergy) * crossSection * xrayEnergy / de * absCoefficient
        mask = np.isnan(zeta)
        zeta[mask] = 1e-18

        x_range = [0.0, 5.0, 2000]
        y_range = [-6.0, 6.0, 2000]
        temp = self.computeTemperature()
        bx1 = self.data.variables["bx1"] * self.data.unitMagneticFluxDensity
        bx2 = self.data.variables["bx2"] * self.data.unitMagneticFluxDensity
        #bx3 = self.data.variables["bx3"] * self.data.unitMagneticFluxDensity


        x, y, temp = Interpolate.interpolateToUniformGrid(self.data, temp, x_range, y_range)
        x, y, rho = Interpolate.interpolateToUniformGrid(self.data, rho, x_range, y_range)
        x, y, bx1 = Interpolate.interpolateToUniformGrid(self.data, bx1, x_range, y_range)
        x, y, bx2 = Interpolate.interpolateToUniformGrid(self.data, bx2, x_range, y_range)
         #x, y, bx3 = Interpolate.interpolateToUniformGrid(self.data, bx3, x_range, y_range)
        x, y, zeta = Interpolate.interpolateToUniformGrid(self.data, zeta, x_range, y_range)

        temp_H = Interpolate.interpolatePoint2D(x_range, y_range, temp, (radius, 0.0))
        H = self.pressureScaleHeightRadius(radius, temp_H)
        yy = np.linspace(-10*H, 10*H, 1000)
        e_numbers = []
        for i in yy:
            rho_i = Interpolate.interpolatePoint2D(x_range, y_range, rho, (radius, i))
            temp_i = Interpolate.interpolatePoint2D(x_range, y_range, temp, (radius, i))
            bz_i = np.absolute(Interpolate.interpolatePoint2D(x_range, y_range, bx2, (radius, i)))
            zeta_i = Interpolate.interpolatePoint2D(x_range, y_range, zeta, (radius, i))

            #print(i, rho_i, temp_i, bz_i, zeta_i)

            xe = collection.interpolateIonFraction(temp_i, zeta_i, rho_i)
            eta_ohm = 230.0 / xe * np.sqrt(temp_i);
            # eta_ohm = 1.268206e+17
            v_a = bz_i / np.sqrt(rho_i / self.data.unitNumberDensity * self.data.unitDensity)
            omega = np.sqrt(self.data.G * self.data.solarMass / (radius * self.data.unitLength)**3)
            elsasser_ohm = v_a**2 / (omega * eta_ohm)
            e_numbers.append(elsasser_ohm)
        return yy/H, np.array(e_numbers)

    def computeTotalMass(self, data):
        rho = self.data.variables["rho"]
        dV = (self.data.x1**2 - (self.data.x1 - self.data.dx1)**2) / (4.0*len(self.data.x2)) * 2.0 * np.pi * self.data.x1
        dV = np.tile(dV, (len(self.data.x2), 1))
        mass = rho * dV
        total = np.sum(mass) * self.data.unitDensity * self.data.unitLength**3 / self.data.solarMass
        return total

    def computeTotalMasses(self, path):
        masses = []
        times = []
        for file in os.listdir(path):
            if file.endswith(".h5"):
                data = Data(os.path.join(path, file))
                mass = self.computeTotalMass(data)
                times.append(float(data.time) * data.unitTimeYears)
                masses.append(mass)
                print("Mass for " + file + ": " + str(mass))
        return np.array(masses), np.array(times)

    def jacobiPotential(self, rho, prs, vx3, r):
        return prs / rho + 1 / r# - 0.5 * r**4 * vx3**2

    def computeJacobiPotential(self, x, y, vx3, rho, prs, x_range, y_range):
        # xticks = np.linspace(x_range[0], x_range[1], x_range[2])
        # yticks = np.linspace(y_range[0], y_range[1], y_range[2])
        potential = []


        for xx, yy in zip(x, y):
            rho_i = Interpolate.interpolatePoint2D(x_range, y_range, rho, (xx, yy))
            prs_i = Interpolate.interpolatePoint2D(x_range, y_range, prs, (xx, yy))
            vx3_i = Interpolate.interpolatePoint2D(x_range, y_range, vx3, (xx, yy))
            r = np.linalg.norm((xx, yy))
            potential.append(self.jacobiPotential(rho_i, prs_i, vx3_i, r)[0])
        return potential

    def computeStreamline(self, point, x, y, vx1, vx2, vx3, rho, prs, x_range, y_range, limit):
        # print(Tools.singlePointInterpolation(0, p0, vx1, vx2, x_range, y_range))
        # vx, vy = np.ravel(self.data.variables["vx1"]), np.ravel(self.data.variables["vx2"])

        p0 = point
        t0 = 0.0
        t1 = 1000
        # print(Tools.singlePointInterpolation(t0, p0, vx1, vx2, x_range, y_range))
        solver = scipy.integrate.ode(Interpolate.singlePointInterpolation)
        solver.set_integrator("vode", rtol=1e-10)
        solver.set_f_params(vx1, vx2, x_range, y_range)
        solver.set_initial_value(p0, t0)

        # mimics the wind launching front
        #H = 4.75 * self.pressureScaleHeightFlat()
        #xticks = self.data.x1

        x, y = [], []
        vabs = np.sqrt(vx1**2 + vx2**2)

        #while solver.y[1] > Interpolate.interpolatePoint(xticks, H, solver.y[0]):
        while Interpolate.interpolatePoint2D(x_range, y_range, vabs, (solver.y[0], solver.y[1])) > limit:
            solver.integrate(t1, step=True)
            x1 = solver.y[0]
            x2 = solver.y[1]
            x.append(x1)
            y.append(x2)
            #print(x1, x2)
            # print(Interpolate.interpolatePoint2D(x_range, y_range, vabs, (x1, x2)))
            # print(solver.y)
        print(solver.y)
        #print("Computing Jacobi potential...")
        #potential = self.computeJacobiPotential(x, y, vx3, rho, prs, x_range, y_range)
        potential = 0.0
        return solver.y[0], potential

    def computeRadialMassLosses(self, resolution=1000, limit=4e-4, start=100):
        computeLimit = int(len(self.data.dx1) * 0.99)
        rho = self.data.variables["rho"][:,computeLimit] * self.data.unitDensity
        vx1 = self.data.variables["vx1"][:,computeLimit] * self.data.unitVelocity
        temp = self.computeTemperature()[:,computeLimit]
        tempRange = [i for i,v in enumerate(temp) if v > 1000 and vx1[i] > 0]
        tempRange = range(min(tempRange), max(tempRange))
        r = self.data.x1[computeLimit]
        theta = self.data.x2[tempRange]

        surface = 0.5*np.pi / len(self.data.x2) * r**2 * 2.0 * np.pi * self.data.unitLength**2
        losses = surface * rho[tempRange] * vx1[tempRange] * self.data.year / self.data.solarMass
        x_start = r * np.sin(theta)
        y_start = r * np.cos(theta)

        trans = Transform(self.data)

        x, y = trans.polarCoordsToCartesian()
        vx1, vx2 = trans.transformVelocityFieldToCylindrical()
        x_range = [1, 100, resolution]
        y_range = [0, 100, resolution]
        x, y, vx1 = Interpolate.interpolateToUniformGrid(self.data, vx1, x_range, y_range)
        x, y, vx2 = Interpolate.interpolateToUniformGrid(self.data, vx2, x_range, y_range)
        x, y, vx3 = Interpolate.interpolateToUniformGrid(self.data, self.data.variables["vx3"], x_range, y_range)
        x, y, rho = Interpolate.interpolateToUniformGrid(self.data, self.data.variables["rho"], x_range, y_range)
        x, y, prs = Interpolate.interpolateToUniformGrid(self.data, self.data.variables["prs"], x_range, y_range)
        # x, y, temp = Interpolate.interpolateToUniformGrid(self.data, self.computeTemperature(), x_range, y_range)


        vx1 = -vx1
        vx2 = -vx2

        losses = losses[start:]
        x_start = x_start[start:]
        y_start = y_start[start:]

        radii = []
        potentials = []

        for i, j in zip(x_start, y_start):
            radius, potential = self.computeStreamline((i, j), x, y, vx1, vx2, vx3, rho, prs, x_range, y_range, limit)
            radii.append(radius)
            potentials.append(potential)

        return radii, losses, potentials

    def computeMassLoss(self, data):
        computeLimit = int(len(data.dx1) * 0.99)
        rho = data.variables["rho"][:,computeLimit] * data.unitDensity
        vx1 = data.variables["vx1"][:,computeLimit] * data.unitVelocity
        temp = self.computeTemperature()[:,computeLimit]
        tempRange = [i for i,v in enumerate(temp) if v > 500 and vx1[i] > 0]
        #tempRange = range(min(tempRange), max(tempRange))
        surface = 0.5*np.pi / len(data.x2) * data.x1[computeLimit]**2 * 2.0 * np.pi * data.unitLength**2
        massLoss = surface * rho[tempRange] * vx1[tempRange] * data.year / data.solarMass
        totalMassLoss = np.sum(massLoss)
        return totalMassLoss

    def computeMassLosses(self, path, frameRange):
        losses = []
        times = []
        for file in os.listdir(path):
            if file.endswith(".h5"):
                frameIndex = int(file.split('.')[1])
                if frameIndex in frameRange:
                    data = Data(os.path.join(path, file))
                    loss = self.computeMassLoss(data)
                    times.append(float(data.time) * data.unitTimeYears)
                    losses.append(loss)
                    print("Massflux for " + file + ": " + str(loss))
        return losses, times

    def plotMassLosses(self, path, filename="losses.eps"):
        losses, times = self.computeMassLosses(path)
        losses = np.array(losses, dtype=np.double)
        times = np.array(times, dtype=np.double)

        key = times.argsort()
        times = times[key]
        losses = losses[key]
        np.savetxt("losses.dat", (times, losses))

        plt.rc('text', usetex=True)
        plt.rc('font', family='serif')
        plt.semilogy(times, losses)
        plt.xlabel(r't [yr]')
        plt.ylabel(r'$\dot{M}_w $ [$\frac{M_{\odot}}{\mathrm{yr}}$]')
        plt.ylim(5e-9, 2e-8)
        plt.savefig(filename)

    def averageFrames(self, path, variable, frameRange):
        frames = []

        for filename in os.listdir(path):
            if filename.endswith(".h5"):
                frameIndex = int(filename.split('.')[1])
                if frameIndex in frameRange:
                    print("Averaging " + str(variable) + " frame: " + str(frameIndex))
                    data = Data(os.path.join(path, filename))
                    frames.append(data.variables[variable])
        frames = np.array(frames)
        averaged = np.mean(frames, axis=0)
        return averaged

    def pressureScaleHeightRadius(self, radius, temp):
        cs = np.sqrt(self.data.kb * temp / (self.data.mu * self.data.mp)) / self.data.unitVelocity
        omega = np.sqrt(1.0 / radius**3)
        return cs / omega

    def pressureScaleHeight(self):
        temp = self.computeTemperature()
        cs = np.sqrt(self.data.kb * temp / (self.data.mu * self.data.mp)) / self.data.unitVelocity
        trans = Transform(self.data)
        x, y = trans.polarCoordsToCartesian()
        omega = np.sqrt(1.0 / x**3)
        H = cs / omega
        return H

    def pressureScaleHeightFlat(self):
        temp = self.computeTemperature()
        cs = np.sqrt(self.data.kb * temp / (self.data.mu * self.data.mp)) / self.data.unitVelocity
        trans = Transform(self.data)
        x, y = trans.polarCoordsToCartesian()
        omega = np.sqrt(1.0 / x**3)
        H = cs / omega
        return np.power(H[-1], 4.33/5.0)



class Transform:

    def __init__(self, data):
        self.data = data

    def transformVelocityFieldToCylindrical(self):
        vx1 = self.data.variables["vx1"]
        vx2 = self.data.variables["vx2"]
        x2 = np.transpose(np.tile(self.data.x2, (len(self.data.x1), 1)))

        vx1_t = vx1 * np.sin(x2) + vx2 * np.cos(x2)
        vx2_t = vx1 * np.cos(x2) - vx2 * np.sin(x2)
        return vx1_t, vx2_t

    def transformMagneticFieldToCylindrical(self):
        bx1 = self.data.variables["bx1"]
        bx2 = self.data.variables["bx2"]
        x2 = np.transpose(np.tile(self.data.x2, (len(self.data.x1), 1)))

        bx1_t = bx1 * np.sin(x2) + bx2 * np.cos(x2)
        bx2_t = bx1 * np.cos(x2) - bx2 * np.sin(x2)
        return bx1_t, bx2_t

    def polarCoordsToCartesian(self):
        r_matrix, th_matrix = np.meshgrid(self.data.x1, self.data.x2)
        x = r_matrix * np.sin(th_matrix)
        y = r_matrix * np.cos(th_matrix)
        return x, y


class Interpolate:

    def __init__(self):
    	pass

    @staticmethod
    def interpolatePoint(ticks, data, point):
        f = scipy.interpolate.interp1d(ticks, data)
        return f(point)

    # Returns single interpolated value on a regular grid (faster than griddata)
    @staticmethod
    def singlePointInterpolation(t, p, vx1, vx2, x_range, y_range):
        pp = [[(p[1] - y_range[0]) * y_range[2] / (y_range[1] - y_range[0])],
                      [(p[0] - x_range[0]) * x_range[2] / (x_range[1] - x_range[0])]]
        pp = np.array(pp)
        return [map_coordinates(vx1, pp, order=1), map_coordinates(vx2, pp, order=1)]

    @staticmethod
    def interpolatePoint2D(x_range, y_range, data, p):
        pp = [[(p[1] - y_range[0]) * y_range[2] / (y_range[1] - y_range[0])],
                      [(p[0] - x_range[0]) * x_range[2] / (x_range[1] - x_range[0])]]
        pp = np.array(pp)
        return map_coordinates(data, pp, order=1)

    @staticmethod
    def interpolateRadialGrid(data, newTicks):
        for key, value in data.variables.items():
            x1 = data.x1
            interpolated = np.array(np.zeros(shape=(value.shape[0], len(newTicks))))

            for i in range(value.shape[0]):
                f = scipy.interpolate.interp1d(x1, value[i])
                interpolated[i] = f(newTicks)

            data.variables[key] = interpolated
        data.x1 = newTicks
        return data

    @staticmethod
    def interpolatePoint2DAlternative(x_range, y_range, data, p):
        pp = [[(p[0] - x_range[0]) * x_range[2] / (x_range[1] - x_range[0])],
              [(p[1] - y_range[0]) * y_range[2] / (y_range[1] - y_range[0])]]
        pp = np.array(pp)
        return map_coordinates(data, pp, order=1)

    @staticmethod
    def interpolateToUniformGrid(data, variable, x_range, y_range):
        t = Transform(data)
        x, y = t.polarCoordsToCartesian()
        x = np.ravel(x)
        y = np.ravel(y)
        variable = np.ravel(variable)
        points = np.column_stack((x, y))
        grid_x, grid_y = np.meshgrid(np.linspace(*x_range), np.linspace(*y_range))
        newVariable = scipy.interpolate.griddata(points, variable, (grid_x, grid_y))
        grid_r = np.sqrt(grid_x**2 + grid_y**2)
        newVariable[grid_r < 1.0] = np.nan
        return grid_x, grid_y, newVariable


class Tools:

    def __init__(self):
        pass

    @staticmethod
    def removeFilesWithStride(path, stride):
        for current_file in os.listdir(path):
            if current_file.endswith(".h5") or current_file.endswith(".xmf"):
                frame = int(current_file.split('.')[1])
                if frame % stride != 0:
                    print("deleting frame " + str(frame))
                    os.remove(os.path.join(path, current_file))
