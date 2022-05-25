# Set of Script to Iterate through Magnet Settings for PIONEER 22 Beamtime

## J. LaBounty

Scripts will require python 3

We want to be able to scan:

* Single magnets through a range of parameter space (either in absolute terms, or in relative terms)
* Quad triplets through a range of parameter space together
* A multi-dimensional parameter space with many magnets

The scripts should also take into account the hysteresis of the magnets (i.e. always go in the same direction while taking the scan)

Example triplet scan
```
{
    "scans":{
        "triplet_example":{
            "scan_type":"TRIPLET",
            "magnet_name": ["QSK41","QSK42","QSK43"],
            "nominal_sets": [18.20, -40.7, 34.8],
            "approach_from": ["ABOVE", "BELOW", "ABOVE"],
            "point_type": ["REL", "REL", "REL"],
            "scan_points": [[5,0.9,1.1],[5,0.9,1.1],[5,0.9,1.1]]
        }
    }
}
```

Example singlet scan

```
{
    "scans":{
        "qsk_init":{
            "scan_type":"SINGLET",
            "magnet_name": ["QSK42"],
            "nominal_sets": [-40.7],
            "approach_from": ["BELOW"],
            "point_type": ["REL"],
            "scan_points": [[5,0.9,1.1]]
        }
    }
}
```
