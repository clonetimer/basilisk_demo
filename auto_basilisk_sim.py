
from Basilisk.utilities import SimulationBaseClass
from Basilisk.simulation import spacecraft
from Basilisk.simulation import thrusterDynamicEffector, coarseSunSensor
from Basilisk.simulation import reactionWheelStateEffector
from Basilisk.simulation import simpleNav
from Basilisk.utilities import orbitalMotion, simIncludeGravBody, macros


def main():
    scSim = SimulationBaseClass.SimBaseClass()
    simTaskName = 'simTask'
    proc = scSim.CreateNewProcess('simProc')
    task = scSim.CreateNewTask(simTaskName, int(1e9))
    proc.addTask(task)

    # Step: Start
    # TODO: no matching rule

    # Step: Init spacecraft
    scObject = spacecraft.Spacecraft()
    scSim.AddModelToTask(simTaskName, scObject)

    # Step: Add gravity
    gravFactory = simIncludeGravBody.gravBodyFactory()
    planet = gravFactory.createEarth()
    gravFactory.addBodiesTo(scObject)
    mu = planet.mu

    # Step: Run simulation
    # TODO: no matching rule

    # Step: Orbit 7000km
    oe = orbitalMotion.ClassicElements()
    oe.a = 7000e3
    oe.e = 0.00001
    oe.i = 0.0 * macros.D2R
    oe.Omega = 48.2 * macros.D2R
    oe.omega = 347.8 * macros.D2R
    oe.f = 85.3 * macros.D2R
    rN, vN = orbitalMotion.elem2rv(mu, oe)
    oe = orbitalMotion.rv2elem(mu, rN, vN) 
    scObject.hub.r_CN_NInit = rN
    scObject.hub.v_CN_NInit = vN

    # Step: End
    # TODO: no matching rule

    scSim.ConfigureStopTime(int(10e9))
    scSim.InitializeSimulation()
    scSim.ExecuteSimulation()

if __name__ == '__main__': main()