#!/usr/bin/env python

#
# Compare two motion vector dumps (from extract_mvs) and compute the
# value of the 2-bit pattern.
#

import sys


def parse_line(l):
    p = [ int(x) for x in l.split(',')[0:-1] ]
    return p


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

                    if pc[0] != ps[0]:
                        # print("We are now at different frame numbers: {} vs. {}".format(pc[0], ps[0]))
                        if pc[0] < ps[0]:
                            while pc[0] < ps[0]:
                                linec = fc.readline()
                                pc = parse_line(linec)
                        else:
                            while ps[0] < ps[0]:
                                lines = fs.readline()
                                ps = parse_line(lines)

                    if pc[2] != ps[2] or pc[3] != ps[3]:
                        print("Block widths and heights differ at frame {}: {}x{} vs {}x{}".format(pc[0], pc[2], pc[3], ps[2], ps[3]))
                        exit()

                    mxc = pc[6] - pc[4]
                    myc = pc[7] - pc[5]

                    mxs = ps[6] - ps[4]
                    mys = pc[7] - pc[5]

                    rx = mxs - mxc
                    ry = mys - myc

                    if abs(rx) == 1 and abs(ry) == 1:
                        print("Residuals: [x,y] = [{},{}] => {}".format(rx,ry, res_decode(rx,ry)))
                        good_resid += 1
                    elif rx == 0 and ry == 0:
                        count += 1
                    else:
                        print("Bad residuals: {} {}".format(rx,ry))
                        bad_resid += 1
                k += 1
                
    print("Summary:")
    print("Found {} good residuals.".format(good_resid))
    print("Found {} unaltered blocks.".format(count))
    print("Found {} bad residuals.".format(bad_resid))
