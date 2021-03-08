#!/usr/bin/env python

#
# Compare two motion vector dumps (from extract_mvs) and compute the
# value of the 2-bit pattern.
#

import sys
#import pandas as pd

RADIUS = 8

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

    d['srcx'] = int(tokens[4])
    d['srcy'] = int(tokens[5])

    d['motion_x'] = int(tokens[6])
    d['motion_y'] = int(tokens[7])

    d['motion_scale'] = int(tokens[8])

#    print(d)
    
    return d

def res_decode(dx,dy):
    if dx > 0:
        bit0 = 1
    else:
        bit0 = 0
    if dy > 0:
        bit1 = 2
    else:
        bit1 = 0

    return bit1 | bit0




def check_cover(filename, thresh=8, stride=81):
    frameno = 0
    k = 0
    with open(filename, 'r') as fc:
        for linec in fc:
            if k == 0:
                k += 1
            else:
                pc = parse_line(linec)
                mx = pc['motion_x'] / pc['motion_scale']
                my = pc['motion_y'] / pc['motion_scale']

                mb_x = int(pc['srcx'] / 16)
                mb_y = int(pc['srcy'] / 16)

                idx = round(mb_x + (mb_y * stride))
            
                if pc['framenum'] != frameno:
                    frameno = pc['framenum']
                    print("New frame:  Frame {}".format(frameno))
                if abs(mx) > thresh or abs(my) > thresh:
                    print("Will modify [{},{}]=>[{},{}]=>{}".format(pc['srcx'], pc['srcy'], mb_x, mb_y, idx))
            



if len(sys.argv) < 2:
    print("Usage: {} <cover> [<steg> [stride=81]]".format(sys.argv[0]))
elif len(sys.argv) < 3:
    check_cover(sys.argv[1])
else:
    count = 0
    good_resid = 0
    bad_resid = 0
    k = 0
    still_more = True
    if len(sys.argv) > 3:
        stride = int(sys.argv[3])
    else:
        stride = 81
    frameno = 0
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
                            while ps['framenum'] < pc['framenum']:
                                lines = fs.readline()
                                ps = parse_line(lines)

                    if pc['framenum'] > frameno:
                        frameno = pc['framenum']
                        print("Frame number {}".format(frameno))
                        
                    if pc['blockw'] != ps['blockw'] or pc['blockh'] != ps['blockh']:
                        print("Block widths and heights differ at frame {}: {}x{} vs {}x{}".format(pc['framenum'], pc['blockw'], pc['blockh'], ps['blockw'], ps['blockh']))
                        exit()

                    mxc = pc['motion_x']  / pc['motion_scale']
                    myc = pc['motion_y']  / pc['motion_scale']

                    mxs = ps['motion_x']  / ps['motion_scale']
                    mys = ps['motion_y']  / ps['motion_scale']

                    rx = abs(mxs - mxc)
                    ry = abs(mys - myc)

                    # OK - WE NEED EXTRACT_MVS TO COUGH UP THE BLOCK COORDINATES!
                    # OR AT LEAST THE INDICES!
                    if abs(mxc) > RADIUS or abs(myc) > RADIUS:
                        # This doesn't fly, since srcx and srcy are
                        # not necessarily multiples of 8.  Yet motion
                        # vectors are computed for each macroblock,
                        # and these have specific mb_x and mb_y
                        # coordinates in units of macroblocks.  So how
                        # to get?

                        mb_x = int(pc['srcx'] / 16)
                        mb_y = int(pc['srcy'] / 16)

                        idx = round(mb_x + (mb_y * stride))
                        print("Residuals: ( [{},{}]=>[{},{}]=>{} ) = [{},{}] => {} (vs. {})".format(pc['srcx'], pc['srcy'], mb_x, mb_y, idx, rx,ry, res_decode(rx,ry), int(idx)&0x3))
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
