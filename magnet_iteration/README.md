# Set of Script to Iterate through Magnet Settings for PIONEER 22 Beamtime

## J. LaBounty

Scripts will require python 3 (I wrote on python 3.10)

We want to be able to scan:

* Single magnets through a range of parameter space (either in absolute terms, or in relative terms)
* Quad triplets through a range of parameter space together
* A multi-dimensional parameter space with many magnets (Not yet implemented)

The scripts should also take into account the hysteresis of the magnets (i.e. always go in the same direction while taking the scan, and go past that value). In general, all piE5 magnets should always be ramped towards zero (i.e. -100 -> -90 -> -60 ... or 100 -> 90 ...).

The code can be run by doing:

```bash
python3 make_scan.py input.json output.json
```

If you do not have an environment to run the code, you can create one in anaconda via:

```bash
conda env create -n magnets python=3.10 numpy matplotlib pandas
```

---

The script will write a file (`output.json`) which is compatable with the WaveDAQ using the scans defined in `input.json`. If you have an invalid input format, or there is some warning (you may be too close to the magnet current limit) The input file format is as follows:

For scanning through single magnet, you can have a file as follows:

```json
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

The `SINGLET` scan type is a "one magnet" scan. In this case `QSK42` is scanned in `REL` mode (i.e. relative to the nominal setpoint in `nominal_sets`) from `0.9*nominal_set` -> `1.1*nominal_set` in 5 steps. At the end of the scan, it will return the magnet to the nominal setpoint. You can also spefify a scan in absolute values:

```json
...
    "point_type":["ABS"],
    "scan_points":[[5,-20,-60]]
...
```

## **IMPORTANT: Always check the output files such that the magnets do not exceed their relative amplitudes! There should be no |values| > 100 unless you know what you're doing!!**

---

A triplet scan scans the 1st and 3rd triplet values relative to the second, and plots out a grid

```json
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

This specifies the three magnets which will be changed (`"QSK41","QSK42","QSK43"`) and the settings they will have. If the first and third set do not match, an error will be thrown.

---

The output file format should be like:

```json
{
    "set_points":[
        {
            // settings 1
        },
        {
            // settings 2
        },
        ...
    ]
}
```

where each of the settings `dict`s are something like

```json
{
    "QSK41":-17.0,
    "settling_time_s":10
}
```

This will set `QSK41` to `-17.0` and wait 10 secondsg before doing a SiMon scan.


---

Once you have the output file, you can copy it to the `pioneer-daq` machine in the folder: `/home/pioneer/simon/config/epics/`. From there, it can be read by the WaveDAQ system.


