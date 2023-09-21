import pytest
import sys
import json
settings_file = open('.\\settings.json')
settings = json.load(settings_file)
sys.path.append(settings["local path to PowerFactory application"])
import powerfactory
sys.path.insert(0,settings["local path to powfacpy (optional)"])
import powfacpy 

@pytest.fixture(scope='session')
def pf_app():
  return powerfactory.GetApplication()

@pytest.fixture(scope="session")
def pfdi(pf_app):
  # Return PFDynSim instance
  return powfacpy.PFDynSimInterface(pf_app)   

@pytest.fixture(scope="session")
def pfpi(pf_app):
  # Return PFPlotInterface instance
  return powfacpy.PFPlotInterface(pf_app)

