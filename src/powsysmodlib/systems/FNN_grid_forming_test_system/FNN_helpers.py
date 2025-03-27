import sys

import powfacpy
from powfacpy.base.functional import set_attr_of_obj, set_attr_of_child

import Parameters.fnn_parameters as parameters

FONTSIZE = 23


def set_active_converters(pfi: powfacpy.PFBaseInterface, is_selfsync):
    """
    SelfSync or PF VSM
    """
    if is_selfsync:
        outserv_selfsync = 0
        outserv_pf_vsm = 1
    else:
        outserv_selfsync = 1
        outserv_pf_vsm = 0
    network_folder = pfi.get_single_obj(r"Network Model\Network Data\FNN grid")
    for conv_num in range(1, 3):
        # SelfSync
        pfi.set_attr(
            r"SelfSync " + str(conv_num),
            {"outserv": outserv_selfsync},
            parent_folder=network_folder,
        )
        pfi.set_attr(
            "DC Voltage Source " + str(conv_num),
            {"outserv": outserv_selfsync},
            parent_folder=network_folder,
        )
        pfi.set_attr(
            "PWM Converter " + str(conv_num),
            {"outserv": outserv_selfsync},
            parent_folder=network_folder,
        )
        # PF VSM
        pfi.set_attr(
            r"GF converter " + str(conv_num),
            {"outserv": outserv_pf_vsm},
            parent_folder=network_folder,
        )
        pfi.set_attr(
            r"VSM Control System " + str(conv_num),
            {"outserv": outserv_pf_vsm},
            parent_folder=network_folder,
        )


def set_selfsync_parameters(
    composite_model, converter, controller_params, converter_params, pfdi
):
    pfdi.set_parameters_of_dsl_models_in_composite_model(
        composite_model, controller_params, single_dict_for_all_dsl_models=True
    )
    set_attr_of_obj(converter, converter_params)


def set_all_pf_vsm_parameters(
    frame, converter, pf_vsm_parameters, pf_vsm_static_gen_parameters
):
    set_attr_of_obj(converter, pf_vsm_static_gen_parameters)
    dsl_objects_paths = [
        "Virtual Synchronous Machine",
        "Output Voltage Calculation",
        "Virtual Impedance",
        "Proportional Voltage Controller",
    ]
    for dsl_obj_path in dsl_objects_paths:
        set_attr_of_child(frame, dsl_obj_path, pf_vsm_parameters[dsl_obj_path])


def get_pf_vsm_frames(pfbi: powfacpy.PFBaseInterface):
    return pfbi.get_obj(r"Network Model\Network Data\FNN grid\VSM Control System*")


def get_selfsync_composite_models(pfbi: powfacpy.PFBaseInterface):
    elmcomp_1 = pfbi.get_single_obj(r"Network Model\Network Data\FNN grid\SelfSync 1")
    elmcomp_2 = pfbi.get_single_obj(r"Network Model\Network Data\FNN grid\SelfSync 2")
    return elmcomp_1, elmcomp_2


def get_pf_vsm_converters(pfbi: powfacpy.PFBaseInterface):
    return pfbi.get_obj(r"Network Model\Network Data\FNN grid\GF converter*")


def get_selfsync_converters(pfbi: powfacpy.PFBaseInterface):
    return pfbi.get_obj(r"Network Model\Network Data\FNN grid\PWM Converter*")


def set_standard_parameters(
    pf_vsm_frames,
    pf_vsm_converters,
    selfsync_converters,
    selfsync_composite_models,
    pfdi,
):
    for pf_vsm_frame, converter in zip(pf_vsm_frames, pf_vsm_converters):
        set_all_pf_vsm_parameters(
            pf_vsm_frame,
            converter,
            parameters.pf_vsm_parameters,
            parameters.pf_vsm_static_gen_parameters,
        )
    for selfsync_converter, selfsync_composite_model in zip(
        selfsync_converters, selfsync_composite_models
    ):
        set_selfsync_parameters(
            selfsync_composite_model,
            selfsync_converter,
            parameters.self_sync_parameters,
            parameters.self_sync_converter_parameters,
            pfdi,
        )


def plot_harmonic_voltage_source_results(pfpi):
    pfpi.set_active_plot("Magnitude", "§ Voltage source")
    pfpi.plot(
        r"Network Model\Network Data\FNN grid\harmonic_voltage_source_terminal",
        "m:u1",
    )
    pfpi.set_active_plot("Frequency", "§ Voltage source")
    pfpi.plot(
        r"Network Model\Network Data\FNN grid\harmonic_voltage_source_terminal",
        "m:fehz",
    )
    pfpi.set_active_plot("Angle", "§ Voltage source")
    pfpi.plot(
        r"Network Model\Network Data\FNN grid\harmonic_voltage_source_terminal",
        "m:phiu1",
    )
    pfpi.set_active_plot("Phases", "§ Voltage source")
    pfpi.plot(
        r"Network Model\Network Data\FNN grid\harmonic_voltage_source_terminal",
        ["m:u:A", "m:u:B", "m:u:C"],
    )


def plot_selfsync_variables(pfpi):
    converter_1 = pfpi.get_single_obj(
        r"Network Model\Network Data\FNN grid\PWM Converter 1"
    )
    converter_2 = pfpi.get_single_obj(
        r"Network Model\Network Data\FNN grid\PWM Converter 2"
    )

    pfpi.set_active_plot("Active power", "§ Power")
    pfpi.plot(
        converter_1,
        "m:Psum:busac",
    )
    pfpi.plot(
        converter_2,
        "m:Psum:busac",
    )
    pfpi.set_all_fonts_of_active_plot(fontsize=FONTSIZE)

    pfpi.set_active_plot("Reactive power", "§ Power")
    pfpi.plot(
        converter_1,
        "m:Qsum:busac",
    )
    pfpi.plot(
        converter_2,
        "m:Qsum:busac",
    )
    pfpi.set_all_fonts_of_active_plot(fontsize=FONTSIZE)

    pfpi.set_active_plot("Magnitude", "§ Current")
    pfpi.plot(
        converter_1,
        "m:i1:busac",
    )
    pfpi.plot(
        converter_2,
        "m:i1:busac",
    )
    pfpi.set_all_fonts_of_active_plot(fontsize=FONTSIZE)

    pfpi.set_active_plot("Phases", "§ Current")
    pfpi.plot(
        converter_1,
        "m:i:busac:A",
    )
    pfpi.plot(
        converter_1,
        "m:i:busac:B",
    )
    pfpi.plot(
        converter_1,
        "m:i:busac:C",
    )
    pfpi.set_all_fonts_of_active_plot(fontsize=FONTSIZE)

    # Plot current for paper on single page
    pfpi.set_active_plot("ABC currents converter 1 (SelfSync)", "§ Current Phases")
    pfpi.plot(converter_1, "m:i:busac:A", label="ia (SelfSync)")
    pfpi.plot(converter_1, "m:i:busac:B", label="ib (SelfSync)")
    pfpi.plot(converter_1, "m:i:busac:C", label="ic (SelfSync)")
    pfpi.set_all_fonts_of_active_plot(fontsize=FONTSIZE)

    pfpi.set_active_plot("ABC voltages converter 1 (SelfSync)", "§ Voltage Phases")
    pfpi.plot(converter_1, "m:u:busac:A", label="ua (SelfSync)")
    pfpi.plot(converter_1, "m:u:busac:B", label="ub (SelfSync)")
    pfpi.plot(converter_1, "m:u:busac:C", label="uc (SelfSync)")

    # Add further results variables
    pfpi.add_results_variable(
        converter_1, ["n:U:busac:A", "n:U:busac:B", "n:U:busac:C"]
    )
    pfpi.add_results_variable(
        converter_1, ["m:I:busac:A", "m:I:busac:B", "m:I:busac:C"]
    )


def plot_powerfactory_vsm_variables(pfpi):
    converter_1 = pfpi.get_single_obj(
        r"Network Model\Network Data\FNN grid\GF converter 1"
    )
    converter_2 = pfpi.get_single_obj(
        r"Network Model\Network Data\FNN grid\GF converter 2"
    )

    pfpi.set_active_plot("Active power", "§ Power")
    pfpi.plot(
        converter_1,
        "m:Psum:bus1",
    )
    pfpi.plot(
        converter_2,
        "m:Psum:bus1",
    )
    pfpi.set_active_plot("Reactive power", "§ Power")
    pfpi.plot(
        converter_1,
        "m:Qsum:bus1",
    )
    pfpi.plot(
        converter_2,
        "m:Qsum:bus1",
    )
    pfpi.set_all_fonts_of_active_plot(fontsize=FONTSIZE)

    pfpi.set_active_plot("Magnitude", "§ Current")
    pfpi.plot(
        converter_1,
        "m:i1:bus1",
    )
    pfpi.plot(
        converter_2,
        "m:i1:bus1",
    )
    pfpi.set_all_fonts_of_active_plot(fontsize=FONTSIZE)

    pfpi.set_active_plot("Phases", "§ Current")
    pfpi.plot(converter_1, "m:i:bus1:A")
    pfpi.plot(converter_1, "m:i:bus1:B")
    pfpi.plot(converter_1, "m:i:bus1:C")
    pfpi.set_all_fonts_of_active_plot(fontsize=FONTSIZE)

    # Plot current for paper on single page
    pfpi.set_active_plot("ABC currents converter 1 (PF-VSM)", "§ Current Phases")
    pfpi.plot(converter_1, "m:i:bus1:A", label="ia (PF-VSM)")
    pfpi.plot(converter_1, "m:i:bus1:B", label="ib (PF-VSM)")
    pfpi.plot(converter_1, "m:i:bus1:C", label="ic (PF-VSM)")
    pfpi.set_all_fonts_of_active_plot(fontsize=FONTSIZE)

    # Plot voltage on single page
    pfpi.set_active_plot("ABC voltages converter 1 (PF-VSM)", "§ Voltage Phases")
    pfpi.plot(converter_1, "m:u:bus1:A", label="ua (PF-VSM)")
    pfpi.plot(converter_1, "m:u:bus1:B", label="ub (PF-VSM)")
    pfpi.plot(converter_1, "m:u:bus1:C", label="uc (PF-VSM)")
    pfpi.set_all_fonts_of_active_plot(fontsize=FONTSIZE)

    # Add further results variables
    pfpi.add_results_variable(converter_1, ["n:U:bus1:A", "n:U:bus1:B", "n:U:bus1:C"])
    pfpi.add_results_variable(converter_1, ["m:I:bus1:A", "m:I:bus1:B", "m:I:bus1:C"])


def plot_comparison_of_converters(
    pfpi,
    selfsync_converter_1,
    pf_vsm_converter_1,
    time_span,
    results_obj_selfsync,
    results_obj_pf_vsm,
):

    pfpi.set_active_plot("Active power", "§ Power")
    pfpi.plot(
        selfsync_converter_1,
        "m:Psum:busac",
        results_obj=results_obj_selfsync,
        label="SelfSync",
    )
    pfpi.plot(
        pf_vsm_converter_1,
        "m:Psum:bus1",
        results_obj=results_obj_pf_vsm,
        label="PF-VSM",
    )
    pfpi.set_x_axis_range_of_active_plot(time_span)
    pfpi.active_graphics_page.DoAutoScaleY()
    pfpi.set_all_fonts_of_active_plot(fontsize=FONTSIZE)

    pfpi.set_active_plot("Reactive power", "§ Power")
    pfpi.plot(
        selfsync_converter_1,
        "m:Qsum:busac",
        results_obj=results_obj_selfsync,
        label="SelfSync",
    )
    pfpi.plot(
        pf_vsm_converter_1,
        "m:Qsum:bus1",
        results_obj=results_obj_pf_vsm,
        label="PF-VSM",
    )
    pfpi.set_x_axis_range_of_active_plot(time_span)
    pfpi.active_graphics_page.DoAutoScaleY()
    pfpi.set_all_fonts_of_active_plot(fontsize=FONTSIZE)
