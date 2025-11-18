# RTC-Tools

RTC-Tools is an open-source platform for the operational optimization of portfolios of assets, in particular storage assets such as hydropower reservoirs and battery energy storage systems (BESS). RTC-Tools is part of [LF Energy](https://lfenergy.org/).

In water management, RTC-Tools is used for model-predictive control of water systems including turbines, pumps, weirs, and reservoirs.

In power trading, the RTC-Tools project aims to move the field of trading optimization towards increased transparency, increased code-reuse, and higher trading value capture.

The RTC-Tools project was originally initiated at [Deltares](https://www.deltares.nl/) and is deployed for water and power trading applications across the globe, across North and South America, Europe, Asia, and Australia.

RTC-Tools offers the following functionality:

- **Systems modelling using extensible libraries**: Build complex system models using extensible libraries of model components. Implement
custom model components, linear or nonlinear, using the [Modelica](https://modelica.org/language/) systems modelling language or directly using the Python
API.

    The following modelling extensions are available (this list is non-exhaustive):
    - [rtc-tools-channel-flow](https://gitlab.com/deltares/rtc-tools-channel-flow): water system models
    - [rtc-tools-hydraulic-structures](https://gitlab.com/deltares/rtc-tools-hydraulic-structures): hydraulic assets, such as weirs and pumps
    - [rtc-tools-heat-network](https://github.com/Nieuwe-Warmte-Nu/rtc-tools-heat-network): heat networks
    - [BESS trading examples](https://portfolioenergy-bess-demo.readthedocs.io/en/latest/): basic Battery Energy Storage Systems (BESS) trading examples for NEM (Australia), ERCOT (Texas) and EU-style markets
            
- **Running simulations**: Simulate a given model.

- **Specifying and solving optimization problems**: Define optimization goals, constraints and decision variables to specify optimization 
problems for a given model. RTC-Tools supports both open-source (CBC, HiGHS, Ipopt) and commercial solvers (Gurobi, CPLEX, Knitro) for solving several types of optimization problems:

    - **Linear, non-linear**:  RTC-Tools supports both linear and non-linear optimization problems.

    - **Continuous and discrete**:  RTC-Tools can handle both continuous and discrete decision variables. This makes it suitable for optimizing systems with a mix of continuous controls (such as pump speeds or gate positions) and discrete decisions (such as on/off states of equipment).

    - **Lexicographic goal programming**: When multiple, and perhaps conflicting, objectives are to be considered (e.g., minimize operational costs while minimizing deviations of water levels from a given range), RTC-Tools offers two approaches to multi-objective optimization: The weighting method, which assigns weights to each objective and optimizes them simultaneously, and the lexicographic goal programming method, which optimizes different objectives sequentially according to a user-defined priority ordering. 

    - **Optimization under uncertainty**: RTC-Tools offers a multi-stage stochastic optimization approach that leverages ensemble inputs 
    to compute solutions that are robust under uncertainty.

To streamline the integration with user interfaces and data management systems (such as Delft-FEWS), RTC-Tools supports CSV and XML file formats for reading/writing timeseries and other model parameters. Support for other formats can be implemented using Python mixins.

RTC-Tools uses [CasADi](https://web.casadi.org/) as a symbolic framework for algorithmic differentiation, as well as for interfacing with numerical optimization solvers.


## Install

```bash
pip install rtc-tools
```

## Documentation

Documentation and examples can be found on [readthedocs](https://rtc-tools.readthedocs.io).


## License

RTC-Tools is licensed under the **[GNU Lesser General Public License v3.0](COPYING)**,
and can be used free of charge. 


## Support

For applications in water management, [Deltares](https://www.deltares.nl/) offers commercial support.

For applications in power trading, [PortfolioEnergy](https://www.portfolioenergy.com/) offers commercial support.


## Acknowledgment

If you use RTC-Tools in your work, please acknowledge it in any resulting publications.
You can do this by citing RTC-Tools and providing a link to our
[GitHub repository](https://github.com/rtc-tools/rtc-tools).
