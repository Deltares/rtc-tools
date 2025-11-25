model Model
	Real x(start=1.1, nominal = 10);
	Real w(start=0.0);
	Real alias;

	Real v_initial(start=2.1, fixed=true);

	parameter Real k = 1.0;

	input Real u(fixed=false);

	output Real y;

	output Real z;

	output Real x_delayed;
	Real x_delayed_extra;

	output Real switched;

	input Real constant_input(fixed=true);
	output Real constant_output;

equation
	der(x) = k * x + u;
	der(w) = x;
	der(v_initial) = 0;

	alias = x;

	y + x = 3.0;

	z = alias^2 + sin(time);

	x_delayed = delay(x, 0.1);
	x_delayed_extra = delay(x, 0.125);

	if x > 0.5 then
		switched = 1.0;
	else
		switched = 2.0;
	end if;

	constant_output = constant_input;

end Model;