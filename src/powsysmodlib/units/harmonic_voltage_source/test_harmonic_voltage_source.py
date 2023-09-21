import pytest
import sys
import json
sys.path.append(r'.\.\src')
settings_file = open(r'.\.\settings.json')
settings = json.load(settings_file)
sys.path.insert(0,settings["local path to powfacpy (optional)"])
import powfacpy
import harmonic_voltage_source as harmonic_vs
sys.path.append(r".\.\tests")
from pytest_fixtures_powfacpy import pfdi, pfpi, pf_app

@pytest.fixture(scope="module")
def harmonic_source(pfdi,activate_test_project):
  # Return harmonic voltage source object
  elmvac = pfdi.get_single_obj(r"Network Model\Network Data\units" +
    r"\harmonic_voltage_source\harmonic_voltage_source\harmonic_voltage_source")
  harmonic_source = harmonic_vs.HarmonicVoltageSource(elmvac,pfdi)
  return harmonic_source

@pytest.fixture(scope="module")
def activate_test_project(pfdi):
  """
  Creates a copy of the test project which is then 
  used for the tests. This ensures that the tests are always run 
  with the same initial project state.
  The test project must be located in PowerFactory in the current user under 
  powsysmodlib\\units\\harmonic_voltage_source\\harmonic_voltage_source_tests
  """
  user = pfdi.app.GetCurrentUser()
  folder_of_project_for_testing = pfdi.get_single_obj(r"powsysmodlib\units\harmonic_voltage_source",
      parent_folder = user) 
  project_for_testing = pfdi.get_single_obj(r"harmonic_voltage_source_tests",
      parent_folder = folder_of_project_for_testing)
  project_copy = pfdi.copy_single_obj(project_for_testing,
      folder_of_project_for_testing, 
      new_name="copy_where_tests_are_run")   
  print(project_copy) 
  project_copy.Activate() 

def test_set_nominal_voltage(
    harmonic_source: harmonic_vs.HarmonicVoltageSource,
    activate_test_project):
  dsl_obj_per_unit_to_nominal = harmonic_source.pfdi.get_single_obj(
      "per_unit_to_nominal",parent_folder=harmonic_source.comp_frame)   
  voltages_kV = (110,400)
  for voltage in voltages_kV:
    harmonic_source.set_nominal_voltage(voltage)
    assert harmonic_source.elmvac.Unom == voltage
    assert dsl_obj_per_unit_to_nominal.nominal_value == voltage

def test_reset_symmetric_and_only_fundamental_frequency(
    harmonic_source: harmonic_vs.HarmonicVoltageSource,
    activate_test_project):
  harmonic_source.pfdi.activate_study_case(
    r"Study Cases\units\harmonic_voltage_source\symmetric_fundamental_frequency")
  harmonic_source.reset_symmetric_and_only_fundamental_frequency()

def test_set_symmetric_with_harmonics(
    harmonic_source: harmonic_vs.HarmonicVoltageSource,
    activate_test_project): 
  harmonic_source.pfdi.activate_study_case(
    r"Study Cases\units\harmonic_voltage_source\symmetric_third_harmonic")  
  params = {
    "f1": [[0,50]],
    "f2": [[0,150]],    
    "mag1": [[0,1]],
    "mag2": [[0.05,0],[0.0501,0.3]],   
    "phi1": [[0,0]],
    "phi2": [[0,180]],        
    }
  harmonic_source.set_symmetric(
    params,
    same_angular_shift_for_harmonics_of_all_phases = True)

if __name__ == "__main__":
  # pytest.main(([r"tests\test_base_interface.py"]))
  pytest.main(([r"src\powsysmodlib"]))
