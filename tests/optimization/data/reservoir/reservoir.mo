model Reservoir
    // Basic model for in/outlow of a reservoir
    parameter Real theta;
    input Real q_in(fixed=true);
    input Real q_out(fixed=false, min=0.0, max=5.0);
    output Real volume;
equation
    der(volume) = q_in - (2 - theta) * q_out;
end Reservoir;
