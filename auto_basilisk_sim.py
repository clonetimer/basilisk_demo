import os
import sys
import numpy as np
import matplotlib.pyplot as plt

from Basilisk.utilities import SimulationBaseClass, macros, orbitalMotion, simIncludeGravBody, simIncludeRW, simIncludeThruster
from Basilisk.simulation import spacecraft
from Basilisk.simulation import radiationPressure, exponentialAtmosphere
from Basilisk.simulation import reactionWheelStateEffector, thrusterDynamicEffector
from Basilisk.simulation import coarseSunSensor, imuSensor
from Basilisk.simulation import simpleNav

from Basilisk import __path__
bskPath = __path__[0]


def main():
    # === Auto Generated Basilisk Script ===

    # === Simulation Core ===
    scSim = SimulationBaseClass.SimBaseClass()
    scSim.SetProgressBar(True)
    
    simTaskName = 'simTask'
    simProcessName = 'simProcess'
    
    dynProcess = scSim.CreateNewProcess(simProcessName)
    simulationTimeStep = macros.sec2nano(10.0)  # 10 s step (example)
    dynProcess.addTask(scSim.CreateNewTask(simTaskName, simulationTimeStep))
    
    # Logging sampling time
    samplingTime = macros.sec2nano(1.0)
    

    # Flowchart Step: Init spacecraft
    # === Spacecraft ===
    scObject = spacecraft.Spacecraft()
    scObject.ModelTag = 'bsk-Sat'
    
    # Mass properties
    scObject.hub.mHub = 750.0
    I = [[900.0, 0.0, 0.0],
         [0.0, 800.0, 0.0],
         [0.0, 0.0, 600.0]]
    scObject.hub.IHubPntBc_B = I
    
    # Default initial state (can be overwritten by Orbit block)
    scObject.hub.r_CN_NInit = [[-6000000.0], [0.0], [0.0]]
    scObject.hub.v_CN_NInit = [[0.0], [-7500.0], [0.0]]
    scObject.hub.sigma_BNInit = [[0.1], [0.2], [-0.3]]
    scObject.hub.omega_BN_BInit = [[0.001], [-0.01], [0.03]]
    
    scSim.AddModelToTask(simTaskName, scObject)
    

    # Flowchart Step: Add Earth gravity
    # === Earth Gravity ===
    gravFactory = simIncludeGravBody.gravBodyFactory()
    earth = gravFactory.createEarth()
    earth.isCentralBody = True
    mu = earth.mu
    earth.useSphericalHarmonicsGravityModel(bskPath + '/supportData/LocalGravData/GGM03S.txt', 2)
    
    # Example: enable J2-only spherical harmonics model (path needs adjustment)
    # earth.useSphericalHarmonicsGravityModel(bskPath + '/supportData/LocalGravData/GGM03S-J2-only.txt', 2)
    
    gravFactory.addBodiesTo(scObject)
    

    # Flowchart Step: Set circular orbit
    # === Initial Orbit (circular, a=7000 km) ===
    oe = orbitalMotion.ClassicElements()
    oe.a = 7000e3
    oe.e = 0.0
    oe.i = 0.0
    
    oe.Omega = 48.2 * macros.D2R
    oe.omega = 347.8 * macros.D2R
    oe.f = 85.3 * macros.D2R
    rN, vN = orbitalMotion.elem2rv(mu, oe)
    oe = orbitalMotion.rv2elem(mu, rN, vN)
    scObject.hub.r_CN_NInit = rN
    scObject.hub.v_CN_NInit = vN
    

    # Flowchart Step: Add reaction wheel
    # === Reaction Wheels ===
    rwStateEffector = reactionWheelStateEffector.ReactionWheelStateEffector()
    rwStateEffector.ModelTag = 'ReactionWheels'
    scSim.AddModelToTask(simTaskName, rwStateEffector)
    
    rwFactory = simIncludeRW.rwFactory()
    rwFactory.create('Honeywell_HR16', [1, 0, 0], maxMomentum=50.0)
    rwFactory.create('Honeywell_HR16', [0, 1, 0], maxMomentum=50.0)
    rwFactory.create('Honeywell_HR16', [0, 0, 1], maxMomentum=50.0)
    rwFactory.addToSpacecraft(scObject.ModelTag, rwStateEffector, scObject)
    
    

    # Flowchart Step: Add SimpleNav
    # === SimpleNav ===
    sNavObject = simpleNav.SimpleNav()
    sNavObject.ModelTag = 'SimpleNavigation'
    scSim.AddModelToTask(simTaskName, sNavObject)
    sNavObject.scStateInMsg.subscribeTo(scObject.scStateOutMsg)
    

    # Flowchart Step: Start
    # (Unmatched step)

    # Flowchart Step: Enable logging
    # === State Logging ===
    dataLog = scObject.scStateOutMsg.recorder(samplingTime)
    scSim.AddModelToTask(simTaskName, dataLog)
    

    # Flowchart Step: Run simulation 200s
    # parsed run_time = 200.0 s


    # Flowchart Step: Plot states
    # (plot will be added after simulation)


    # Flowchart Step: End
    # (Unmatched step)

    # === Run Simulation ===
    simTime = macros.sec2nano(200.0)
    scSim.ConfigureStopTime(simTime)
    scSim.InitializeSimulation()
    scSim.ExecuteSimulation()

    # === Plot Position ===
    timeAxis = dataLog.times() * macros.NANO2SEC
    posData = dataLog.r_BN_N
    
    plt.figure(1)
    for idx in range(3):
        plt.plot(timeAxis, posData[:, idx])
    plt.xlabel('Time (s)')
    plt.ylabel('Position (m)')
    plt.legend(['x', 'y', 'z'])
    plt.grid(True)
    plt.savefig('position_xyz.png')
    

if __name__ == '__main__':
    main()
