import sys
sys.path.insert(0,r'D:\User\seberlein\Code\powfacpy\src')
import powfacpy 
import Parameters.fnn_parameters as parameters

def copy_nordic_system_op_point_a_consolidated_to_selfsynctosimulink_folder(
    pfbi: powfacpy.PFBaseInterface):
  """
  Takes the original nordic system project (with operating point a consoidated) and copies
  to the SelfSyncToSimulink folder. Desctivates the original results import.
  """
  project_op_point_a_consolidated = create_operating_point_a_consolidated_version_of_nordic_system_pf_project(
    pfbi,
    r"Nordic System\Nordic_Test_System_unchanged",
    r"Nordic System" 
  ) 
  user = pfbi.app.GetCurrentUser()
  target_project_folder = pfbi.get_single_obj("SelfSyncToSimulink",
      parent_folder = user)
  project_nordic_system_selfsync_paper = pfbi.copy_single_obj(
                      project_op_point_a_consolidated,
                      target_project_folder,
                      new_name="Nordic_System_Selfsync_Paper")
  # Deactivate original results import 
  project_nordic_system_selfsync_paper.Activate()
  pfbi.get_single_obj(r"Netzmodell\Netzdaten\Nordic\Original_Results").outserv = 1
  return project_nordic_system_selfsync_paper
  
def add_distributed_generators_template_grid_to_nordic_system_project(
    pfbi: powfacpy.PFBaseInterface,
    project_nordic_system):
  user = pfbi.app.GetCurrentUser()
  project_nordic_system.Activate()
  pfni = powfacpy.PFNetworkInterface(pfbi.app)
  dg_template_grid = pfbi.get_single_obj(
    r"SelfSyncToSimulink\distributed_generators_template_grid\distributed_generators_template_grid",
    parent_folder = user)
  pfbi.create_in_folder(r"Netzmodell\Netzdaten","distributed_generators.IntFolder")
  pfni.copy_grid(dg_template_grid,
                 r"Netzmodell\Netzdaten\distributed_generators",
                 "distributed_generators_template")

def create_operating_point_a_consolidated_version_of_nordic_system_pf_project(
        pfbi: powfacpy.PFBaseInterface,
        original_nordic_system_project,
        target_project_path):
  user = pfbi.app.GetCurrentUser()
  original_nordic_system_project = pfbi.get_single_obj(original_nordic_system_project,
      parent_folder = user)
  target_project_folder = pfbi.get_single_obj(target_project_path,
      parent_folder = user)  
  project_op_point_a_consolidated = pfbi.copy_single_obj(
        original_nordic_system_project,
        target_project_folder,
        new_name="Nordic_Test_Sys_Op_Point_A_Consolidated")
  project_op_point_a_consolidated.Activate()
  study_case = pfbi.get_single_obj(r"Berechnungsfälle\Berechnungsfall")
  study_case.Consolidate()
  scenario = pfbi.get_single_obj(r"Betriebsfälle\Operating point A") 
  scenario.Deactivate()
  scenario.Apply(0)
  pfbi.delete_obj(scenario)
  project_op_point_a_consolidated.Deactivate()
  return project_op_point_a_consolidated 
    
def add_grids_with_distributed_generators(
    pfbi: powfacpy.PFBaseInterface,
    pfpi: powfacpy.PFPlotInterface,
    pfni: powfacpy.PFNetworkInterface):
  """
  Adds a grid with distributed generators at each SM transformer HV terminal.
  """
  pfpi.clear_grid_diagrams()
  distributed_sm_library_folder = pfbi.create_in_folder("Bibliothek\Betriebsmitteltypen-Bibliothek","Distributed synchronous maschines.IntFolder")
  distributed_gfoll_trafo_library_folder = pfbi.create_in_folder("Bibliothek\Betriebsmitteltypen-Bibliothek","Distributed PV trafos.IntFolder")
  original_synchronous_machines = pfni.get_obj("g*.ElmSym",parent_folder=r"Netzmodell\Netzdaten\Nordic")
  distributed_gen_grids_folder = pfni.get_single_obj(r"Netzmodell\Netzdaten\distributed_generators")
  distributed_gens_grid_template = pfni.get_single_obj(r"distributed_generators_template",
    parent_folder = distributed_gen_grids_folder)
  distributed_gens_grid_template.Deactivate()
  (original_sm_trafos,  distributed_gen_grids, distributed_gen_synchronous_machines, 
   distributed_gen_gfoll_converters, gfoll_trafo_types,distributed_gen_selfsync_converters,
   distributed_gen_pf_vsm_converters) = [],[],[],[],[],[],[]

  for original_sm in original_synchronous_machines:
    # Add distributed generator grid at each HV terminal of the SM connecting transformers
    terminal = pfni.get_connected_terminal(original_sm)
    connected_elms = pfni.get_elements_connected_to_terminal(terminal)
    sm_trafo = pfni.get_by_condition(connected_elms,lambda x: "ElmTr" in x.GetClassName())[0]
    hv_terminal = sm_trafo.bushv.cterm
    distributed_gen_grid = pfni.copy_grid(distributed_gens_grid_template,
      distributed_gen_grids_folder,
      "distributed_gens_" + original_sm.loc_name) 
    connecting_trafo = pfni.get_single_obj("Connecting transformer.ElmTr*",
      parent_folder=distributed_gen_grid)
    copy_data_from_orgiginal_sm_trafo_to_connecting_trafo(pfni,connecting_trafo,sm_trafo,hv_terminal)  

    # Distributed generator settings and control 
    # Grid-following
    distributed_gen_gfoll_converter = pfni.get_single_obj(
      "distributed_gen_gfoll_converter.ElmPvsys",parent_folder=distributed_gen_grid)
    distributed_gen_gfoll_converter.loc_name = "dg_gfoll_conv_" + original_sm.loc_name
    gfoll_trafo_elm =  pfni.get_single_obj(
      "Trf PV Plant.ElmTr2",parent_folder=distributed_gen_grid)
    gfoll_trafo_type = pfni.copy_single_obj(
        gfoll_trafo_elm.typ_id,
        distributed_gfoll_trafo_library_folder,
        new_name="PV_trafo_" + original_sm.loc_name)
    gfoll_trafo_elm.typ_id = gfoll_trafo_type
    # SelfSync
    distributed_gen_selfsync_converter = pfni.get_single_obj(
      "distributed_gen_selfsync_converter.ElmVSCmono",parent_folder=distributed_gen_grid)
    distributed_gen_selfsync_converter.loc_name = "dg_selfsync_conv_" + original_sm.loc_name
    # PF VSM
    distributed_gen_pf_vsm_converter = pfni.get_single_obj(
      "distributed_gen_pf_vsm_converter",parent_folder=distributed_gen_grid)
    distributed_gen_pf_vsm_converter.loc_name = "dg_pf_vsm_converter" + original_sm.loc_name
    # Distributed SM
    dg_sm = pfni.get_single_obj("*.ElmSym",parent_folder=distributed_gen_grid)
    dg_sm.typ_id = pfbi.copy_single_obj(original_sm.typ_id,distributed_sm_library_folder)
    dg_sm.loc_name = "dg_sm_" + original_sm.loc_name
    add_dsl_frame_for_dg_sm(pfbi, distributed_gen_grid, original_sm, dg_sm)
    # Station controller for voltage control
    station_voltage_ctrl = pfbi.get_single_obj(
      "Station voltage control.ElmStactrl",parent_folder=distributed_gen_grid)
    station_voltage_ctrl.usetp = original_sm.usetp
    distributed_gen_grid.Activate() # If not activated once, it behaves strangely
    # Store the elements to be used later
    original_sm_trafos.append(sm_trafo)
    distributed_gen_grids.append(distributed_gen_grid)
    distributed_gen_gfoll_converters.append(distributed_gen_gfoll_converter)
    gfoll_trafo_types.append(gfoll_trafo_type)
    distributed_gen_synchronous_machines.append(dg_sm)
    distributed_gen_selfsync_converters.append(distributed_gen_selfsync_converter)
    distributed_gen_pf_vsm_converters.append(distributed_gen_pf_vsm_converter)
  return {
    "original_sm_trafos":original_sm_trafos,
    "original_synchronous_machines":original_synchronous_machines,
    "distributed_gen_grids": distributed_gen_grids,
    "distributed_gen_gfoll_converters": distributed_gen_gfoll_converters,
    "distributed_gen_gfoll_trafo_types": gfoll_trafo_types,
    "distributed_gen_synchronous_machines": distributed_gen_synchronous_machines,
    "distributed_gen_selfsync_converters": distributed_gen_selfsync_converters,
    "distributed_gen_pf_vsm_converters": distributed_gen_pf_vsm_converters,
  }

def copy_data_from_orgiginal_sm_trafo_to_connecting_trafo(
    pfni: powfacpy.PFNetworkInterface,
    connecting_trafo,
    sm_trafo,
    hv_terminal):
  connecting_trafo.typ_id = sm_trafo.typ_id
  connecting_trafo.nntap = sm_trafo.nntap # tap position
  substation = hv_terminal.GetParent()
  substation_main_busbar = pfni.get_single_obj(
    substation.loc_name + ".ElmTerm",parent_folder=substation)
  connecting_trafo.bushv = pfni.get_vacant_cubicle_of_terminal(substation_main_busbar,
    new_cubicle_name="distributed_gens")

def add_dsl_frame_for_dg_sm(
    pfbi: powfacpy.PFBaseInterface, 
    distributed_gen_grid, 
    original_sm, 
    dg_sm):
  original_sm_frame = original_sm.c_pmod
  dg_sm_frame = pfbi.copy_single_obj(original_sm_frame, 
    distributed_gen_grid,
    new_name="frame_distributed_gens_" + original_sm.loc_name)
  pelm = dg_sm_frame.pelm
  pelm[0] = dg_sm
  dg_sm_frame.pelm = pelm

def switch_between_distributed_generation_and_original_synchronous_machines(
    power_system_objs,
    is_distributed_generation):
  """
  Set synchronous machine into or out of service or activate/deactive
  the distributed generator grids, respectively.
  """
  if is_distributed_generation:
    outserve_sm = 1
  else:
    outserve_sm = 0
  for trafo in power_system_objs["original_sm_trafos"]:
      trafo.outserv = outserve_sm
  for sm in power_system_objs["original_synchronous_machines"]:
    sm.outserv = outserve_sm
    sm.c_pmod.outserv = outserve_sm
  for dg_grids in power_system_objs["distributed_gen_grids"]:
    if is_distributed_generation:
      dg_grids.Activate()
    else:
      dg_grids.Activate()
      dg_grids.Deactivate()
      
def set_distributed_generator_parameters(
    pfbi: powfacpy.PFBaseInterface,
    power_system_objs,
    converter_share,
    gform_converter_share,
    gf_converter_type):
  """
  Iterates through distributed generators and sets their parameters.
  converter_share is the share of all converters (i.e. grid-forming and grid-following)
  gform_vonverter_share is the share of grif-forming converters amongst all converters.
  """
  for original_sm,dg_gfoll_converter,dg_gfoll_trafo_type,dg_sm,dg_selfsync_converter,distributed_gen_grid,dg_pf_vsm_converter in zip(
    power_system_objs["original_synchronous_machines"],
    power_system_objs["distributed_gen_gfoll_converters"],
    power_system_objs["distributed_gen_gfoll_trafo_types"],
    power_system_objs["distributed_gen_synchronous_machines"],
    power_system_objs["distributed_gen_selfsync_converters"],
    power_system_objs["distributed_gen_grids"],
    power_system_objs["distributed_gen_pf_vsm_converters"],
    ):
    set_param_gfoll(
      pfbi,
      converter_share,
      gform_converter_share,
      dg_gfoll_converter,
      dg_gfoll_trafo_type,
      distributed_gen_grid,
      original_sm)
    set_param_selfsync(
      pfbi,
      converter_share,
      gform_converter_share,
      dg_selfsync_converter,
      distributed_gen_grid,
      original_sm,
      gf_converter_type)
    set_param_dg_sm(
      pfbi,
      converter_share,
      dg_sm,
      original_sm,
      distributed_gen_grid)
    set_param_pf_vsm(
      pfbi,
      converter_share,
      gform_converter_share,
      dg_pf_vsm_converter,
      distributed_gen_grid,
      original_sm,
      gf_converter_type)

def set_param_pf_vsm(
      pfbi,
      converter_share,
      gform_converter_share,
      dg_pf_vsm_converter,
      distributed_gen_grid,
      original_sm,
      gf_converter_type):
  if converter_share > 0 and gform_converter_share > 0 and gf_converter_type == "PowerFactory VSM":
    set_activity_pf_vsm_conv(
      pfbi,
      True,
      distributed_gen_grid,
      dg_pf_vsm_converter)
    dg_pf_vsm_converter.sgn = original_sm.typ_id.sgn * converter_share * gform_converter_share
    dg_pf_vsm_converter.uk = parameters.uk
    dg_pf_vsm_converter.Pcu = parameters.copper_losses_pu*dg_pf_vsm_converter.sgn*1000
    dg_pf_vsm_converter.pgini = original_sm.pgini*converter_share*(gform_converter_share)
    dg_pf_vsm_converter.qgini = original_sm.qgini*converter_share*(gform_converter_share)
    frame = dg_pf_vsm_converter.c_pmod
    pf_vsm_parameters = parameters.pf_vsm_parameters
    r_series_pu,x_series_pu = powfacpy.engineering_helpers.get_resistance_and_reactance_from_uk_and_copper_losses(
      dg_pf_vsm_converter.uk,
      dg_pf_vsm_converter.Pcu,
      dg_pf_vsm_converter.sgn,
      15)
    pf_vsm_parameters["Output Voltage Calculation"]["Rseries"] = r_series_pu
    pf_vsm_parameters["Output Voltage Calculation"]["Xseries"] = x_series_pu
    pf_vsm_parameters["Output Voltage Calculation"]["Mode"] = 1
    dsl_objects_paths = ["Virtual Synchronous Machine","Output Voltage Calculation",
    "Virtual Impedance","Proportional Voltage Controller"]
    for dsl_obj_path in dsl_objects_paths:
      powfacpy.set_attr_of_child(frame,dsl_obj_path,pf_vsm_parameters[dsl_obj_path])
  else:
    set_activity_pf_vsm_conv(
      pfbi,
      False,
      distributed_gen_grid,
      dg_pf_vsm_converter)

def set_activity_pf_vsm_conv(
    pfbi: powfacpy.PFBaseInterface,
    is_active,
    distributed_gen_grid,
    dg_pf_vsm_converter):
  if is_active:
    outserv_pf_vsm = 0
  else:
    outserv_pf_vsm = 1
  dg_pf_vsm_converter.outserv = outserv_pf_vsm
  frame = pfbi.get_single_obj(r"VSM Control System",
    parent_folder=distributed_gen_grid)
  frame.outserv = outserv_pf_vsm
  pf_vsm_impedance = pfbi.get_single_obj(
      "Impedance_pf_vsm.ElmZpu",parent_folder=distributed_gen_grid)
  pf_vsm_impedance.outserv = outserv_pf_vsm

def set_param_dg_sm(
      pfbi,
      converter_share,
      dg_sm,
      original_sm,
      distributed_gen_grid):
  if converter_share < 1:
    set_activity_dg_sm(
      pfbi,
      True,
      distributed_gen_grid,
      dg_sm)
    dg_sm.pgini = original_sm.pgini*(1-converter_share)
    dg_sm.qgini = original_sm.qgini*(1-converter_share)
    dg_sm.usetp = original_sm.usetp
    dg_sm.av_mode = original_sm.av_mode
    dg_sm.typ_id.sgn = original_sm.typ_id.sgn*(1-converter_share) 
    dg_sm.P_max = original_sm.P_max*(1-converter_share)
  else:   
    set_activity_dg_sm(
      pfbi,
      False,
      distributed_gen_grid,
      dg_sm)
    
def set_param_gfoll(
      pfbi,
      converter_share,
      gform_converter_share,
      dg_gfoll_converter,
      dg_gfoll_trafo_type,
      distributed_gen_grid,
      original_sm):
  if converter_share > 0 and gform_converter_share < 1:
    set_activity_of_gfoll_conv(pfbi,
      True,
      distributed_gen_grid,
      dg_gfoll_converter)
    dg_gfoll_converter.pgini = original_sm.pgini*converter_share*(1-gform_converter_share)*1000
    dg_gfoll_converter.qgini = original_sm.qgini*converter_share*(1-gform_converter_share)*1000
    dg_gfoll_converter.usetp = original_sm.usetp
    dg_gfoll_converter.av_mode = original_sm.av_mode
    dg_gfoll_converter.sgn = original_sm.typ_id.sgn*converter_share*(1-gform_converter_share)*1000
    dg_gfoll_converter.Pmax_uc = original_sm.P_max*converter_share*(1-gform_converter_share)*1000
    dg_gfoll_converter.P_max = original_sm.P_max*converter_share*(1-gform_converter_share)*1000
    dg_gfoll_converter.mode_inp = "PQ"
    dg_gfoll_converter.uk = 10
    dg_gfoll_converter.Pcu = 0.01*dg_gfoll_converter.sgn
    dg_gfoll_trafo_type.strn = original_sm.typ_id.sgn*converter_share*(1-gform_converter_share)
    gfoll_filter = pfbi.get_single_obj("Filter_GFoll",parent_folder=distributed_gen_grid)
    gfoll_filter.qtotn = 0.05*dg_gfoll_converter.sgn/1000
  else:  
    set_activity_of_gfoll_conv(pfbi,
      False,
      distributed_gen_grid,
      dg_gfoll_converter)

def set_param_selfsync(
      pfbi: powfacpy.PFBaseInterface,
      converter_share,
      gform_converter_share,
      dg_selfsync_converter,
      distributed_gen_grid,
      original_sm,
      gf_converter_type):
  if converter_share > 0 and gform_converter_share > 0 and gf_converter_type == "SelfSync":
    set_activity_selfsync_conv(
      pfbi,
      True,
      distributed_gen_grid,
      dg_selfsync_converter)
    dg_selfsync_converter.Snom = original_sm.typ_id.sgn * converter_share * gform_converter_share
    dg_selfsync_converter.uk = parameters.uk
    dg_selfsync_converter.Pcu = parameters.copper_losses_pu*dg_selfsync_converter.Snom*1000
    dg_selfsync_converter.psetp = original_sm.pgini*converter_share*(gform_converter_share)
    dg_selfsync_converter.qsetp = original_sm.qgini*converter_share*(gform_converter_share)
    frame = dg_selfsync_converter.c_pmod
    selfsync = pfbi.get_single_obj("SelfSync.ElmDsl",parent_folder=frame)
    selflim = pfbi.get_single_obj("SelfLim.ElmDsl",parent_folder=frame)
    pfdi = powfacpy.PFDynSimInterface(pfbi.app)
    pfdi.set_parameters_of_dsl_models_in_composite_model(
      frame, 
      parameters.self_sync_parameters,
      single_dict_for_all_dsl_models = True)
    r_series_pu,x_series_pu = powfacpy.engineering_helpers.get_resistance_and_reactance_from_uk_and_copper_losses(
      dg_selfsync_converter.uk,
      dg_selfsync_converter.Pcu,
      dg_selfsync_converter.Snom,
      dg_selfsync_converter.Unom)
    selflim.Ri = r_series_pu
    selflim.Xi = x_series_pu
    selflim.actOC = 1
    selfsync.Sb = dg_selfsync_converter.Snom*1e6
    selfsync.kp_strich = 2
  else:
    set_activity_selfsync_conv(
      pfbi,
      False,
      distributed_gen_grid,
      dg_selfsync_converter)

def set_activity_of_gfoll_conv(
    pfbi: powfacpy.PFBaseInterface,
    is_active,
    distributed_gen_grid,
    dg_gfoll_converter):
  if is_active:
    outserv_gfoll = 0
  else:
    outserv_gfoll = 1
  gfoll_trafo_elm =  pfbi.get_single_obj(
      "Trf PV Plant.ElmTr2",parent_folder=distributed_gen_grid)
  gfoll_trafo_elm.outserv = outserv_gfoll
  dg_gfoll_converter.outserv = outserv_gfoll
  frame = pfbi.get_single_obj(r"WECC Large-scale PV Plant EMT",
    parent_folder=distributed_gen_grid)
  frame.outserv = outserv_gfoll
  gfoll_impedance = pfbi.get_single_obj(         
      "Impedance_GFoll.ElmZpu",parent_folder=distributed_gen_grid)
  gfoll_impedance.outserv = outserv_gfoll

def set_activity_dg_sm(
    pfbi: powfacpy.PFBaseInterface,
    is_active,
    distributed_gen_grid,
    dg_sm):
  if is_active:
    outserv_dg_sm= 0
  else:
    outserv_dg_sm = 1
  dg_sm.outserv = outserv_dg_sm
  frame = pfbi.get_single_obj(r"frame_distributed_gens_g*",
    parent_folder=distributed_gen_grid)
  frame.outserv = outserv_dg_sm
  dg_sm_impedance = pfbi.get_single_obj(
      "Impedance_SM.ElmZpu",parent_folder=distributed_gen_grid)
  dg_sm_impedance.outserv = outserv_dg_sm

def get_main_terminals_of_substations_in_nordic_system(
    pfbi: powfacpy.PFBaseInterface):
  nordic_grid = pfbi.get_single_obj(r"Netzmodell\Netzdaten\Nordic")
  substations = pfbi.get_obj(".ElmSubstat",parent_folder=nordic_grid)
  main_terminals = []
  for substation in substations:
    main_terminals.append(pfbi.get_single_obj(
      substation.loc_name + ".ElmTerm",parent_folder=substation))
  return main_terminals

def set_activity_selfsync_conv(
    pfbi: powfacpy.PFBaseInterface,
    is_active,
    distributed_gen_grid,
    dg_selfsync_converter):
  if is_active:
    outserv_selfsync = 0
  else:
    outserv_selfsync = 1
  dg_selfsync_converter.outserv = outserv_selfsync
  frame = pfbi.get_single_obj(r"SelfSync",
    parent_folder=distributed_gen_grid)
  frame.outserv = outserv_selfsync
  selfsync_dc_source = pfbi.get_single_obj(
      "DC Source SelfSync.ElmDcu",parent_folder=distributed_gen_grid)
  selfsync_dc_source.outserv = outserv_selfsync
  selfsync_impedance = pfbi.get_single_obj(
      "Impedance_selfsync.ElmZpu",parent_folder=distributed_gen_grid)
  selfsync_impedance.outserv = outserv_selfsync

def check_if_with_and_without_dg_gives_same_load_flow_result(
    pfbi: powfacpy.PFBaseInterface,
    power_system_objs,
    max_allowed_voltage_deviation_pu=0.01):
  """
  Checks if the load flow results are the same if the distributed 
  generators are added compared to the original system with synchronous 
  machines. This verifies the settings of the distributed gen. and
  the station load flow controllers.
  """
  main_terminals = get_main_terminals_of_substations_in_nordic_system(pfbi)
  voltages_of_terminals_no_dg = []
  switch_between_distributed_generation_and_original_synchronous_machines(
    power_system_objs,False)
  pfbi.app.GetFromStudyCase("ComLdf").Execute()
  for terminal in main_terminals:
    voltages_of_terminals_no_dg.append(terminal.GetAttribute("m:u"))
  voltages_of_terminals_with_dg = []
  switch_between_distributed_generation_and_original_synchronous_machines(
    power_system_objs,True)
  pfbi.app.GetFromStudyCase("ComLdf").Execute()
  for terminal in main_terminals:
    voltages_of_terminals_with_dg.append(terminal.GetAttribute("m:u"))
  max_voltage_deviation_exceeded = False
  for term_num,_ in enumerate(voltages_of_terminals_no_dg):
    voltage_deviation = voltages_of_terminals_no_dg[term_num] - voltages_of_terminals_with_dg[term_num]
    if voltage_deviation > max_allowed_voltage_deviation_pu:
      print("Max. voltage deviation is exceeded at terminal " +
            main_terminals[term_num].loc_name +
            ": " + str(voltage_deviation))
      max_voltage_deviation_exceeded = True
  if not max_voltage_deviation_exceeded:
    print("Voltage deviations are within limit of " + 
          str(max_allowed_voltage_deviation_pu) + "pu.")    

