"""
Investigation of the nordic system with distributed 
generators. The synchronous machines are replaced by an
equivalent grid with distributed generators (grid-forming, 
grid-following, distributed synchronous machine).
The grid-forming controllers either have SelfSync control
or the PowerFactory VSM template controller.

powfacpy is used (github.com/FraunhIEE-UniKassel-PowSysStability/powfacpy).
"""

# %%
%load_ext autoreload
%autoreload 2
import sys
from os import getcwd
# Adjust your path to the PF app
sys.path.append(r'C:\Program Files\DIgSILENT\PowerFactory 2022 SP4\Python\3.10')
import powerfactory as powerfactory

# powfacpy is required (see github.com/FraunhIEE-UniKassel-PowSysStability/powfacpy), download or install with pip
sys.path.insert(0,r'D:\User\seberlein\Code\powfacpy\src')
import powfacpy 
from nordic_system_helpers import *

app = powerfactory.GetApplication()
pfbi = powfacpy.PFBaseInterface(app)
pfbi.app.Show()
app.ActivateProject(r'\seberlein\SelfSyncToPowerFactory\Nordic_System_Selfsync_Paper_enc')
# app.ActivateProject(r'\seberlein\SelfSyncToPowerFactory\Nordic_System_Selfsync_Paper')
pfni = powfacpy.PFNetworkInterface(app)
pfpi = powfacpy.PFPlotInterface(app)
pfdi = powfacpy.PFDynSimInterface(app)


# %% Add grids with distributed generators, activate the distributed gen. and set their parameters
converter_share = 0.9
grid_forming_converter_share = 0.5
try:
  app.Hide()
  pfbi.activate_study_case(r"Berechnungsfälle\Berechnungsfall")
  power_system_objs = add_grids_with_distributed_generators(
    pfbi, pfpi, pfni)
  switch_between_distributed_generation_and_original_synchronous_machines(
    power_system_objs,True)
  set_distributed_generator_parameters(
    pfbi,
    power_system_objs,
    converter_share,
    grid_forming_converter_share,
    "PowerFactory VSM")
finally:
  app.Show()


# %% Create study cases
try:  
  pfsc = powfacpy.PFStudyCases(app)
  pfsc.app.Hide()
  switch_between_distributed_generation_and_original_synchronous_machines(
      power_system_objs,True)  
  pfsc.parameter_values = {
      "Conv. share": [0.7],
      "Grid-forming share":[0.7],
      "Contingency":["Short circuit", ],#"Line outage",],
      "Conv. type": ["SelfSync", "PowerFactory VSM", "Comparison"],
  }
  pfsc.active_grids = pfbi.get_single_obj(r"Netzmodell\Netzdaten\Nordic")
  pfsc.parent_folder_study_cases = pfbi.create_in_folder("Berechnungsfälle","Paper.IntFolder")
  pfsc.parent_folder_scenarios = pfbi.create_in_folder("Betriebsfälle","Paper.IntFolder")
  pfsc.parent_folder_variations = pfbi.create_in_folder(r"Netzmodell\Netzdaten\Varianten","Paper.IntFolder")
  pfsc.clear_parent_folders()
  pfsc.hierarchy = ["Conv. type", "Contingency","Conv. share"]
  pfsc.anonymous_parameters = ["Contingency", "Conv. type"]
  pfsc.add_variation_to_each_case = True
  pfsc.apply_permutation()
  pfsc.create_cases()
  # The cominc should be executed once, otherwise PF behaves strangely
  for scenario_num,study_case_obj in enumerate(pfsc.study_cases):
    study_case_obj.Activate()
    cominc = pfsc.app.GetFromStudyCase("Calculation of initial conditions.ComInc")
    cominc.Execute()
    study_case_obj.Deactivate()
finally:
  app.Show()

# %% Set parameters
try:
  app.Hide()
  for scenario_num,study_case_obj in enumerate(pfsc.study_cases):
    study_case_obj.Activate()
    switch_between_distributed_generation_and_original_synchronous_machines(
      power_system_objs,True)
    converter_share = pfsc.get_value_of_parameter_for_case(
      "Conv. share",scenario_num)
    grid_forming_converter_share = pfsc.get_value_of_parameter_for_case(
      "Grid-forming share",scenario_num)
    set_distributed_generator_parameters(
      pfbi,
      power_system_objs,
      converter_share,
      grid_forming_converter_share,
      pfsc.get_value_of_parameter_for_case(
      "Conv. type",scenario_num))
finally:
  app.Show() 


# %% Create simulation events and plots, simulate
TIME_SPAN = (-0.02,1)
FONTSIZE = 23

try:  
  app.Hide()
  for scenario_num,study_case_obj in enumerate(pfsc.study_cases):
    study_case_obj.Activate()
    switch_between_distributed_generation_and_original_synchronous_machines(
      power_system_objs,True)
    converter_share = pfsc.get_value_of_parameter_for_case(
      "Conv. share",scenario_num)
    grid_forming_converter_share = pfsc.get_value_of_parameter_for_case(
      "Grid-forming share",scenario_num)
    set_distributed_generator_parameters(
      pfbi,
      power_system_objs,
      converter_share,
      grid_forming_converter_share,
      pfsc.get_value_of_parameter_for_case(
      "Conv. type",scenario_num))
    # Short circuit events
    if pfsc.get_value_of_parameter_for_case(
      "Contingency",scenario_num) == "Short circuit":
      shc_target = pfdi.get_single_obj(r"Netzmodell\Netzdaten\Nordic\L4012-4022")
      pfdi.create_event("short_circuit_"+shc_target.loc_name+".EvtShc",
        {"time":0.001, "i_shc":0, "p_target":shc_target, "shcLocation":50})
      pfdi.create_event("clear_short_circuit_"+shc_target.loc_name+".EvtShc",
        {"time":0.15, "i_shc":4, "p_target":shc_target})
      dg_grid_for_plotting = pfbi.get_single_obj(
        r"Netzmodell\Netzdaten\distributed_generators\distributed_gens_g04")
    # Line outage events
    elif pfsc.get_value_of_parameter_for_case(
      "Contingency",scenario_num) == "Line outage":  
      target_breaker = pfdi.get_single_obj(r"Netzmodell\Netzdaten\Nordic\4044\CB2")
      pfdi.create_event(target_breaker.loc_name + ".EvtSwitch",
        {"time":0.001, "i_switch":0, "p_target":target_breaker })
      dg_grid_for_plotting = pfbi.get_single_obj(
        r"Netzmodell\Netzdaten\distributed_generators\distributed_gens_g12") 
    dg_sm = pfbi.get_single_obj(r"dg_sm_*.ElmSym",
      parent_folder=dg_grid_for_plotting)
    dg_gfoll = pfbi.get_single_obj("dg_gfoll_conv_*.ElmPvsys",
      parent_folder=dg_grid_for_plotting)
    
    # Plot
    pfpi.clear_plot_pages()
    dg_gform_selfsync = pfbi.get_single_obj("dg_selfsync_conv_*.ElmVscmono",
        parent_folder=dg_grid_for_plotting)
    dg_gform_vsm = pfbi.get_single_obj("dg_pf_vsm_converter*.ElmGenstat",
        parent_folder=dg_grid_for_plotting)
    if pfsc.get_value_of_parameter_for_case("Conv. type",scenario_num) == "SelfSync":
      
      pfpi.set_active_plot("Power","§ Power")
      pfpi.plot(dg_gform_selfsync,"m:Psum:busac",label="P (SelfSync) [MW]")
      pfpi.plot(dg_gform_selfsync,"m:Qsum:busac",label="Q (SelfSync) [MVar]")
      pfpi.set_active_plot("Short-circuit terminal","§ Short Circuit")
      pfpi.plot(r"Netzmodell\Netzdaten\Nordic\4022\4022","m:u1",label="u (SelfSync) [pu]")

      pfpi.set_active_plot("ABC currents SelfSync","§ Currents")
      pfpi.plot(dg_gform_selfsync,"m:i:busac:A",label="ia")
      pfpi.plot(dg_gform_selfsync,"m:i:busac:B",label="ib")
      pfpi.plot(dg_gform_selfsync,"m:i:busac:C",label="ic")
      pfpi.set_x_axis_range_of_active_plot(TIME_SPAN)
      pfpi.active_graphics_page.DoAutoScaleY()
      pfpi.set_all_fonts_of_active_plot(fontsize=FONTSIZE)
      pfpi.get_title_obj_of_active_plot().showTitle = 0

      # Comparison with PF VSM
      pfpi.set_active_plot("Power","§ Power")
      results_obj_vsm = pfpi.get_single_obj(r"Berechnungsfälle\Paper\PowerFactory VSM\Short circuit\Conv. share_0.7\Grid-forming share _ 0.7\All calculations") 
      pfpi.plot(dg_gform_vsm,"m:Psum:bus1",results_obj=results_obj_vsm,label="P (PF-VSM) [MW]")
      pfpi.plot(dg_gform_vsm,"m:Qsum:bus1",results_obj=results_obj_vsm,label="Q (PF-VSM) [MVar]")

      pfpi.set_active_plot("Short-circuit terminal","§ Short Circuit")
      pfpi.plot(r"Netzmodell\Netzdaten\Nordic\4022\4022","m:u1",results_obj=results_obj_vsm,label="u (PF-VSM) [pu]")

      cominc = pfsc.app.GetFromStudyCase("Calculation of initial conditions.ComInc")
      pfdi.set_attr(cominc,{"iopt_sim":"ins","dtemt":0.0625, 
        "iopt_fastchk": 0, "tstart": -50})
      comsim = pfsc.app.GetFromStudyCase(".ComSim")
      pfdi.set_attr(comsim,{"tstop":1})
      comsim.Execute()
      
    elif pfsc.get_value_of_parameter_for_case("Conv. type",scenario_num) == "PowerFactory VSM":  
      dg_gform_vsm = pfbi.get_single_obj("dg_pf_vsm_converter*.ElmGenstat",
        parent_folder=dg_grid_for_plotting)
      
      pfpi.set_active_plot("Power","§ Power")
      pfpi.plot(dg_gform_vsm,"m:Psum:bus1") 
      pfpi.plot(dg_gform_vsm,"m:Qsum:bus1")
      pfpi.set_active_plot("Short-circuit terminal","§ Short Circuit")
      pfpi.plot(r"Netzmodell\Netzdaten\Nordic\4022\4022","m:u1")

      pfpi.set_active_plot("ABC currents PF-VSM","§ Currents")
      pfpi.plot(dg_gform_vsm,"m:i:bus1:A",label="ia")
      pfpi.plot(dg_gform_vsm,"m:i:bus1:B",label="ib")
      pfpi.plot(dg_gform_vsm,"m:i:bus1:C",label="ic")
      pfpi.set_x_axis_range_of_active_plot(TIME_SPAN)
      pfpi.active_graphics_page.DoAutoScaleY()
      pfpi.set_all_fonts_of_active_plot(fontsize=FONTSIZE)
      export_path = getcwd() + r"\Figures\nordic_system" + "\\" + "PF-VSM Currents"
      pfpi.get_title_obj_of_active_plot().showTitle = 0
      pfpi.export_active_page(path=export_path)
      
      cominc = pfsc.app.GetFromStudyCase("Calculation of initial conditions.ComInc")
      pfdi.set_attr(cominc,{"iopt_sim":"ins","dtemt":0.0625, 
        "iopt_fastchk": 0, "tstart": -50})
      comsim = pfsc.app.GetFromStudyCase(".ComSim")
      pfdi.set_attr(comsim,{"tstop":1})
      comsim.Execute()

    # Compare SelfSync and PF VSM
    elif pfsc.get_value_of_parameter_for_case("Conv. type",scenario_num) == "Comparison":
      results_obj_vsm = pfpi.get_single_obj(r"Berechnungsfälle\Paper\PowerFactory VSM\Short circuit\Conv. share_0.7\Grid-forming share _ 0.7\All calculations")
      results_obj_selfsync = pfpi.get_single_obj(r"Berechnungsfälle\Paper\SelfSync\Short circuit\Conv. share_0.7\Grid-forming share _ 0.7\All calculations")
      
      pfpi.set_active_plot("Active power","§ Power")
      pfpi.plot(dg_gform_selfsync,"m:Psum:busac",label="SelfSync",results_obj=results_obj_selfsync)
      pfpi.plot(dg_gform_vsm,"m:Psum:bus1",label="PF-VSM",results_obj=results_obj_vsm) 
      pfpi.set_x_axis_range_of_active_plot(TIME_SPAN)
      pfpi.active_graphics_page.DoAutoScaleY()
      pfpi.set_all_fonts_of_active_plot(fontsize=FONTSIZE)

      pfpi.set_active_plot("Reactive power","§ Power")
      pfpi.plot(dg_gform_selfsync,"m:Qsum:busac",label="SelfSync",results_obj=results_obj_selfsync)
      pfpi.plot(dg_gform_vsm,"m:Qsum:bus1",label="PF-VSM",results_obj=results_obj_vsm) 
      pfpi.set_x_axis_range_of_active_plot(TIME_SPAN)
      pfpi.active_graphics_page.DoAutoScaleY()
      pfpi.set_all_fonts_of_active_plot(fontsize=FONTSIZE)
      export_path = getcwd() + r"\Figures\nordic_system" + "\\" + "p and q comparison"
      pfpi.export_active_page(path=export_path)

    
finally:
  app.Show()


# %% Export plots
try:  
  # app.Hide()
  for scenario_num,study_case_obj in enumerate(pfsc.study_cases):
    if pfsc.get_value_of_parameter_for_case("Conv. type",scenario_num) == "SelfSync":
      export_path = getcwd() + r"\Figures\nordic_system" + "\\" + "SelfSync Currents"
      study_case_obj.Activate()
      pfpi.set_active_plot("ABC currents SelfSync","§ Currents")
      pfpi.autoscale()
      pfpi.export_active_page(path=export_path)
    elif pfsc.get_value_of_parameter_for_case("Conv. type",scenario_num) == "PowerFactory VSM":        
      export_path = getcwd() + r"\Figures\nordic_system" + "\\" + "PF-VSM Currents"
      study_case_obj.Activate()
      pfpi.set_active_plot("ABC currents PF-VSM","§ Currents")
      pfpi.autoscale()
      pfpi.export_active_page(path=export_path)
    elif pfsc.get_value_of_parameter_for_case("Conv. type",scenario_num) == "Comparison":
      export_path = getcwd() + r"\Figures\nordic_system" + "\\" + "p and q comparison"
      study_case_obj.Activate()
      pfpi.set_active_plot("Active power","§ Power")
      pfpi.autoscale()
      pfpi.export_active_page(path=export_path)
finally:
  app.Show()


# %% Validate the settings of distributed generators by comparing load flow results

try:
  app.Hide()
  pfsc.get_study_cases({"Conv. type": lambda x: x=="SelfSync"})[0].Activate()
  check_if_with_and_without_dg_gives_same_load_flow_result(
    pfbi,
    power_system_objs,
    max_allowed_voltage_deviation_pu=0.01)
finally:
  app.Show()
# %%
