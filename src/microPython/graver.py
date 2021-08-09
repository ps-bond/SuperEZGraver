# graver.py
# Collection of classes for threaded operation (which should make adding a UI in easier by decoupling input stage from output)

# microPython specific
import machine
from machine import Pin, PWM

# generic(ish)
import queue
import threading
import time

#  Class for the super EZ graver
class Graver(threading.Thread):

    __debug = True

    # Defaults
    outputPin = 0               #
    defaultPulseLength = 15     # ms
    maxFreq = 2500/60           # Hz - representation is Strokes Per Minute
    speedBias = 0.01            # ignore any readings below this and don't switch on
    pwmFreq = 1000              # max 1000
    pwmRange = 1023             # Will vary

    maxCumulativeOnTime = 2000  # ms
    coolingTime = 4

    # Init the PWM - primarily, turn it off if on
    # (code is run on first import)
 
    def __init__(self, speedQueue, powerQueue):

        self.currentSpeed = 0.0     # 0..1.0
        self.currentPower = 0.0     # 0..1.0
        self.pulseLength = self.defaultPulseLength    
        self.bias = self.speedBias

        self.speedQueue = speedQueue
        self.powerQueue = powerQueue

        self.pwmPin = PWM(Pin(self.outputPin))
        self.pwmPin.freq(self.pwmFreq)
        self.pwmPin.duty(0)

        self.__running = True

    def __readQueues(self):
        # Speed
        # lock
        if not self.speedQueue.empty():
            self.currentSpeed = self.speedQueue.get()
            if self.__debug:
                print("graver - speed read as ", (int)(self.currentSpeed * 100), "%")

            if self.currentSpeed < 0.0:
                self.currentSpeed = 0.0

            if self.currentSpeed > 1.0:
                self.currentSpeed = 1.0

        if not self.powerQueue.empty():
            self.currentPower = self.powerQueue.get()
            if self.__debug:
                print("graver - power read as ", (int)(self.currentPower * 100), "%")

            if self.currentPower < 0.0:
                self.currentPower = 0.0

            if self.currentPower > 1.0:
                self.currentPower = 1.0


    # These methods will probably go - threaded, after all.
    def setSpeed(self, speed):
        self.currentSpeed = speed

    def getSpeed(self):
        return self.currentSpeed

    def setPower(self, power):
        self.CurrentPower = power

    def getPower(self):
        return self.currentPower

    def terminate(self):
        self.__running = False

    def run(self):
        cumulativeOnTime = 0    # How man ms has the solenoid been powered on
        currentSPM = 0          # Current Strokes Per Minute
        lastSPM = 0             # Last set SPM (so we can see if it changed)

        while self.__running:
            self.__readQueues()

            # Divide by zero guard
            if self.currentSpeed > 0.0:
                offTime = (int)(1000/(self.maxFreq * self.currentSpeed)) - self.pulseLength
            else:
                # This will be detected in the next test of offTime
                offTime = 0.0

            if offTime <= self.pulseLength:
                if self.__debug:
                    print("\nOff time throttled - was ", offTime, "ms, now ", self.pulseLength)
                offTime = self.pulseLength # 50% overall duty cycle max

            currentSPM = 60 * 1000/(offTime + self.pulseLength)

            # Might do something else with the SPM, so not wrapping this in a debug test, just the print()
            # Only want to update if it changes - printing at even 115200 can get a bit slow
            # Arbitrary decision to only update if SPM changes by more than 5
            if abs(currentSPM - lastSPM) > 5:
                  if self.__debug:
                    print("SPM set to ", currentSPM)

            duty = (int)(self.currentPower * self.pwmRange)

            if self.currentSpeed > self.bias:
                # Switch on
                self.pwmPin(duty)
                # Wait
                time.sleep_ms(self.pulseLength)

                # Switch off
                self.pwmPin(0)
                 # Wait
                time.sleep_ms(offTime)

                if self.__debug:
                    print("*")

                # Guard the solenoid - it doesn't like being energised for long and there's not much detail on actual duty cycles
                # Obviously the faster it's run the quicker this pause will happen...
                cumulativeOnTime += self.pulseLength
                if cumulativeOnTime >= self.maxCumulativeOnTime:
                    #
                    # Signal user of pause
                    #
                    if self.__debug:
                        print("\n", self.maxCumulativeOnTime/1000, "s on-time reached; cooling...")
                    time.sleep(self.coolingTime)
                    cumulativeOnTime = 0
                    if self.__debug:
                        print("Cooling done")
            else:
                # sleep 100ms
                time.sleep_ms(50)   # 1/2 of sample rate for input
                if self.__debug:
                    print("Speed < bias")

            lastSPM = currentSPM

        # Cleanup - shutdown output
        if self.__debug:
            print("Shutdown")

# Check limitations of microPython + threads


# Input class - generic
class Input(threading.Thread):

    __debug = True
    sleepTime = 100 # ms

    def __init__(self, outputQueue):
        self.currentValue = 0.0
        self.outputQueue = outputQueue
        self.__running = True

    def terminate(self):
        self.__running = False

    def getValue():
        # Validation of imput value goes here
        return 0.0

    def run(self):
        while self.__running:
            # Read input
            self.currentValue = self.getValue()
            # Get queue lock
            # Push value to queue (NB do we interpret this to a fixed range? 0..1 for example?)
            # Release queue lock
            # sleep
            time.sleep_ms(self.sleepTime)

            if self.__debug:
                print("Current input reading for ", self, " = ", self.currentValue)

        # Cleanup

# Class for the input ADC
class ADCInput(Input):

    __debug = True

    def __init__(self, pin, range, outputQueue):
        # Configure the pin for ADC
        self.pin = pin
        self.range = range
        self.outputQueue = outputQueue
        self.currentValue = 0.0
        self.sleepTime = 100 # ms - sample rate
    
    def getValue():
        # Read ADC, validate input, return
        pass
