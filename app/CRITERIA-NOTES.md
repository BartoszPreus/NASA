# Comparison criteria

`criteria.json` describes the comparison shown in the atlas. The five entries marked as in the terrain score cover eight numerical features because related baselines are grouped for readers. The implementation uses the features named by `pipeline/features.py` and the ranking rule described in [the method](../docs/METHOD.md). The mask and the dune-like rule have separate effects on selection and ranking.

Context comes from the [source registry](../data/sources.csv). The dune-like relief rule was checked against surface temperature and moisture in [J26](../docs/sources/j26.md). The effects of the mask, controls, known analog tiles and elevation models are documented in [validation](../docs/VALIDATION.md).

The criteria list was reconstructed from the tracked project documentation and code for J7. It describes which parts of a field experiment or mission design the available data can support.
