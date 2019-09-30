#!/usr/bin/env python3
import matplotlib.pyplot as plt
from descartes import PolygonPatch
from shapely.geometry import Polygon, MultiPolygon, shape
from shapely.ops import unary_union
import fiona

def getPolygonForLeastDeprivedZonesEngland(minimumDeprivationRank):
    # Metadata as per https://www.arcgis.com/home/item.html?id=5e1c399d787e48c0902e5fe4fc1ccfe3
    # LSOA01CD: 		LSOA code (2011)
    # LSOA01NM: 		LSOA name (2011)
    # LADcd: 		    Local Authority District code (2019)
    # LADnm: 		    Local Authority District name (2019)
    # IMDScore: 		Index of Multiple Deprivation (IMD) Score
    # IMDRank0: 		Index of Multiple Deprivation (IMD) Rank (where 1 is most deprived)
    # IMDDec0: 		Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)
    # IncScore: 		Income Score (rate)
    # IncRank: 		Income Rank (where 1 is most deprived)
    # IncDec: 		Income Decile (where 1 is most deprived 10% of LSOAs)
    # EmpScore: 		Employment Score (rate)
    # EmpRank: 		Employment Rank (where 1 is most deprived)
    # EmpDec: 		Employment Decile (where 1 is most deprived 10% of LSOAs)
    # EduScore: 		Education, Skills and Training Score
    # EduRank: 		Education, Skills and Training Rank (where 1 is most deprived)
    # EduDec: 		Education, Skills and Training Decile (where 1 is most deprived 10% of LSOAs)
    # HDDScore: 		Health Deprivation and Disability Score
    # HDDRank: 		Health Deprivation and Disability Rank (where 1 is most deprived)
    # HDDDec: 		Health Deprivation and Disability Decile (where 1 is most deprived 10% of LSOAs)
    # CriScore: 		Crime Score
    # CriRank: 		Crime Rank (where 1 is most deprived)
    # CriDec: 		Crime Decile (where 1 is most deprived 10% of LSOAs)
    # BHSScore: 		Barriers to Housing and Services Score
    # BHSRank: 		Barriers to Housing and Services Rank (where 1 is most deprived)
    # BHSDec: 		Barriers to Housing and Services Decile (where 1 is most deprived 10% of LSOAs)
    # EnvScore: 		Living Environment Score
    # EnvRank: 		Living Environment Rank (where 1 is most deprived)
    # EnvDec: 		Living Environment Decile (where 1 is most deprived 10% of LSOAs)
    # IDCScore: 		Income Deprivation Affecting Children Index (IDACI) Score (rate)
    # IDCRank: 		Income Deprivation Affecting Children Index (IDACI) Rank (where 1 is most deprived)
    # IDCDec: 		Income Deprivation Affecting Children Index (IDACI) Decile (where 1 is most deprived 10% of LSOAs)
    # IDOScore: 		Income Deprivation Affecting Older People (IDAOPI) Score (rate)
    # IDORank: 		Income Deprivation Affecting Older People (IDAOPI) Rank (where 1 is most deprived)
    # IDODec: 		Income Deprivation Affecting Older People (IDAOPI) Decile (where 1 is most deprived 10% of LSOAs)
    # CYPScore: 		Children and Young People Sub-domain Score
    # CYPRank: 		Children and Young People Sub-domain Rank (where 1 is most deprived)
    # CYPDec: 		Children and Young People Sub-domain Decile (where 1 is most deprived 10% of LSOAs)
    # ASScore: 		Adult Skills Sub-domain Score
    # ASRank: 		Adult Skills Sub-domain Rank (where 1 is most deprived)
    # ASDec: 		    Adult Skills Sub-domain Decile (where 1 is most deprived 10% of LSOAs)
    # GBScore: 		Geographical Barriers Sub-domain Score
    # GBRank: 		Geographical Barriers Sub-domain Rank (where 1 is most deprived)
    # GBDec: 		    Geographical Barriers Sub-domain Decile (where 1 is most deprived 10% of LSOAs)
    # WBScore: 		Wider Barriers Sub-domain Score
    # WBRank: 		Wider Barriers Sub-domain Rank (where 1 is most deprived)
    # WBDec: 		    Wider Barriers Sub-domain Decile (where 1 is most deprived 10% of LSOAs)
    # IndScore: 		Indoors Sub-domain Score
    # IndRank: 		Indoors Sub-domain Rank (where 1 is most deprived)
    # IndDec: 		Indoors Sub-domain Decile (where 1 is most deprived 10% of LSOAs)
    # OutScore: 		Outdoors Sub-domain Score
    # OutRank: 		Outdoors Sub-domain Rank (where 1 is most deprived)
    # OutDec: 		Outdoors Sub-domain Decile (where 1 is most deprived 10% of LSOAs)
    # TotPop: 		Total population: mid 2015 (excluding prisoners)
    # DepChi: 		Dependent Children aged 0-15: mid 2015 (excluding prisoners)
    # Pop16_59: 		Population aged 16-59: mid 2015 (excluding prisoners)
    # Pop60+: 		Older population aged 60 and over: mid 2015 (excluding prisoners)
    # WorkPop: 		Working age population 18-59/64: for use with Employment Deprivation Domain (excluding prisoners)

    # BLUE = '#6699cc'
    # fig = plt.figure() 
    # ax = fig.gca() 

    filteredZonesPolygons = []
    with fiona.open('datasets/IMD_2019/IMD_2019.shp') as allZones:
        # print("Total zones: " + str(len(allZones)))
        # print(allZones.crs)
        
        for singleZone in allZones:
            if singleZone['properties']['IMDDec0'] >= minimumDeprivationRank:

                filteredZonesPolygons.append(shape(singleZone['geometry']))

                # ax.add_patch(PolygonPatch(singleZone['geometry'], fc=BLUE, ec=BLUE, alpha=0.5, zorder=2 ))

        # print("Total zones after filtering for rank " +str(minimumDeprivationRank)+": " + str(len(filteredZones)))
    
    # ax.axis('scaled')
    # plt.show()
    return MultiPolygon(filteredZonesPolygons)
