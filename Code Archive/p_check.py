#!/usr/bin/env python
"""
================================================
ABElectronics ADC Pi 8-Channel ADC demo

Requires python smbus to be installed
run with: python demo_readvoltage.py
================================================

Initialise the ADC device using the default addresses and sample rate,
change this value if you have changed the address selection jumpers

Sample rate can be 12,14, 16 or 18
"""

from __future__ import absolute_import, division, print_function, unicode_literals
from secant import secant

try:
    from ADCPi import ADCPi
except ImportError:
    print("Failed to import ADCPi from python system path")
    print("Importing from parent folder instead")
    try:
        import sys

        sys.path.append('..')
        from ADCPi import ADCPi
    except ImportError:
        raise ImportError(
            "Failed to import library from parent folder")


def p_check():
    """
    Main program function
    """

    adc = ADCPi(0x68, 0x69, 14)
    volts = 0
    try:
        # take an average reading of the voltage output over a second --- 14bit = 60 samples / sec
        for i in range(0, 60, 1):
            volts += adc.read_voltage(1)
        volts /= 60

        print('{0:.3f}'.format(volts), "v")

        # Testing showed a cubic relationship best fits the values for 0- 12 bar
        d = 0.4919 - volts
        p = lambda x: (-0.0006 * (x ** 3)) + (0.0133 * x ** 2) + (0.2584 * x) + d

        bar_calc = secant(p, -1, 14, 100)

        if bar_calc < 0:
            bar_calc = 0
        else:
            pass

        print('{0:.3f}'.format(bar_calc), " bar(g)")

        return bar_calc

    except Exception as e:
        print(e)
        print("pressure check has failed report to Pneumatrol for further analysis")
        return None


if __name__ == "__main__":
    p_check()
