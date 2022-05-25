'''
    Script to iterate through magnet settings and make a scan
    Expects a json input format like
    {
        "scans":[
            "scan_name":{
                "scan_type"    : What type of scan this object is describing
                    Options-> SINGLET, TRIPLET, PARAM_SPACE
                "magnet_name"  : List of the magnet names to alter, as given in magnets.json
                    EX) ["AST41", "QSF45"]
                "nominal_sets" : Nominal setpoint to return to after the scan
                    EX) [-97.40, 86.00]
                "approach_from": List of which direction to approach settings from -> ABOVE, BELOW
                    EX) ["BELOW", "ABOVE"]
                "point_type"   : Whether the points in the "scan_points" list are given in relative or absolute terms
                    Options) REL, ABS
                    EX) ["REL", "ABS"]
                "scan_points"  : List of scan points for each magnet in the above lists, in the format (npts, lower, upper)
                    EX) [(40, -10, 10), (20, 82, 93)]
            },
        ...
        ]
    }
'''

from ast import parse
from dataclasses import dataclass
import json
from jsonschema import ValidationError
import pandas 
import numpy as np 
import sys
import os 

@dataclass
class MagnetScan:
    # name         : str
    scan_type     : str
    magnet_name   : tuple
    nominal_sets  : tuple
    approach_from : tuple
    point_type    : tuple
    scan_points   : tuple
    settling_time : int = 2
    triplet_type  : int = 1

    def __post_init__(self):
        assert len(self.magnet_name) == len(self.nominal_sets) == len(self.approach_from) == len(self.point_type) == len(self.scan_points)
        if(self.scan_type == 1 or self.scan_type == 3):
            assert len(self.magnet_name) == self.scan_type

def load_magnet_names(infile):
    with open(infile, 'r') as fin:
        ding = json.load(fin)
    magnet_names = []
    for x in ding['magnets']:
        if(x['writable']):
            magnet_names.append(x['name'])

    return magnet_names

VALID_SCAN_TYPE = {'SINGLET':1, 'TRIPLET':3, 'PARAM_SPACE':0}
VALID_MAGNET_NAME = load_magnet_names('config/magnets.json')
VALID_APPROACH_FROM = {'BELOW':-1, 'ABOVE':1}
VALID_POINT_TYPE = {"REL":0, "ABS":1}
VALID_TRIPLET_TYPE = {"DIAGONAL":0, "PLANE":1}

MAGNET_LIMIT = 100

def parse_single_scan(raw):
    # parses a single scan and returns a MagnetScan Object
    print(raw)
    for x in raw['magnet_name']:
        if x not in VALID_MAGNET_NAME:
            raise ValueError(f'Magnet not found or not writable: "{x}"')
    return MagnetScan(
        VALID_SCAN_TYPE[raw['scan_type']],
        [x for x in raw['magnet_name'] if x in VALID_MAGNET_NAME],# else raise ValueError()],
        raw['nominal_sets'],
        [VALID_APPROACH_FROM[x] for x in raw['approach_from']],
        [VALID_POINT_TYPE[x] for x in raw['point_type']],
        raw['scan_points']
    )

def parse_config_create_scan(raw_scan):
    '''
        Parses the input from the json file into one or more MagnetScan objects
    '''
    these_scans = []
    for name,x in raw_scan['scans'].items():
        these_scans.append(parse_single_scan(x))
    print(these_scans)
    return these_scans

def get_scan_points(scan:MagnetScan, index:int, return_to_initial=True):
    '''
        Returns a list of absolute magnet settings based on the scan_points at the 
        specified index
    '''
    npts = int(scan.scan_points[index][0])
    if(scan.point_type[index] == 0):
        minpower = scan.nominal_sets[index] * scan.scan_points[index][1]
        maxpower = scan.nominal_sets[index] * scan.scan_points[index][2]
    else:
        minpower = scan.nominal_sets[index]
        maxpower = scan.nominal_sets[index]
    print(npts, minpower, maxpower)
    points = list(round(x,3) for x in np.linspace(minpower, maxpower, npts))
    if(np.amax(np.abs(points)) >= MAGNET_LIMIT ):
        raise ValueError(f"Warning: Magnet setpoints nearline limit ({MAGNET_LIMIT}): {points}")

    points.sort()
    if(scan.approach_from[index] == 1):
        # print('reverse')
        points.reverse()

    # add the hysteresis points
    # ten times the distance between points 0 and 1 should be fine
    diff = (points[0] - points[1])*10.0
    points = [points[0] + diff] + points 
    print(diff, points[:3])

    print(points)
    if(np.abs(points[1]) <= np.abs(points[2])):
        raise ValueError(f"ERROR: You should have your points approach 0: {points[0]} -> {points[1]}")

    
    # TODO: Add return to nominal logic
    if(return_to_initial):
        points += [points[0], scan.nominal_sets[index]]


    print(points)
    return points



def export_singlet_scan(scan:MagnetScan):
    '''
        Exports a SINGLET magnet scan to the wavedaq format
    '''
    export = {'set_points':[]}
    this_export = []
    these_points = get_scan_points(scan, 0)
    for i,x in enumerate(these_points):
        this_export.append(
            {scan.magnet_name[0]: x, "settling_time_s": scan.settling_time}
        )
        if( i not in [0, len(these_points)-2]):
            print(i)
            export['set_points'].append(this_export)
            this_export = []

    return export

def export_triplet_scan(scan:MagnetScan):
    '''
        Exports a TRIPLET magnet scan to the wavedaq format
    '''
    # TODO: Fix to make list format for hysteresis points
    export = {'set_points':[]}
    outer_points = (get_scan_points(scan,0, False),get_scan_points(scan,2, False))
    inner_points = get_scan_points(scan,1, False)

    outer_points_hyst = (get_scan_points(scan,0)[-2:],get_scan_points(scan,2)[-2:])
    inner_points_hyst = get_scan_points(scan,1)[-2:]
    
    if((len(outer_points[0]) != len(outer_points[1])) or (tuple(scan.scan_points[0]) != tuple(scan.scan_points[2]))):
        raise ValidationError('First and last points do not have the same Npoints / Range')
    if(scan.triplet_type == 1):
        this_export = []
        for i, trip1 in enumerate(inner_points):
            for j, trip0 in enumerate(outer_points[0]):
                trip2 = outer_points[1][j]
                
                if( i == 0 and j == 0 ):
                    # hysteresis points for both magnets
                    this_export.append(
                        {
                            scan.magnet_name[0]: trip0,
                            scan.magnet_name[1]: trip1,
                            scan.magnet_name[2]: trip2,
                            "settling_time_s": scan.settling_time
                        }
                    )
                elif( i == 0 ):
                    # skip the first col, the rest of the hysteresis points
                    continue
                else:
                    this_export.append(
                            {
                            scan.magnet_name[0]: trip0,
                            scan.magnet_name[1]: trip1,
                            scan.magnet_name[2]: trip2,
                            "settling_time_s": scan.settling_time,
                            "wow":(i,j)
                        }
                    )
                    if(j != 0):
                        export['set_points'].append(this_export)
                        this_export = []
                    
        export['set_points'].append(
            [
                {
                    scan.magnet_name[0]: outer_points_hyst[0][-2],
                    scan.magnet_name[1]: inner_points_hyst[-2],
                    scan.magnet_name[2]: outer_points_hyst[1][-2],
                    "settling_time_s": scan.settling_time,
                    # "wow":(i,j)
                },
                {
                    scan.magnet_name[0]: outer_points_hyst[0][-1],
                    scan.magnet_name[1]: inner_points_hyst[-1],
                    scan.magnet_name[2]: outer_points_hyst[1][-1],
                    "settling_time_s": scan.settling_time,
                    # "wow":(i,j)
                },

            ]
        )
    else:
        raise NotImplementedError()
    return export
def export_scan_to_wavedaq_format(scan:MagnetScan):
    '''
        Exports the MagnetScan object to a format which can be parsed by the WaveDAQ
        See: pioneer_nearline/magnet_iteration/config/epics_example.json
    '''
    if(scan.scan_type == 1):
        return export_singlet_scan(scan)
    elif(scan.scan_type == 3):
        return export_triplet_scan(scan)
    else:
        raise NotImplementedError()

def load_config(infile):
    # loads up an input file
    with open(infile, 'r') as fin:
        return json.load(fin)


def export_scans(infile, outfile):
    config = load_config(infile)
    these_scans = parse_config_create_scan(config)
    exported_scans = [export_scan_to_wavedaq_format(x) for x in these_scans]

    if('.json' not in outfile):
        outfile += '.json'
    for i,x in enumerate(exported_scans):
        print(f"Exporting scan with {len(x['set_points'])} points")
        with open(outfile.replace('.json', f'_{i:02}.json'), 'w') as fout:
            json.dump(x, fout, indent=1)


if __name__ == '__main__':
    if( len(sys.argv) > 2):
        export_scans(sys.argv[1], sys.argv[2])
    else:
        export_scans(sys.argv[1], 'scan.json')