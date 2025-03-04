//! base 0.1.0
package 'Example'
  model 'Example'
    Real 'inflow.QOut.Q'(nominal = 'inflow.Q_nominal', unit = "m3/s", quantity = "VolumeFlowRate") "Volume flow";
    Real 'inflow.Q'(nominal = 'inflow.Q_nominal', unit = "m3/s", quantity = "VolumeFlowRate");
    parameter Real 'inflow.Q_nominal'(unit = "m3/s", quantity = "VolumeFlowRate") = 1.0;
    Real 'storage.QIn.Q'(nominal = 'storage.Q_nominal', unit = "m3/s", quantity = "VolumeFlowRate") "Volume flow";
    Real 'storage.QOut.Q'(nominal = 'storage.Q_nominal', unit = "m3/s", quantity = "VolumeFlowRate") "Volume flow";
    parameter Integer 'storage.n_QForcing'(min = 0) = 0;
    Real[0] 'storage.QForcing'(each nominal = 'storage.Q_nominal', unit = fill("", 0), quantity = fill("", 0));
    Real 'storage.Q_release'(nominal = 'storage.Q_nominal', unit = "m3/s", quantity = "VolumeFlowRate");
    Real 'storage.V'(nominal = 4e5, max = 6e5, min = 2e5, unit = "m3", quantity = "Volume");
    parameter Real 'storage.Q_nominal'(unit = "m3/s", quantity = "VolumeFlowRate") = 1.0;
    Real 'outfall.QIn.Q'(nominal = 'outfall.Q_nominal', unit = "m3/s", quantity = "VolumeFlowRate") "Volume flow";
    Real 'outfall.Q'(nominal = 'outfall.Q_nominal', unit = "m3/s", quantity = "VolumeFlowRate");
    parameter Real 'outfall.Q_nominal'(unit = "m3/s", quantity = "VolumeFlowRate") = 1.0;
    input Real 'Q_in'(fixed = true, unit = "m3/s", quantity = "VolumeFlowRate");
    input Real 'Q_release'(fixed = false, max = 6.5, min = 0.0, unit = "m3/s", quantity = "VolumeFlowRate");
    output Real 'V_storage'(unit = "m3", quantity = "Volume");
  equation
    'inflow.QOut.Q' = 'storage.QIn.Q';
    'storage.QOut.Q' = 'outfall.QIn.Q';
    'inflow.QOut.Q' / 'inflow.Q_nominal' = 'inflow.Q' / 'inflow.Q_nominal';
    der('storage.V') / 'storage.Q_nominal' = ('storage.QIn.Q' - 'storage.QOut.Q') / 'storage.Q_nominal';
    'storage.QOut.Q' / 'storage.Q_nominal' = 'storage.Q_release' / 'storage.Q_nominal';
    'outfall.Q' / 'outfall.Q_nominal' = 'outfall.QIn.Q' / 'outfall.Q_nominal';
    'storage.Q_release' = 'Q_release';
    'inflow.Q' = 'Q_in';
    'V_storage' = 'storage.V';
  end 'Example';
end 'Example';
