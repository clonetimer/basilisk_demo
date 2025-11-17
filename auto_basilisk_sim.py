import os
import sys
import numpy as np
import matplotlib.pyplot as plt

from Basilisk.utilities import SimulationBaseClass, macros, orbitalMotion
from Basilisk.utilities import simIncludeGravBody, simIncludeRW, simIncludeThruster
from Basilisk.utilities import unitTestSupport
from Basilisk.simulation import spacecraft
from Basilisk.simulation import radiationPressure, exponentialAtmosphere
from Basilisk.simulation import reactionWheelStateEffector, thrusterDynamicEffector
from Basilisk.simulation import coarseSunSensor, imuSensor
from Basilisk.simulation import simpleNav
from Basilisk.fswAlgorithms import attTrackingError
from Basilisk.fswAlgorithms import inertial3D
from Basilisk.fswAlgorithms import mrpFeedback
from Basilisk.simulation import extForceTorque
from Basilisk.architecture import messaging



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
    

    # Flowchart Step: Init spacecraft
    # === Spacecraft ===
    scObject = spacecraft.Spacecraft()
    scObject.ModelTag = 'bsk-Sat'
    
    # Mass properties
    scObject.hub.mHub = 750.0
    I = [900., 0., 0.,
         0., 800., 0.,
         0., 0., 600.]
    scObject.hub.IHubPntBc_B = I
    
    # Default initial state (can be overwritten by Orbit block)
    scObject.hub.r_CN_NInit = [[-6000000.0], [0.0], [0.0]]
    scObject.hub.v_CN_NInit = [[0.0], [-7500.0], [0.0]]
    scObject.hub.sigma_BNInit = [[0.1], [0.2], [-0.3]]
    scObject.hub.IHubPntBc_B = unitTestSupport.np2EigenMatrix3d(I)
    # scObject.hub.omega_BN_BInit = [[0.001], [-0.01], [0.03]]
    
    scSim.AddModelToTask(simTaskName, scObject)
    

    # Flowchart Step: Add SimpleNav
    # === SimpleNav ===
    sNavObject = simpleNav.SimpleNav()
    sNavObject.ModelTag = 'SimpleNavigation'
    scSim.AddModelToTask(simTaskName, sNavObject)
    sNavObject.scStateInMsg.subscribeTo(scObject.scStateOutMsg)
    

    # Flowchart Step: Start
    # (Unmatched step)

    # Flowchart Step: Set simulation time
    simulationTime = 86400.0


    # Flowchart Step: Add external force torque
    # === External Disturbance ===
    extFTObject = extForceTorque.ExtForceTorque()
    extFTObject.ModelTag = 'externalDisturbance'
    scObject.addDynamicEffector(extFTObject)
    scSim.AddModelToTask(simTaskName, extFTObject)
    

    # Flowchart Step: Add inertial 3D nav
    # === Inertial 3D Navigation ===
    inertial3DObj = inertial3D.inertial3D()
    inertial3DObj.ModelTag = 'inertial3D'
    scSim.AddModelToTask(simTaskName, inertial3DObj)


    # Flowchart Step: Add MRP control
    # === Control ===
    # setup the attitude tracking error evaluation module
    attError = attTrackingError.attTrackingError()
    attError.ModelTag = 'attErrorInertial3D'
    scSim.AddModelToTask(simTaskName, attError)
    
    # setup the MRP Feedback control module
    mrpControl = mrpFeedback.mrpFeedback()
    mrpControl.ModelTag = 'mrpFeedback'
    scSim.AddModelToTask(simTaskName, mrpControl)
    mrpControl.K = 3.5
    mrpControl.Ki = -1  # make value negative to turn off integral feedback
    mrpControl.P = 30.0
    mrpControl.integralLimit = 2. / mrpControl.Ki * 0.1
    

    # Flowchart Step: Set num points
    numDataPoints = 400.0


    # Flowchart Step: Enable logging
    # === State Logging ===
    samplingTime = unitTestSupport.samplingTime(simulationTime, simulationTimeStep, numDataPoints)
    dataLog = scObject.scStateOutMsg.recorder(samplingTime)
    scSim.AddModelToTask(simTaskName, dataLog)
    attErrorLog = attError.attGuidOutMsg.recorder(samplingTime)
    scSim.AddModelToTask(simTaskName, attErrorLog)
    mrpLog = mrpControl.cmdTorqueOutMsg.recorder(samplingTime)
    scSim.AddModelToTask(simTaskName, mrpLog)
    

    # Flowchart Step: Create message
    # === Message ===
    # create the FSW vehicle configuration message
    # use the same inertia in the FSW algorithm as in the simulation
    vehicleConfigOut = messaging.VehicleConfigMsgPayload(ISCPntB_B=I)
    configDataMsg = messaging.VehicleConfigMsg().write(vehicleConfigOut)
    # connect the messages to the modules
    sNavObject.scStateInMsg.subscribeTo(scObject.scStateOutMsg)
    attError.attNavInMsg.subscribeTo(sNavObject.attOutMsg)
    attError.attRefInMsg.subscribeTo(inertial3DObj.attRefOutMsg)
    mrpControl.guidInMsg.subscribeTo(attError.attGuidOutMsg)
    extFTObject.cmdTorqueInMsg.subscribeTo(mrpControl.cmdTorqueOutMsg)
    mrpControl.vehConfigInMsg.subscribeTo(configDataMsg)
    

    # Flowchart Step: Plot results
    # (plot will be added after simulation)


    # Flowchart Step: End
    # (Unmatched step)

    # === Run Simulation ===
    scSim.InitializeSimulation()
    scSim.ConfigureStopTime(simulationTime)
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
    plt.savefig('temp/position_xyz.png')
    

if __name__ == '__main__':
    main()
