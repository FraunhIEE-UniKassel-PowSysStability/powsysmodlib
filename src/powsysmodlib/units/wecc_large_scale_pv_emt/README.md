# Description

- Type of simulation: EMT
- Software: PowerFactory (DSL)
  
This model is based on the 'WECC Large-scale PV Plant 110MVA 50Hz' model template from the PowerFactory library (path in PF library: *DIgSILENT Library\Templates\Photovoltaic\WECC Large-scale PV Plant 110MVA 50Hz*). The template is adapted for EMT simulations by adding some minor alterations. The main adjustment is that a PLL is added. The PLL replaces the "Voltage Source Ref" slot. The built-in implementation of the  current controller of the static/PV generator is used. Furthermore, the voltage magnitude calculation is added.

The model template is found in the project 'wecc_converted_to_emt.pfd' in the templates library (*Library\Templates\WECC Large Scale PV EMT*).

Developed for the publication (**please cite**)

*Open-Source EMT Model of Grid-Forming Converter with Industrial Grade SelfSync and SelfLim Control* by Simon Eberlein, Peter Unruh and Tobias Erckrath, IEEE ISGT 2023, Grenoble.

See also *github.com/FraunhIEE-UniKassel-PowSysStability/paper_isgt_2023_selfsync*.