import powfacpy
import copy

class HarmonicVoltageSource():
  """
  An interface to the dynamic model of a harmonic voltage source in 
  PowerFactory and provides helper methods to set parameters.
  The dynamic model consists of a voltage source (ElmVac) and its DSL 
  controller model. Up to three sine waves (harmonics) can be superimposed. 
  Each harmonic has a frequency, magnitude and phase. In addition, the
  DC offset can be set
  For example, the following parameter setting refer to the first sine wave
  and are time value pairs which are interpolated: 
  params = {
      "f1": [[0,50],[1,51]], # frequency starts at 50Hz at t = 0s and rises to 51Hz in one second   
      "mag1": [[0,1],[2,1],[2.0001,0.95]], # Magnitude starts at 1pu and jumps to 0.95 within 0.1ms at t=2s
      "phi1": [[0,0]], # Angle (additional to angular chang edue to frequency) is zero        
    }  
  """
    
  def __init__(self, 
               elmvac, 
               app_or_dyn_sim_interface, 
               composite_frame=None):
    """Initialization.
    Arguments:
      - elmvac: Voltage source object (ElmVac)
      - app_or_dyn_sim_interface: PowerFactory application or dynamic 
      simulaition interface of powfacpy (PFDynSimInterface). If the 
      PowerFactory application is provided, an instance of the 
      PFDynSimInterface is created. 
      - composite_frame: Composite frame of voltage source with the
      DSL model of the harmonic source. If not provided, the frame is
      fetched from the attribute c_pmod of the voltage source object   
    """
    if isinstance(app_or_dyn_sim_interface,powfacpy.PFDynSimInterface):
      self.pfdi: powfacpy.PFDynSimInterface = app_or_dyn_sim_interface
    else:
      self.pfdi: powfacpy.PFDynSimInterface = powfacpy.PFDynSimInterface(
        app_or_dyn_sim_interface)
    self.elmvac = self.pfdi.handle_single_pf_object_or_path_input(elmvac)
    if composite_frame:
      self.comp_frame = composite_frame
    else:
      self.comp_frame = self.elmvac.c_pmod
    self.set_nominal_voltage_of_dsl_model(self.elmvac.Unom)

  def set_phase(self,phase: str, params: dict):
    """Set dsl array parameters of one phase.
    Arguments:
    - phase: "a","b","c"
    - params: parameters and values of the dsl array.
      To map the parameters to the array columns get_array_number is used.

    Example:
      params =   
    """
    phase_dsl = self.get_dsl_model_of_phase(self,phase)
    for param,value in params.items():
      array_num = self.get_array_number(param)
      self.pfdi.set_dsl_obj_array(phase_dsl,value,array_num=array_num,
        size_included_in_array=False)

  def set_symmetric(
      self,
      params: dict,
      same_angular_shift_for_harmonics_of_all_phases = False):
    """
    Set parameters for all phases symmetrically.
    """
    for phase in ("a","b","c"):
      dsl_model_of_phase = self.get_dsl_model_of_phase(phase)
      for param,time_value_pairs in params.items():
        time_value_pairs_copy = copy.deepcopy(time_value_pairs)
        if "phi" in param:
          if same_angular_shift_for_harmonics_of_all_phases and not param == "phi1":
            additional_angle = 0 
          else:  
            if phase == "a":
              additional_angle = 0
            elif phase == "b":
              additional_angle = -120  
            else:
              additional_angle = 120  
          for idx,angle_at_time in enumerate(time_value_pairs):
            time_value_pairs_copy[idx][1] = angle_at_time[1] + additional_angle
        self.pfdi.set_dsl_obj_array(dsl_model_of_phase,
          time_value_pairs_copy,
          array_num=self.get_array_number(param),
          size_included_in_array=False)

  def reset_symmetric_and_only_fundamental_frequency(
      self,
      fundamental_frequency=50,
      magnitude=1,
      angle=0):
    """
    Set symmetric and only fundamental frequency.
    """
    params = {
      "f1": [[0,fundamental_frequency]],    
      "mag1": [[0,magnitude]],
      "mag2": [[0,0]],   
      "mag3": [[0,0]],
      "offset": [[0,0]], 
      "phi1": [[0,angle]],        
    }
    self.set_symmetric(params)

  def set_nominal_voltage(self,voltage_kV):
    self.set_nominal_voltage_of_dsl_model(voltage_kV)
    self.set_nominal_voltage_of_elmvac(voltage_kV)

  def set_nominal_voltage_of_dsl_model(self,voltage_kV):
    self.pfdi.get_single_obj(
      "per_unit_to_nominal",parent_folder=self.comp_frame).SetAttribute(
        "nominal_value",voltage_kV)

  def set_nominal_voltage_of_elmvac(self,voltage_kV):
    self.elmvac.Unom = voltage_kV

  def get_dsl_models_of_all_phases(self):
    return self.pfdi.get_obj("phase*.ElmDsl", parent_folder=self.comp_frame)
  
  def get_dsl_model_of_phase(self,phase: str):
    return self.pfdi.get_single_obj("phase_" + phase, 
      parent_folder=self.comp_frame)

  @staticmethod  
  def get_array_number(variable):
    """Mapping of the parameters to the DSL array column.
    """
    return (
      "f1",       # 1
      "f2",       # 2
      "f3",       # 3
      "mag1",     # 4
      "mag2",     # 5
      "mag3",     # 6
      "offset",   # 7
      "phi1",     # 8
      "phi2",     # 9
      "phi3"      # 10
      ).index(variable) + 1
