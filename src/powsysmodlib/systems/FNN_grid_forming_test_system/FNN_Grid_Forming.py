"""
Simulations of the FNN test system and its various test cases
according to 
"FNN Guideline: Grid forming behaviour of HVDC systems and DC-connected 
PPMs." VDE Verband der Elektrotechnik Elektronik Informationstechnik, 2020.

The converter controllers SelfSync and the VSM of the PowerFactory libary
are compared.

powfacpy is used (github.com/FraunhIEE-UniKassel-PowSysStability/powfacpy).
"""

# %%
%load_ext autoreload
%autoreload 2
import sys
from os import getcwd, makedirs
import pathlib

import pandas as pd

sys.path.append(r'C:\Program Files\DIgSILENT\PowerFactory 2023 SP5\Python\3.11')
import powerfactory
# powfacpy is required (see github.com/FraunhIEE-UniKassel-PowSysStability/powfacpy), download or install with pip
sys.path.insert(0,r'D:\User\seberlein\FraunhIEE-UniKassel-PowSysStability\powfacpy\src')
import powfacpy 
import powfacpy.applications
import powfacpy.applications.results

from FNN_helpers import *
import harmonic_voltage_source as harmonic_vs

app = powerfactory.GetApplication()
pfbi = powfacpy.PFBaseInterface(app)
pfdi = powfacpy.PFDynSimInterface(app)

pfbi.app.Show()
pfbi.app.ActivateProject(r'\seberlein\SelfSyncToPowerFactory\FNN_Guideline_Grid_Forming_enc')

pfri = powfacpy.applications.results.Results(app)

# Get controler frame and converter objects from PF network database
pf_vsm_frames = get_pf_vsm_frames(pfbi)
pf_vsm_converters = get_pf_vsm_converters(pfbi)
selfsync_converters = get_selfsync_converters(pfbi)
selfsync_composite_models = get_selfsync_composite_models(pfbi)

# %% Create Study Cases
try:
  app.Hide()
  pfsc = powfacpy.PFStudyCases(app)

  pfsc.parameter_values = {
      "test_scenario": [
          "Angular jump",
          "Angular jump + lin frequency change",
          "Voltage magnitude jump",
          "Negative sequence component",
          "Harmonics",
          "Subharmonics",
          "Grid impedance change",        
          "Islanding",
          "Voltage sag",
          "Voltage sag and islanding",
      ],
      "converter_type": [
          "SelfSync",
          "Comparison",
          "PF-VSM",
      ],
  }

  pfsc.anonymous_parameters = ["test_scenario", "converter_type"]
  pfsc.hierarchy = ["converter_type"]
  pfsc.active_grids = r"Network Model\Network Data\FNN grid"
  pfsc.parent_folder_study_cases = r"Study Cases\auto_generated"
  pfsc.add_variation_to_each_case = True
  pfsc.consecutively_number_case_names = False
  pfsc.delete_obj("*",parent_folder=pfsc.parent_folder_study_cases,error_if_non_existent=False,include_subfolders=True)
  pfsc.delete_obj("*",parent_folder="Network Model\Operation Scenarios",error_if_non_existent=False)
  pfsc.delete_obj("*",parent_folder="Network Model\Variations",error_if_non_existent=False)
  set_standard_parameters(pf_vsm_frames,pf_vsm_converters,selfsync_converters,selfsync_composite_models,pfdi)
  pfsc.apply_permutation()
  pfsc.create_cases()
finally:  
  app.Show()

# %% Set standard parameters for all scenarios
try:
  app.Hide()
  for scenario_num,study_case_obj in enumerate(pfsc.study_cases):
    study_case_obj.Activate()
    set_standard_parameters(pf_vsm_frames,pf_vsm_converters,selfsync_converters,selfsync_composite_models,pfdi)
finally:  
  app.Show()


# %% Iterate study cases to apply settings (to harmonic voltage source etc.) and plot 
try:
  app.Hide()
  # Set time span to be shown for each case
  time_spans = {
    "Angular jump": (6.9,8),    
    "Angular jump + lin frequency change": (0,14),  
    "Voltage magnitude jump": (0.95,1.3),
    "Negative sequence component": (0.95,1.3),
    "Harmonics": (0,10),
    "Subharmonics": (0,24),
    "Grid impedance change":  (0.9,5),
    "Islanding": (0.5,2),
    "Voltage sag": (0.95,1.4),
    "Voltage sag and islanding":(0.95,1.4),
  } 
  pfpi = powfacpy.PFPlotInterface(app)
  harmonic_source = harmonic_vs.HarmonicVoltageSource(
    r"Network Model\Network Data\FNN grid\harmonic_source",
    pfdi)

  for scenario_num,study_case_obj in enumerate(pfsc.study_cases):
    study_case_obj.Activate()
    harmonic_source.reset_symmetric_and_only_fundamental_frequency()   
    cominc = pfsc.app.GetFromStudyCase("Calculation of initial conditions.ComInc")
    cominc.Execute()
    pfdi.set_attr(cominc,{"iopt_sim":"ins","dtemt":0.0625, "iopt_fastchk": 0})
    comsim = pfsc.app.GetFromStudyCase("Run Simulation.ComSim")
    pfdi.set_attr(comsim,{"tstop":3})
    set_standard_parameters(pf_vsm_frames,pf_vsm_converters,selfsync_converters,selfsync_composite_models,pfdi)

    pfpi.clear_plot_pages()
    if not pfsc.get_value_of_parameter_for_case("converter_type",scenario_num) == "Comparison":
        
      if pfsc.get_value_of_parameter_for_case("test_scenario",scenario_num) == "Angular jump":
        params = {
          "phi1":[[1,0],[1.0001,-10],
            [3,-10],[3.0001,-40],
            [5,-40],[5.0001,-30],
            [7,-30],[7.0001,0]]  
        }
        harmonic_source.set_symmetric(params)
        pfdi.set_attr(comsim,{"tstop":9})

      elif pfsc.get_value_of_parameter_for_case("test_scenario",scenario_num) == "Angular jump + lin frequency change":
        
        params = {
          "f1": [
            [1,50],[1.5,51],[4,51], [4.5,50],
            [7,50],[7.5,49],[11,49],[11.5,50]],   
          "phi1": [
            [1,0],[1.0001,30],
            [4,30],[4.0001,0],
            [7,0],[7.0001,-30],
            [11,-30],[11.0001,0]]
          }   
        harmonic_source.set_symmetric(params)
        pfdi.set_attr(comsim,{"tstop":15})

      elif pfsc.get_value_of_parameter_for_case("test_scenario",scenario_num) == "Voltage magnitude jump":
        params = {
          "mag1": [
            [1,1],      [1.0001,0.95],
            [3,0.95],   [3.0001,1],
            [5,1],      [5.0001,0.9],
            [7,0.9],    [7.0001,1],
            [9,1],      [9.0001,1.05],
            [11,1.05],  [11.0001,1],
            [13,1],     [13.0001,1.1],
            [15,1.1],   [15.0001,1]]   
        }   
        harmonic_source.set_symmetric(params)
        pfdi.set_attr(comsim,{"tstop":17})

      elif pfsc.get_value_of_parameter_for_case("test_scenario",scenario_num) == "Grid impedance change":
          target = pfdi.get_single_obj(r"Network Model\Network Data\FNN grid\S1")
          pfdi.create_dyn_sim_event ("Switch 1.EvtSwitch",{"time":1,"p_target":target,"i_switch":0})
          target = pfdi.get_single_obj(r"Network Model\Network Data\FNN grid\S2")
          pfdi.create_dyn_sim_event ("Switch 2.EvtSwitch",{"time":3,"p_target":target,"i_switch":0})
          pfdi.set_attr(comsim,{"tstop":5})
          
      elif pfsc.get_value_of_parameter_for_case("test_scenario",scenario_num) == "Negative sequence component":
        # This case is not yet implemented because the harmonic source is not yet tested for negative sequences
        if False:  
          negative_sequence_magnitude_time_value_pairs = [
              [1,0],[1.0001,0.02],
          ]
          for dsl_obj in dsl_voltage_source_phases:
              powfacpy.PFDynSimInterface.set_dsl_obj_array(
                  dsl_obj,
                  negative_sequence_magnitude_time_value_pairs,
                  size_included_in_array=False,
                  array_num = 5)
          pfdi.set_attr(comsim,{"tstop":5})

      elif pfsc.get_value_of_parameter_for_case("test_scenario",scenario_num) == "Harmonics":
        params = {
          "f2":  [
            [1,0],[1.0001,100],
            [3,100],[3.0001,-250],
            [5,-250],[5.0001,950],
            [7,950],[7.0001,1550],],
          "mag2": [
              [1,0],[1.0001,0.02],
              [2,0.02],[2.0001,0],
              [3,0],[3.0001,0.02],
              [4,0.02],[4.0001,0],
              [5,0],[5.0001,0.02],
              [6,0.02],[6.0001,0],
              [7,0],[7.0001,0.02],
              [8,0.02],[8.0001,0],],
          "f3": [
              [3,0],[3.0001,350],], 
          "mag3": [
              [3,0],[3.0001,0.02],
              [4,0.02],[4.0001,0],]
        }   
        harmonic_source.set_symmetric(params)             
        pfdi.set_attr(comsim,{"tstop":10})

      elif pfsc.get_value_of_parameter_for_case("test_scenario",scenario_num) == "Subharmonics":
        params = {
          "f2":  [
            [1,0],[1.0001,5],
            [11,5],[11.0001,10],
            [21,10],[21.0001,15.9],],
          "mag2": [
            [1,0],[1.0001,0.02],
            [6,0.02],[6.0001,0],
            [11,0],[11.0001,0.02],
            [16,0.02],[16.0001,0],
            [21,0],[21.0001,0.02],],
          } 
        harmonic_source.set_symmetric(params)  
        pfdi.set_attr(comsim,{"tstop":24})

      elif pfsc.get_value_of_parameter_for_case("test_scenario",scenario_num) == "Islanding":
          target = pfdi.get_single_obj(r"Network Model\Network Data\FNN grid\S5")
          pfbi.set_attr(target,{"on_off":1})
          target = pfdi.get_single_obj(r"Network Model\Network Data\FNN grid\S1")
          pfdi.create_dyn_sim_event ("Switch 1.EvtSwitch",{"time":1,"p_target":target,"i_switch":0})
          target = pfdi.get_single_obj(r"Network Model\Network Data\FNN grid\S2")
          pfdi.create_dyn_sim_event ("Switch 2.EvtSwitch",{"time":1,"p_target":target,"i_switch":0})
          target = pfdi.get_single_obj(r"Network Model\Network Data\FNN grid\S3")
          pfdi.create_dyn_sim_event ("Switch 3.EvtSwitch",{"time":1,"p_target":target,"i_switch":0})
          pfdi.set_attr(comsim,{"tstop":5})

          # Set pf_vsm converters as referencemachines because otherwise they switch of in islanded operation
          for pf_vsm_conv in pf_vsm_converters:
            pf_vsm_conv.ip_ctrl = 1
            pf_vsm_conv.usetp = 0.983
            pf_vsm_conv.phiini = 7.65  

      elif pfsc.get_value_of_parameter_for_case("test_scenario",scenario_num) == "Short-circuit 3ph":
          target = pfdi.get_single_obj(r"Network Model\Network Data\FNN grid\T1")
          pfdi.create_dyn_sim_event ("Shc at T1.EvtShc",{"time":1,"p_target":target,"i_shc":0,"R_f":10})
          pfdi.create_dyn_sim_event ("Clear shc at T1.EvtShc",{"time":1.1,"p_target":target,"i_shc":4})
          pfdi.set_attr(comsim,{"tstop":5})

      elif pfsc.get_value_of_parameter_for_case("test_scenario",scenario_num) == "Short-circuit 2ph":
          target = pfdi.get_single_obj(r"Network Model\Network Data\FNN grid\T1")
          pfdi.create_dyn_sim_event ("Shc at T1.EvtShc",       {"time":1,"p_target":target,"i_shc":1})
          pfdi.create_dyn_sim_event ("Clear shc at T1.EvtShc", {"time":1.1,"p_target":target,"i_shc":4})
          pfdi.set_attr(comsim,{"tstop":5})

      elif pfsc.get_value_of_parameter_for_case("test_scenario",scenario_num) == "Voltage sag":
        params = {
          "mag1": [
            [1,1],[1.0001,0.3],
            [1.15,0.3],[1.15001,1]]
        }   
        harmonic_source.set_symmetric(params)      
        pfdi.set_attr(comsim,{"tstop":5})

      elif pfsc.get_value_of_parameter_for_case("test_scenario",scenario_num) == "Voltage sag and islanding":           
        params = {
          "mag1": [
            [1,1],[1.0001,0.3],
            [1.15,0.3],[1.15001,1]]
        }   
        harmonic_source.set_symmetric(params)

        target = pfdi.get_single_obj(r"Network Model\Network Data\FNN grid\S5")
        pfbi.set_attr(target,{"on_off":1})
        target = pfdi.get_single_obj(r"Network Model\Network Data\FNN grid\S1")
        pfdi.create_dyn_sim_event("Switch 1.EvtSwitch",{"time":1.15,"p_target":target,"i_switch":0,})
        target = pfdi.get_single_obj(r"Network Model\Network Data\FNN grid\S2")
        pfdi.create_dyn_sim_event ("Switch 2.EvtSwitch",{"time":1.15,"p_target":target,"i_switch":0,})
        target = pfdi.get_single_obj(r"Network Model\Network Data\FNN grid\S3")
        pfdi.create_dyn_sim_event ("Switch 3.EvtSwitch",{"time":1.15,"p_target":target,"i_switch":0,})
        pfdi.set_attr(comsim,{"tstop":5})

        # Set pf_vsm converters as referencemachines because otherwise they switch of in islanded operation
        for pf_vsm_conv in pf_vsm_converters:
          pf_vsm_conv.ip_ctrl = 1
          pf_vsm_conv.usetp = 0.983
          pf_vsm_conv.phiini = 7.65 

      # Plots  
      plot_harmonic_voltage_source_results(pfpi)
      if pfsc.get_value_of_parameter_for_case("converter_type",scenario_num) == "SelfSync":
        set_active_converters(pfsc,True)
        plot_selfsync_variables(pfpi)
        if "kp_strich" in pfsc.parameter_values:
          kp_strich = pfsc.get_value_of_parameter_for_case("kp_strich",scenario_num)
          for selfsync_ctrl in selfsync_controllers:
            selfsync_ctrl.kp_strich = kp_strich
      elif pfsc.get_value_of_parameter_for_case("converter_type",scenario_num) == "PF-VSM":
        set_active_converters(pfsc,False)
        plot_powerfactory_vsm_variables(pfpi)
        
finally:
  app.Show()


# %% Simulate all converter study cases and save results (using pickle)
 
try:
  # app.Hide()
  for scenario_num,study_case_obj in enumerate(pfsc.study_cases):
    converter_type = pfsc.get_value_of_parameter_for_case("converter_type",scenario_num)
    scenario = pfsc.get_value_of_parameter_for_case("test_scenario",scenario_num)
    if not pfsc.get_value_of_parameter_for_case("converter_type",scenario_num) == "Comparison":
      study_case_obj.Activate()
      
      comsim = pfsc.app.GetFromStudyCase("Run Simulation.ComSim")
      comsim.Execute()
      df_res = pfri.export_to_pandas()
      path = rf".\output\{converter_type}"
      pathlib.Path(path).mkdir(parents=True, exist_ok=True)
      df_res.to_pickle(rf"{path}\{scenario}") 
finally:
  app.Show()   


# %% Create plots in study cases that compare the two converters
try:
  app.Hide()
  makedirs(getcwd() + r"\Figures\FNN",exist_ok=True)
  selfsync_converter_1 = pfsc.get_single_obj(r"Network Model\Network Data\FNN grid\PWM Converter 1")
  pf_vsm_converter_1 = pfsc.get_single_obj(r"Network Model\Network Data\FNN grid\GF converter 1")
  # Set time span to be shown for each case
  time_spans = {
    "Angular jump": (6.9,8),    
    "Angular jump + lin frequency change": (0,14),  
    "Voltage magnitude jump": (0.95,1.3),
    "Negative sequence component": (0.95,1.3),
    "Harmonics": (0,10),
    "Subharmonics": (0,24),
    "Grid impedance change":  (0.9,5),
    "Islanding": (0.5,2),
    "Voltage sag": (0.95,1.4),
    "Voltage sag and islanding":(0.95,1.4),
  } 
  for scenario_num,study_case_obj in enumerate(pfsc.study_cases):
    test_scenario = pfsc.get_value_of_parameter_for_case("test_scenario",scenario_num)
    study_case_obj.Activate()
    converter_type = pfsc.get_value_of_parameter_for_case("converter_type",scenario_num) 
    if pfsc.get_value_of_parameter_for_case("converter_type",scenario_num) == "Comparison":
      pfpi.clear_plot_pages()
      # In case the influence of kp_strich is investigated
      if "kp_strich" in pfsc.parameter_values:
        kp_strich = pfsc.get_value_of_parameter_for_case("kp_strich",scenario_num)
        case_obj_selfsync =  pfsc.get_study_cases({
          "kp_strich":lambda x: x == kp_strich,
          "converter_type": lambda x: x == "SelfSync",
          "test_scenario": lambda x: x == test_scenario,
          })[0]
        results_obj_selfsync = pfsc.get_single_obj("All calculations",parent_folder=case_obj_selfsync)
        case_obj_pf_vsm =  pfsc.get_study_cases({
          "kp_strich":lambda x: x == kp_strich,
          "converter_type": lambda x: x == "PF-VSM",
          "test_scenario": lambda x: x == test_scenario,
          })[0]
        results_obj_pf_vsm = pfsc.get_single_obj("All calculations",parent_folder=case_obj_pf_vsm)
        plot_comparison_of_converters(pfpi,
          selfsync_converter_1,
          pf_vsm_converter_1,
          time_spans[test_scenario],
          results_obj_selfsync,
          results_obj_pf_vsm)  
        export_path = getcwd() + r"\Figures\FNN" + "\\" + test_scenario + " kp_strich_" + str(kp_strich) + " p and q comparison"
        pfpi.export_active_page(path=export_path)
      else:
        case_obj_selfsync =  pfsc.get_study_cases({
          "converter_type": lambda x: x == "SelfSync",
          "test_scenario": lambda x: x == test_scenario,
          })[0]
        results_obj_selfsync = pfsc.get_single_obj("All calculations",parent_folder=case_obj_selfsync)
        case_obj_pf_vsm =  pfsc.get_study_cases({
          "converter_type": lambda x: x == "PF-VSM",
          "test_scenario": lambda x: x == test_scenario,
          })[0]
        results_obj_pf_vsm = pfsc.get_single_obj("All calculations",parent_folder=case_obj_pf_vsm)
        plot_comparison_of_converters(pfpi,
          selfsync_converter_1,
          pf_vsm_converter_1,
          time_spans[test_scenario],
          results_obj_selfsync,
          results_obj_pf_vsm)  
        export_path = getcwd() + r"\Figures\FNN" + "\\" + test_scenario + " p and q comparison"
        pfpi.export_active_page(path=export_path)
    else:
      pfpi.set_active_plot("ABC currents converter 1 ("+converter_type+")","§ Current Phases")    
      pfpi.set_x_axis_range_of_active_plot(time_spans[test_scenario]) 
      pfpi.active_graphics_page.DoAutoScaleY()
      export_path = getcwd() + r"\Figures\FNN" + "\\" + test_scenario + " " + converter_type + " abc currents"  
      pfpi.export_active_page(path=export_path)

finally:
  app.Show()



# %%
