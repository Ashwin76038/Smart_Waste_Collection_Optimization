# Business charter

## Scope
Municipal non-hazardous solid waste in Tamil Nadu; proposed Chennai pilot for secondary collection from community bins to eligible receiving facilities. Keep door-to-door vehicles, community-bin compactors, street litter and long-haul disposal as distinct operating processes. Do not route infectious hospital waste or industrial hazardous waste as ordinary municipal refuse. Schools/hospitals/industrial land-use are possible demand-context proxies only.

## Stakeholders and decisions
- Municipal operations lead: collection priorities, service coverage, shifts and exceptions.
- Dispatcher: feasible bin assignments, truck capacity, access and receiving windows.
- Finance analyst: marginal operating costs, fixed costs and scenario break-even.
- Planning team: evidence for coverage gaps and future bin or vehicle allocation.
- Portfolio reviewer: source traceability, reproducible decisions and honest limitations.

## Success contract (proposed; no measured targets yet)
Compare operating kilometres, fuel, labour and costs only among scenarios meeting the same service requirements. Minimize avoidable work subject to overflow risk, maximum time since collection, vehicle/road access, capacity, receiving-facility hours and shift limits. Show infeasible or unserved demand, never hide it as a saving.

Performance targets must be frozen after baseline profiling. Candidate decisions such as a fill threshold or maximum service gap are assumptions, not official Chennai policy. Operational deployment requires actual operator review beyond this portfolio.

## KPI definitions to implement later
| Metric | Definition and unit | Guardrail |
|---|---|---|
| Vehicle distance | Sum of all directed route legs, km, including depot and disposal legs | Include deadhead trips |
| Overflow exposure | Bin-hours above physical capacity / eligible observed or simulated bin-hours | Report missing observation exposure separately |
| Unserved demand | Due bins missed and uncollected kg at horizon end | No silent dropping |
| Collection utilization | Pre-service occupied volume / bin capacity, % | Bin volume is not truck payload |
| Fleet utilization | Served payload / rated usable vehicle payload, % by trip | Both kg and m3 constraints |
| Fuel intensity | Total litres / collected metric tonnes | Null when collected mass is zero |
| Labour | Sum of crew members times paid shift/service hours, person-hours | Include paid idle time separately |
| Operating cost | Fuel + labour + variable maintenance + disposal, INR | Separate fixed assets and existing budget |
| Scenario saving | Baseline cost minus candidate cost, INR; divided by baseline for % | Matched scope; undefined for zero baseline |
| Collection per resident | Matching collected kg / population / covered days | Label collected, not generated; geography/vintage must match |
| Forecast error | MAE in target units; WAPE as sum abs errors / sum actuals | No MAPE on zero-heavy targets |

Bin and vehicle allocation studies are extensions after service feasibility. Area-level demand correlations do not establish causal benefits from moving bins.
