# Copyright 2021 IRT Saint Exupéry, https://www.irt-saintexupery.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# Contributors:
#    INITIAL AUTHORS - initial API and implementation and/or initial documentation
#        :author: Jorge CAMACHO CASERO
#    OTHER AUTHORS   - MACROSCOPIC CHANGES
"""Utility to create basic signals in the form of numpy arrays.

It is useful to seamlessly generate input data usable by the FMUDiscipline.
"""
import pylab as plt
import scipy.signal as signal
from numpy import cos
from numpy import exp
from numpy import linspace
from numpy import pi
from numpy import random
from numpy import repeat
from numpy import sin
from numpy import tan


def constant_wave(x, amplitude=1):
    return amplitude


def sine_wave(x, amplitude=1, freq=1):
    return amplitude * sin(2 * pi * freq * x)


def cosine_wave(x, amplitude=1, freq=1):
    return amplitude * cos(2 * pi * freq * x)


def damped_sine_wave(x, amplitude=1, freq=1, k=1):
    return amplitude * exp(-k * x) * sin(2 * pi * freq * x)


def damped_cosine_wave(x, amplitude=1, freq=1, k=1):
    return amplitude * exp(-k * x) * cos(2 * pi * freq * x)


def triangle_wave(x, amplitude=1, freq=1, width=0.5):
    return amplitude * signal.sawtooth(2 * pi * freq * x, width=width)


def square_wave(x, amplitude=1, freq=1, duty=0.3):
    return amplitude * signal.square(2 * pi * freq * x, duty=duty)


def gausspulse_wave(
    x, amplitude=1, fc=1000, bw=0.5, bwr=-6, tpr=-60, retquad=False, retenv=False
):
    return amplitude * signal.gausspulse(x, fc, bw, bwr, tpr, retquad, retenv)


def chirp_wave(
    x, amplitude=1, f0=6, f1=1, t1=10, method="linear", phi=0, vertex_zero=True
):
    return amplitude * signal.chirp(x, f0, t1, f1, method, phi, vertex_zero)


def pattern_wave(x, amplitude=1, pattern=[0.0, 1.0, 0.0, 1.0, 0.0, 1.0]):
    # pattern =  [0., 1., 1., 0., 1., 0., 0., 1.]
    return amplitude * repeat(pattern, len(x) / len(pattern))


def noisy_wave(func, scale=1, size=0.9):
    sig_noise = random.normal(scale, size, func.shape)
    return func + sig_noise


def spikes(x, amplitude=5, k=0.01):
    sig = k * tan(cos(x) - 1)
    return amplitude * sig


def positive_spikes(x, amplitude=5, k=0.01):
    sig = abs(k * tan(cos(x) - 1))
    return amplitude * sig


def plot_waves(
    functions, xlabel=None, ylabel=None, sharex=True, sharey=True, fname="waves.png"
):
    """Plots a dictionary of functions."""
    n_subplots = len(functions)
    fig, axs = plt.subplots(n_subplots, sharex=sharex, sharey=sharey)
    for key, val in functions.items():
        key_index = list(functions).index(key)
        axs[key_index].plot(val, label=key)
        axs[key_index].title.set_text(key)
        # axs[key_index].legend(loc="upper right")
    plt.tight_layout()
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.show()
    fig.savefig(fname=fname)


if __name__ == "__main__":
    x = linspace(0, 5, 50)
    amp = 10
    freq = 1

    elementary_waves = {
        "sine_wave": sine_wave(x, amplitude=amp, freq=freq),
        "cosine_wave": cosine_wave(x, amplitude=amp, freq=freq),
        "triangle_wave": triangle_wave(x, amplitude=amp, freq=freq, width=0),
        "square_wave": square_wave(x, amplitude=amp, freq=freq, duty=0.5),
    }

    intermediate_waves = {
        "damped_sine_wave": damped_sine_wave(x, amplitude=amp, freq=freq, k=0.5),
        "damped_cosine_wave": damped_cosine_wave(x, amplitude=amp, freq=freq, k=0.5),
        "gausspulse_wave": gausspulse_wave(x, amplitude=amp),
        "chirp_wave": chirp_wave(x, amplitude=amp),
    }

    specialised_waves = {
        "spikes": spikes(x, amplitude=amp, k=0.025),
        "positive_spikes": positive_spikes(x, amplitude=amp, k=0.025),
        "pattern_wave": pattern_wave(
            x, pattern=[0.0, 1.0, 0.0, 1.0, 0.0, 1.0], amplitude=amp
        ),
        "noisi_wave": noisy_wave(pattern_wave(x, amplitude=amp)),
    }

    plot_waves(elementary_waves, xlabel=None, ylabel=None, fname="elem_waves.png")
    plot_waves(intermediate_waves, xlabel=None, ylabel=None, fname="inter_waves.png")
    plot_waves(specialised_waves, xlabel=None, ylabel=None, fname="spec_waves.png")
