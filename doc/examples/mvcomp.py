#!/usr/bin/env python

#
# Compare two motion vector dumps (from extract_mvs) and compute the
# value of the 2-bit pattern.
#

import sys
#import pandas as pd


def parse_line_dist(l):
    tokens = l.split(',')
    d = {}
    d['framenum'] = int(tokens[0])
    d['source'] = int(tokens[1])

    d['blockw'] = int(tokens[2])
    d['blockh'] = int(tokens[3])

    d['srcx'] = int(tokens[4])
    d['srcy'] = int(tokens[5])

    d['dstx'] = int(tokens[6])
    d['dsty'] = int(tokens[7])

    d['flags'] = tokens[8]
    
    return d

def parse_line(l):
    tokens = l.split(',')
    d = {}
    d['framenum'] = int(tokens[0])
    d['source'] = int(tokens[1])

    d['blockw'] = int(tokens[2])
    d['blockh'] = int(tokens[3])

    d['motion_x'] = int(tokens[4])
    d['motion_y'] = int(tokens[5])

    d['motion_scale'] = int(tokens[6])
    
    return d


def res_decode(dx,dy):
    if dx == -1:
        bit0 = 0
    elif dx == 1:
        bit0 = 1
    if dy == -1:
        bit1 = 0
    elif dy == 1:
        bit1 = 1

    return (bit1 << 1) | bit0

if len(sys.argv) != 3:
    print("Usage: {} <cover> <steg>".format(sys.argv[0]))
else:
    count = 0
    good_resid = 0
    bad_resid = 0
    k = 0
    still_more = True
    with open(sys.argv[1], 'r') as fc:
        with open(sys.argv[2], 'r') as fs:
            while still_more:
                linec = fc.readline()
                lines = fs.readline()
                if not (linec and lines):
                    still_more = False
                elif k > 0:
                    pc = parse_line(linec)
                    ps = parse_line(lines)

                    if pc['framenum'] != ps['framenum']:
                        # print("We are now at different frame numbers: {} vs. {}".format(pc[0], ps[0]))
                        if pc['framenum'] < ps['framenum']:
                            while pc['framenum'] < ps['framenum']:
                                linec = fc.readline()
                                pc = parse_line(linec)
                        else:
                            while ps['framenum'] < ps['framenum']:
                                lines = fs.readline()
                                ps = parse_line(lines)

                    if pc['blockw'] != ps['blockw'] or pc['blockh'] != ps['blockh']:
                        print("Block widths and heights differ at frame {}: {}x{} vs {}x{}".format(pc['framenum'], pc['blockw'], pc['blockh'], ps['blockw'], ps['blockh']))
                        exit()

                    mxc = pc['motion_x']
                    myc = pc['motion_y']

                    mxs = ps['motion_x']
                    mys = ps['motion_y']

                    rx = mxs - mxc
                    ry = mys - myc

                    if abs(rx) == 1 and abs(ry) == 1:
                        print("Residuals: [x,y] = [{},{}] => {}".format(rx,ry, res_decode(rx,ry)))
                        good_resid += 1
                    elif rx == 0 and ry == 0:
                        count += 1
                    else:
                        # print("Bad residuals: {} {}".format(rx,ry))
                        bad_resid += 1
                k += 1
                
    print("Summary:")
    print("Found {} good residuals.".format(good_resid))
    print("Found {} unaltered blocks.".format(count))
    print("Found {} bad residuals.".format(bad_resid))
