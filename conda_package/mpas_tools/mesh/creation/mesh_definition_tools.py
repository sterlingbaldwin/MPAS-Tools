#!/usr/bin/env python
"""
These functions are tools used to define the ``cellWidth`` variable on
regular lat/lon grids.  The ``cellWidth`` variable is a ``jigsaw`` input that
defines the mesh.
"""
from __future__ import absolute_import, division, print_function, \
    unicode_literals

import numpy as np


def mergeCellWidthVsLat(
        lat,
        cellWidthInSouth,
        cellWidthInNorth,
        latTransition,
        latWidthTransition):
    """
    Combine two cell width distributions using a ``tanh`` function. This is
    intended as part of the workflow to make an MPAS global mesh.

    Parameters
    ----------
    lat : ndarray
        vector of length n, with entries between -90 and 90, degrees

    cellWidthInSouth : ndarray
        vector of length n, first distribution

    cellWidthInNorth : ndarray
        vector of length n, second distribution

    latTransition : float
        lat to change from ``cellWidthInSouth`` to ``cellWidthInNorth`` in
        degrees

    latWidthTransition : float
        width of lat transition in degrees

    Returns
    -------
    cellWidthOut : ndarray
        vector of length n, entries are cell width as a function of lat
    """

    cellWidthOut = np.ones(lat.size)
    if latWidthTransition == 0:
        for j in range(lat.size):
            if lat[j] < latTransition:
                cellWidthOut[j] = cellWidthInSouth[j]
            else:
                cellWidthOut[j] = cellWidthInNorth[j]
    else:
        for j in range(lat.size):
            weightNorth = 0.5 * \
                (np.tanh((lat[j] - latTransition) / latWidthTransition) + 1.0)
            weightSouth = 1.0 - weightNorth
            cellWidthOut[j] = weightSouth * cellWidthInSouth[j] + \
                weightNorth * cellWidthInNorth[j]

    return cellWidthOut


def EC_CellWidthVsLat(lat, cellWidthEq=30.0, cellWidthMidLat=60.0,
                      cellWidthPole=35.0, latPosEq=15.0, latPosPole=73.0,
                      latTransition=40.0, latWidthEq=6.0, latWidthPole=9.0):
    """
    Create Eddy Closure spacing as a function of lat. This is intended as part
    of the workflow to make an MPAS global mesh.

    Parameters
    ----------
    lat : ndarray
       vector of length n, with entries between -90 and 90, degrees

    cellWidthEq : float, optional
       Cell width in km at the equator

    cellWidthMidLat : float, optional
       Cell width in km at mid latitudes

    cellWidthPole : float, optional
       Cell width in km at the poles

    latPosEq : float, optional
       Latitude in degrees of center of the equatorial transition region

    latPosPole : float, optional
       Latitude in degrees of center of the polar transition region

    latTransition : float, optional
       Latitude in degrees of the change from equatorial to polar function

    latWidthEq : float, optional
       Width in degrees latitude of the equatorial transition region

    latWidthPole : float, optional
       Width in degrees latitude of the polar transition region

    Returns
    -------
    cellWidthOut : ndarray
         1D array of same length as ``lat`` with entries that are cell width as
         a function of lat

    Examples
    --------
    Default

    >>> EC60to30 = EC_CellWidthVsLat(lat)

    Half the default resolution:

    >>> EC120to60 = EC_CellWidthVsLat(lat, cellWidthEq=60., cellWidthMidLat=120., cellWidthPole=70.)
    """

    minCellWidth = min(cellWidthEq, min(cellWidthMidLat, cellWidthPole))
    densityEq = (minCellWidth / cellWidthEq)**4
    densityMidLat = (minCellWidth / cellWidthMidLat)**4
    densityPole = (minCellWidth / cellWidthPole)**4
    densityEqToMid = ((densityEq - densityMidLat) * (1.0 + np.tanh(
        (latPosEq - np.abs(lat)) / latWidthEq)) / 2.0) + densityMidLat
    densityMidToPole = ((densityMidLat - densityPole) * (1.0 + np.tanh(
        (latPosPole - np.abs(lat)) / latWidthPole)) / 2.0) + densityPole
    mask = np.abs(lat) < latTransition
    densityEC = np.array(densityMidToPole)
    densityEC[mask] = densityEqToMid[mask]
    cellWidthOut = minCellWidth / densityEC**0.25

    return cellWidthOut


def RRS_CellWidthVsLat(lat, cellWidthEq, cellWidthPole):
    """
    Create Rossby Radius Scaling as a function of lat.  This is intended  as
    part of the workflow to make an MPAS global mesh.

    Parameters
    ----------
    lat : ndarray
       vector of length n, with entries between -90 and 90, degrees

    cellWidthEq : float, optional
       Cell width in km at the equator

    cellWidthPole : float, optional
       Cell width in km at the poles

    Returns
    -------
    cellWidthOut : ndarray
         1D array of same length as ``lat`` with entries that are cell width as
         a function of lat

    Examples
    --------
    >>> RRS18to6 = EC_CellWidthVsLat(lat, 18., 6.)
    """

    # ratio between high and low resolution
    gamma = (cellWidthPole / cellWidthEq)**4.0

    densityRRS = (1.0 - gamma) * \
        np.power(np.sin(np.deg2rad(np.absolute(lat))), 4.0) + gamma
    cellWidthOut = cellWidthPole / np.power(densityRRS, 0.25)
    return cellWidthOut


def AtlanticPacificGrid(lat, lon, cellWidthInAtlantic, cellWidthInPacific):
    """
    Combine two cell width distributions using a ``tanh`` function.

    Parameters
    ----------
    lat : ndarray
       vector of length n, with entries between -90 and 90, degrees

    lon : ndarray
       vector of length m, with entries between -180, 180, degrees

    cellWidthInAtlantic : float, optional
       vector of length n, cell width in Atlantic as a function of lon, km

    cellWidthInPacific : float, optional
       vector of length n, cell width in Pacific as a function of lon, km

    Returns
    -------
    cellWidthOut : ndarray
         m by n array, grid cell width on globe, km

    """
    cellWidthOut = np.zeros((lat.size, lon.size))
    for i in range(lon.size):
        for j in range(lat.size):
            # set to Pacific mask as default
            cellWidthOut[j, i] = cellWidthInPacific[j]
            # test if in Atlantic Basin:
            if lat[j] > 65.0:
                if (lon[i] > -150.0) & (lon[i] < 170.0):
                    cellWidthOut[j, i] = cellWidthInAtlantic[j]
            elif lat[j] > 20.0:
                if (lon[i] > -100.0) & (lon[i] < 35.0):
                    cellWidthOut[j, i] = cellWidthInAtlantic[j]
            elif lat[j] > 0.0:
                if (lon[i] > -2.0 * lat[j] - 60.0) & (lon[i] < 35.0):
                    cellWidthOut[j, i] = cellWidthInAtlantic[j]
            else:
                if (lon[i] > -60.0) & (lon[i] < 20.0):
                    cellWidthOut[j, i] = cellWidthInAtlantic[j]
    return cellWidthOut
