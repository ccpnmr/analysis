"""
A basic SS drawer using matplotlib

As seen in https://gist.github.com/JoaoRodrigues/f9906b343d3acb38e39f2b982b02ecb0

"""


import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpl_patches
import matplotlib.ticker as ticker


DSSP_definitions = {
           'H': 'H', # 3-turn helix (310 helix). Min length 3 residues.
           'G': 'H', # 4-turn helix (α helix). Minimum length 4 residues.
           'I': 'H',  #  5-turn helix (π helix). Minimum length 5 residues.
           'B': 'E', # extended strand in parallel and/or anti-parallel β-sheet conformation. Min length 2 residues.
           'E': 'E', # residue in isolated β-bridge (single pair β-sheet hydrogen bond formation)
           'T': 'T', # hydrogen bonded turn (3, 4 or 5 turn)
           'S': 'T', #  coil (residues which are not in any of the above conformations).
            'C':'C', # DSSP_definitions, only a blank placeholder to join blocks,
            }

def createBlocksFromSequence(ss_sequence):
    ss_blocks = []  # (type, start, end)
    prev_ss = None
    for idx, elem in enumerate(ss_sequence):
        reduced_elem = DSSP_definitions.get(elem, 'C')
        if reduced_elem != prev_ss:
            ss_blocks.append([reduced_elem, idx, idx])
            prev_ss = reduced_elem
        ss_blocks[-1][-1] = idx
    return ss_blocks


def plotSS(ss_blocks, sequence, startingResidueCode=1, helix_as_cylinder = True, figure=None, axis = None, showExtraXTicks=2, showBottomAxis=False):
    if figure is None:
        figure = plt.figure()
    if axis is None:
        axis = figure.add_subplot(111)
    n_res = len(sequence)
    startRC = startingResidueCode
    endRC = startRC + n_res + 1

    x_axis_ticks = np.arange(startRC,endRC)

    helix_as_wave = False
    if not helix_as_cylinder:
        helix_as_wave = True

    fc_sheet = 'blue'
    fc_helix = 'red'
    fc_coil = 'black'
    ec = 'none'

    width = 2.0  # General width controller
    helix_arc_width = 4.0
    coil_thickness_factor = 1/12
    edge_thickness = 1.0
    sheet_thickness_factor = 2/3
    turn_thickness_factor = 1/2

    # Draw artists
    width = 2.0
    for blk_idx, ss_blk in enumerate(ss_blocks, ):
        ss_type, start, last = ss_blk
        start, last = start+startRC, last+startRC

        if helix_as_cylinder and ss_type == 'H':
            # Draw rectangle capped by two elipses
            # Elipse width = 1 residue
            # Origin is *center* of elipse
            # Order of drawing matters for overlap
            # First elipse
            elength = width / 2  # horizontal diameter
            height = width - 0.001  # vertical axis (slight offset bc of edge)
            origin = (start + elength/2, height/2)
            e = mpl_patches.Ellipse(origin, elength, height,
                                    linewidth=edge_thickness,
                                    edgecolor='black', facecolor=fc_helix)
            axis.add_patch(e)
            # Rectangle(s)
            length = last - start + 1 - elength  # deduct l of the ellipses
            height = width  # rectangle width is fraction of global
            origin = (start + elength/2, 0)  # origin is lower left: make it v-cntr
            e = mpl_patches.Rectangle(origin, length, height,
                                      edgecolor='none', facecolor=fc_helix)
            axis.add_patch(e)

            # Second elipse
            height = width - 0.001  # vertical axis
            origin = (last + 1 - elength/2, height/2)
            e = mpl_patches.Ellipse(origin, elength, height,
                                    linewidth=edge_thickness,
                                    edgecolor='black', facecolor=fc_helix)

            axis.add_patch(e)

        elif helix_as_wave and ss_type == 'H':
            # Draw as consecutive elyptical arcs
            height = width
            length = 0.5
            st_theta, en_theta = 0, 180
            for t_start in np.arange(start, last + 1, length):  # turns
                origin = (t_start + 0.25, height/2)
                e = mpl_patches.Arc(origin, length, height,
                                    linewidth=helix_arc_width,
                                    # Add a bit to each angle to avoid sharp cuts
                                    # that show as white lines in plot
                                    theta1=st_theta - 1, theta2=en_theta + 1,
                                    edgecolor=fc_helix)

                st_theta += 180
                en_theta += 180
                axis.add_patch(e)

        elif ss_type == 'E':
            # Draw arrow
            length = last - start + 1
            tail_height = width * sheet_thickness_factor
            head_height = width

            e = mpl_patches.FancyArrow(start, width/2,  # x, y of tail
                                       length, 0,  # dx, dy=0 -> flat arrow
                                       length_includes_head=True,
                                       head_length=length/4,
                                       head_width=head_height - 0.001,
                                       width=tail_height,
                                       facecolor=fc_sheet,
                                       edgecolor=ec,
                                       linewidth=edge_thickness)

            axis.add_patch(e)

        elif ss_type == 'T':
            # Draw turn as thin arc
            height = width
            length = last - start + 1
            st_theta, en_theta = 0, 180
            origin = (start + length / 2, height/2)
            e = mpl_patches.Arc(origin, length, height,
                                linewidth=helix_arc_width,
                                theta1=st_theta, theta2=en_theta,
                                edgecolor=fc_helix)

            axis.add_patch(e)

        else:  # draw line (thin Rectangle)
            length = last - start + 1
            height = width * coil_thickness_factor

            # Offset ends to fake continuity
            prev_blk_type = ss_blocks[blk_idx - 1][0]
            if prev_blk_type in ('H', 'T'):
                # Rougly the same size as the linewidth
                start -= 4/72
                length += 4/72
            elif prev_blk_type == 'E':
                # Go wild
                start -= 0.5
                length += 0.5

            if (blk_idx + 1) < len(ss_blocks):
                next_blk_type = ss_blocks[blk_idx + 1][0]
                if next_blk_type in ('H', 'T'):
                    length += 4/72
                elif next_blk_type == 'E':
                    length += 0.5

            origin = (start, width/2 - height/2)  # vertical center

            e = mpl_patches.Rectangle(origin, length, height,
                                      linewidth=edge_thickness,
                                      edgecolor=ec, facecolor=fc_coil)
            axis.add_patch(e)




    for i, txt in enumerate(sequence):
        axis.annotate(str(txt), (x_axis_ticks[i], 5 ), fontsize=5, ha='center')

    # Set tick formatting
    axis.set_ylim([-1, 5])
    # axis.set_xticks(x_axis_ticks)
    for tick in axis.xaxis.get_minor_ticks():
        # tick.tick1line.set_markersize(0)
        # tick.tick2line.set_markersize(0)
        tick.label1.set_horizontalalignment('center')

    axis.set_xlim(startRC - showExtraXTicks, endRC + showExtraXTicks)
    # axis.set_xticklabels(resn_labels, rotation=90)

    # Set axis labels
    # axis.set_xlabel('Residue Number')
    # Overall plot formatting
    axis.set_aspect(0.5)
    axis.spines['left'].set_visible(False)
    axis.spines['right'].set_visible(False)
    axis.spines['top'].set_visible(False)
    axis.get_yaxis().set_visible(False)
    axis.get_xaxis().set_visible(showBottomAxis)
    axis.spines['bottom'].set_visible(showBottomAxis)
    # plt.show()
    return axis


if __name__ == '__main__':
    ss_sequence   =  'BBBBBBCCCCBBBBBBCCCCHHHHHHHHHHHHHHCCCCCBBBBCCCCCBBBBBC'
    sequence  = 'YKLILNGKTLKGETTTEAVDAATAEKVFKQYANDNGVDGEWTYDAATKTFTVTE'
    startingResidueCode = 17
    blocks = createBlocksFromSequence(ss_sequence=ss_sequence)

    axss = plotSS(blocks, sequence, startingResidueCode=startingResidueCode)
    plt.show()


