"""
These standard parameters are used for the FNN and nordic system tests.
Note that for the validation, the parameters from SelfSyn.json/SelfSyncData.py are used (the
reason is that it was originally planned to read the parameters also in Matlab from JSON,
but unfortunately the Matlab version used does not support JSON import).

"""

import sys
import powfacpy
import powfacpy.engineering_helpers

# Basic
Snom_MVA = 150
Unom_kV = 15
current_limit_pu = 1

# VSM
Ta = 10
kp = 0.05
kq = 0.1
T_HP = 3

# Series impedance
uk = 5
copper_losses_pu = 0.01
copper_losses_kW = Snom_MVA * copper_losses_pu * 1000

r_series_pu, x_series_pu = (
    powfacpy.engineering_helpers.get_resistance_and_reactance_from_uk_and_copper_losses(
        uk, copper_losses_kW, Snom_MVA, Unom_kV
    )
)

self_sync_parameters = {
    "U_ki": 0.3852,
    "Q_ki": 0.1006731,
    "Sb": Snom_MVA * 1e6,
    "T_HP": T_HP * 1000,  # in ms not in s!
    "Ta": Ta,
    "Tu": 1,
    "Ub": 400,
    "actOC": 1,
    "actP": 1,
    "actQU": 0,
    "kp": kp,
    "kp_strich": 2,
    "kq": 0.1,
    "kq_strich": 0,
    "fb": 50,
    "db": 0.003,
    "Prio": 1,
    "Ri": r_series_pu,
    "Xi": x_series_pu,
}

self_sync_converter_parameters = {
    "uk": uk,
    "Pcu": copper_losses_kW,
    "psetp": 75,
    "Snom": Snom_MVA,
}

pf_vsm_parameters = {}
pf_vsm_parameters["Virtual Synchronous Machine"] = {
    "Ta": Ta,
    "Dp": 100,  # 1/kp, # works better with 100
    "w_c": 1 / T_HP,  # *1000,
}

pf_vsm_parameters["Output Voltage Calculation"] = {
    "Rseries": r_series_pu * 100,
    "Xseries": x_series_pu * 100,
    "i_max": current_limit_pu,
    "Mode": 1,
    "Tlpf_mag": 0.0003,
    "Tlpf_angle": 0,
}

pf_vsm_parameters["Virtual Impedance"] = {
    "Mode": 0,
    "x": 0,
    "r": 0,
}

pf_vsm_parameters["Proportional Voltage Controller"] = {
    "K": kq,
}

pf_vsm_static_gen_parameters = {
    "uk": uk,
    "Pcu": copper_losses_kW,
    "pgini": 75,
    "sgn": Snom_MVA,
}
