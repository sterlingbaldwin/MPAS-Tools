from __future__ import absolute_import, division, print_function, \
    unicode_literals

import numpy as np

from netCDF4 import Dataset as NetCDFFile
from mpas_tools.mesh.creation.util import circumcenter

import argparse


def triangle_to_netcdf(node, ele, output_name):
    """
    Converts mesh data defined in triangle format to NetCDF

    Parameters
    ----------
    node : str
        A node file name
    ele : str
        An element file name
    output_name: str
        The name of the output file
    """
    # Authors: Phillip J. Wolfram, Matthew Hoffman and Xylar Asay-Davis
    on_sphere = False
    grid = NetCDFFile(output_name, 'w', format='NETCDF3_CLASSIC')

    # Get dimensions
    # Get nCells
    cell_info = open(node, 'r')
    nCells = -1  # There is one header line
    for block in iter(lambda: cell_info.readline(), ""):
        if block.startswith("#"):
            continue  # skip comment lines
        nCells = nCells + 1
    cell_info.close()

    # Get vertexDegree and nVertices
    cov_info = open(ele, 'r')
    vertexDegree = 3  # always triangles with Triangle!
    nVertices = -1  # There is one header line
    for block in iter(lambda: cov_info.readline(), ""):
        if block.startswith("#"):
            continue  # skip comment lines
        nVertices = nVertices + 1
    cov_info.close()

    if vertexDegree != 3:
        ValueError("This script can only compute vertices with triangular "
                   "dual meshes currently.")

    grid.createDimension('nCells', nCells)
    grid.createDimension('nVertices', nVertices)
    grid.createDimension('vertexDegree', vertexDegree)

    # Create cell variables and sphere_radius
    xCell_full = np.zeros((nCells,))
    yCell_full = np.zeros((nCells,))
    zCell_full = np.zeros((nCells,))

    cell_info = open(node, 'r')
    cell_info.readline()  # read header
    i = 0
    for block in iter(lambda: cell_info.readline(), ""):
        block_arr = block.split()
        if block_arr[0] == "#":
            continue  # skip comment lines
        xCell_full[i] = float(block_arr[1])
        yCell_full[i] = float(block_arr[2])
        zCell_full[i] = 0.0  # z-position is always 0.0 in a planar mesh
        i = i + 1
    cell_info.close()

    grid.on_a_sphere = "NO"
    grid.sphere_radius = 0.0

    cellsOnVertex_full = np.zeros(
        (nVertices, vertexDegree), dtype=np.int32)

    cov_info = open(ele, 'r')
    cov_info.readline()  # read header
    iVertex = 0
    for block in iter(lambda: cov_info.readline(), ""):
        block_arr = block.split()
        if block_arr[0] == "#":
            continue  # skip comment lines
        cellsOnVertex_full[iVertex, :] = int(-1)
        # skip the first column, which is the triangle number, and then
        # only get the next 3 columns
        for j in np.arange(0, 3):
            cellsOnVertex_full[iVertex, j] = int(block_arr[j + 1])

        iVertex = iVertex + 1

    cov_info.close()

    # Create vertex variables
    xVertex_full = np.zeros((nVertices,))
    yVertex_full = np.zeros((nVertices,))
    zVertex_full = np.zeros((nVertices,))

    for iVertex in np.arange(0, nVertices):
        cell1 = cellsOnVertex_full[iVertex, 0]
        cell2 = cellsOnVertex_full[iVertex, 1]
        cell3 = cellsOnVertex_full[iVertex, 2]

        x1 = xCell_full[cell1 - 1]
        y1 = yCell_full[cell1 - 1]
        z1 = zCell_full[cell1 - 1]
        x2 = xCell_full[cell2 - 1]
        y2 = yCell_full[cell2 - 1]
        z2 = zCell_full[cell2 - 1]
        x3 = xCell_full[cell3 - 1]
        y3 = yCell_full[cell3 - 1]
        z3 = zCell_full[cell3 - 1]

        pv = circumcenter(on_sphere, x1, y1, z1, x2, y2, z2, x3, y3, z3)
        xVertex_full[iVertex] = pv.x
        yVertex_full[iVertex] = pv.y
        zVertex_full[iVertex] = pv.z

    meshDensity_full = grid.createVariable(
        'meshDensity', 'f8', ('nCells',))

    meshDensity_full[0:nCells] = 1.0

    var = grid.createVariable('xCell', 'f8', ('nCells',))
    var[:] = xCell_full
    var = grid.createVariable('yCell', 'f8', ('nCells',))
    var[:] = yCell_full
    var = grid.createVariable('zCell', 'f8', ('nCells',))
    var[:] = zCell_full
    var = grid.createVariable('xVertex', 'f8', ('nVertices',))
    var[:] = xVertex_full
    var = grid.createVariable('yVertex', 'f8', ('nVertices',))
    var[:] = yVertex_full
    var = grid.createVariable('zVertex', 'f8', ('nVertices',))
    var[:] = zVertex_full
    var = grid.createVariable(
        'cellsOnVertex', 'i4', ('nVertices', 'vertexDegree',))
    var[:] = cellsOnVertex_full

    grid.sync()
    grid.close()


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "-n",
        "--node",
        dest="node",
        required=True,
        help="input .node file generated by Triangle.",
        metavar="FILE")
    parser.add_argument(
        "-e",
        "--ele",
        dest="ele",
        required=True,
        help="input .ele file generated by Triangle.",
        metavar="FILE")
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        default="grid.nc",
        help="output file name.",
        metavar="FILE")
    options = parser.parse_args()

    triangle_to_netcdf(options.node, options.ele, options.output)
