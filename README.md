# RTC-Tools

## Project Overview

RTC-Tools is an open-source Python framework designed to model, simulate, and optimize time-dependent systems with interconnected components. It is part of [LF Energy](https://lfenergy.org/).

## Project Description

RTC-Tools provides a modular and extensible platform for operational optimization and control of complex systems across multiple domains, with a primary focus on water management and energy systems. Originally initiated at [Deltares](https://www.deltares.nl/) in 2015, RTC-Tools is deployed for water and power trading applications across the globe, across North and South America, Europe, Asia, and Australia.

### Application Domains

- **Water Management**: Model-predictive control of canals, polders, reservoirs, hydropower scheduling, and pumped storage systems, including turbines, pumps, weirs, and other hydraulic structures.
- **Energy Systems**: Battery energy storage system (BESS) optimization, power trading, and multi-energy system planning.

### Multi-Domain Modeling Libraries

RTC-Tools offers extensible libraries for building complex system models using model components. Implement custom model components, linear or nonlinear, using the [Modelica](https://modelica.org/language/) systems modeling language or directly using the Python API.

The following modeling libraries are available (this list is non-exhaustive):

- [RTC-Tools Channel Flow](https://github.com/Deltares/rtc-tools-channel-flow): Hydraulic channel flow and water level dynamics
- [RTC-Tools Hydraulic Structures](https://rtc-tools-hydraulic-structures.readthedocs.io/en/latest/): Hydraulic assets such as weirs, pumps, and other control structures
- [RTC-Tools Simulation](https://rtc-tools-simulation.readthedocs.io/en/latest/): Reservoir and system simulation workflows
- [Mesido](https://github.com/Multi-Energy-Systems-Optimization/mesido/pulls): Heat network design and multi-energy system optimization
- [BESS Trading Examples](https://portfolioenergy-bess-demo.readthedocs.io/en/latest/): Battery energy storage trading formulations for NEM (Australia), ERCOT (Texas), and EU-style markets

### Core Capabilities

- **Simulation**: Simulate a given model to analyze system behavior over time.

- **Optimization**: Define optimization goals, constraints, and decision variables to specify optimization problems for a given model. RTC-Tools is solver-agnostic and supports both open-source solvers (CBC, HiGHS, Ipopt) and commercial solvers (Gurobi, CPLEX, Knitro) for solving several types of optimization problems:

    - **Linear and non-linear**: RTC-Tools supports both linear and non-linear optimization problems.

    - **Continuous and discrete**: RTC-Tools can handle both continuous and discrete decision variables. This makes it suitable for optimizing systems with a mix of continuous controls (such as pump speeds or gate positions) and discrete decisions (such as on/off states of equipment).

- **Multi-Objective Optimization**: When multiple, and perhaps conflicting, objectives need to be considered (e.g., minimize operational costs while minimizing deviations of water levels from a given range), RTC-Tools offers two approaches:
    - **Weighting method**: Assigns weights to each objective and optimizes them simultaneously.
    - **Lexicographic goal programming**: Optimizes different objectives sequentially according to a user-defined priority ordering.

- **Optimization Under Uncertainty**: RTC-Tools supports multi-stage stochastic optimization that leverages ensemble forecasts to compute solutions that are robust under uncertainty. Features include control tree generation and scenario tree reduction and aggregation. Optional risk constraints such as Conditional Value at Risk (CVaR) can be implemented depending on the user's specific formulation.

### Integration

To streamline integration with user interfaces and data management systems (such as Delft-FEWS), RTC-Tools supports CSV and XML file formats for reading/writing timeseries and other model parameters. Support for other formats can be implemented using Python mixins.

RTC-Tools uses [CasADi](https://web.casadi.org/) as a symbolic framework for algorithmic differentiation, as well as for interfacing with numerical optimization solvers.


## Install

```bash
pip install rtc-tools
```

## Documentation

Documentation and examples are available at:
- [Stable documentation](https://rtc-tools.readthedocs.io/en/stable/)
- [Latest documentation](https://rtc-tools.readthedocs.io/en/latest/)


## License

RTC-Tools is licensed under the **[GNU Lesser General Public License v3.0](COPYING)**,
and can be used free of charge. 


## Support

### Community Support

For questions, issues, and discussions, please use:
- [GitHub Issues](https://github.com/rtc-tools/rtc-tools/issues) for bug reports and feature requests
- [GitHub Discussions](https://github.com/rtc-tools/rtc-tools/discussions) for questions and community discussions

### Commercial Support

For applications in water management, [Deltares](https://www.deltares.nl/) offers commercial support.

For applications in power trading and battery energy storage systems (BESS), [PortfolioEnergy](https://www.portfolioenergy.com/) offers commercial support.


## Governance & Roadmap

RTC-Tools development follows an open governance model. To learn more about the project roadmap and contribute to future development:

- Review the [roadmap discussion](https://github.com/rtc-tools/rtc-tools/discussions/1725)
- Check [project milestones](https://github.com/rtc-tools/rtc-tools/milestones)
- Watch the [feature overview video](https://www.youtube.com/watch?v=GAuQ5ft8vr4)
- See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines


## Ecosystem & Collaboration

RTC-Tools is part of the LF Energy ecosystem and welcomes collaboration from researchers, practitioners, and organizations working on optimization and control of water and energy systems. We encourage the development of extensions, modeling libraries, and integrations that expand the capabilities and reach of the framework.


## Acknowledgment

If you use RTC-Tools in your work, please acknowledge it in any resulting publications. You can do this by citing the RTC-Tools software and providing a link to our [GitHub repository](https://github.com/rtc-tools/rtc-tools).
