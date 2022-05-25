# Set of Script to Iterate through Magnet Settings for PIONEER 22 Beamtime

## J. LaBounty

Scripts will require python 3

We want to be able to scan:

* Single magnets through a range of parameter space (either in absolute terms, or in relative terms)
* Quad triplets through a range of parameter space together
* A multi-dimensional parameter space with many magnets

The scripts should also take into account the hysteresis of the magnets (i.e. always go in the same direction while taking the scan)