#!/usr/bin/python
"""
Process Matlab load review output files. This script is meant for two purposes:

1) Read in the propagation ending information and write a review schedule input
   file for MCC to read. This is done with this type of syntax:
   
   python LoadReviewTools.py --Propschedule=MAY0712A \
   --OutputPropEndingConfiguration

2) Read in both the propagation and review schdule output files and write a
   thermal loadreview report listing all the relevant temperature data. This
   is done with this type of syntax:

   python loadreviewtools.py --Propschedule=MAY0712A --Reviewschedule=MAY1412A \
   --OutputThermalReport

NOTE: This is meant to be run from within the working directory
"""

import sys
import os
import numpy as np
import argparse
import glob
from tempfile import TemporaryDirectory


class LoadReviewTools(object):
    def __init__(self, propschedule, reviewschedule=None):

        self.fileparts = {
            "psmc": "_1pdeaat_plot.txt",
            "dpa": "_dpa_plot.txt",
            "dea": "_dea_plot.txt",
            "tank": "_pftank2t_plot.txt",
            "aca": "_aca_plot.txt",
            "mups": "_mups_valves_plot.txt",
            "oba": "_4rt700t_plot.txt",
            "pline03t": "_pline03t_plot.txt",
            "pline04t": "_pline04t_plot.txt",
            "hrc": "_2ceahvpt_plot.txt",
            "acisfp": "_acis_fp_plot.txt",
        }

        self.headerinfo = {
            "psmc": {
                "columns": 6,
                "names": ["Time", "1PDEAAT", "PIN1AT", "Pitch", "Roll", "Sun_Body_Y"],
                "title": "ACIS: PSMC",
            },
            "dpa": {
                "columns": 11,
                "names": [
                    "Time",
                    "1DPAMZT",
                    "DPA0",
                    "Pitch",
                    "Roll",
                    "Sun_Body_Y",
                    "SimPos",
                    "FEP_Count",
                    "CCD_Count",
                    "Vid_Board",
                    "Clocking",
                ],
                "title": "ACIS: DPA",
            },
            "dea": {
                "columns": 11,
                "names": [
                    "Time",
                    "1DEAMZT",
                    "DEA0",
                    "Pitch",
                    "Roll",
                    "Sun_Body_Y",
                    "SimPos",
                    "FEP_Count",
                    "CCD_Count",
                    "Vid_Board",
                    "Clocking",
                ],
                "title": "ACIS: DEA",
            },
            "tank": {
                "columns": 7,
                "names": ["Time", "PFTANK2T", "PFTANKIP", "PF0TANK2T", "Pitch", "Roll", "Sun_Body_Y"],
                "title": "Spacecraft: Fuel Tank",
            },
            "aca": {
                "columns": 5,
                "names": ["Time", "AACCCDPT", "ACA0", "Pitch", "Roll"],
                "title": "Spacecraft: Aspect Camera",
            },
            "mups": {
                "columns": 6,
                "names": ["Time", "PM1THV2T", "PM1THV2T_0", "PM2THV1T", "PM2THV1T_0", "PM2THV1T_1"],
                "title": "Spacecraft: MUPS Valves",
            },
            "cc": {
                "columns": 5,
                "names": ["Time", "TCYLAFT6", "TCYLAFT6_0", "Pitch", "Roll"],
                "title": "Spacecraft: Central Cylinder",
            },
            "oba": {
                "columns": 5,
                "names": ["Time", "4RT700T", "4RT700T_0", "Pitch", "Roll"],
                "title": "OBA: Forward Bulkhead",
            },
            "pline03t": {
                "columns": 5,
                "names": ["Time", "PLINE03T", "PLINE03T_0", "Pitch", "Roll"],
                "title": "PLINE03T",
            },
            "pline04t": {
                "columns": 5,
                "names": ["Time", "PLINE04T", "PLINE04T_0", "Pitch", "Roll"],
                "title": "PLINE04T",
            },
            "hrc": {
                "columns": 19,
                "names": [
                    "Time",
                    "2CEAHVPT",
                    "CEA0",
                    "CEA1",
                    "15V",
                    "24V",
                    "HRCI",
                    "HRCS",
                    "Shield",
                    "5V_A",
                    "5V_B",
                    "Pitch",
                    "Roll",
                    "SimPos",
                    "FEP_Count",
                    "CCD_Count",
                    "Vid_Board",
                    "Clocking",
                    "DH_Heater",
                ],
                "title": "ISIM: HRC CEA",
            },
            "acisfp": {
                "columns": 23,
                "names": [
                    "Time",
                    "FPTEMP",
                    "FPTEMP_Rel",
                    "Solid_Angle",
                    "in_out",
                    "1CBAT",
                    "SIM_PX",
                    "Pitch",
                    "Roll",
                    "Sun_Body_Y",
                    "SimPos",
                    "FEP_Count",
                    "CCD_Count",
                    "Vid_Board",
                    "Clocking",
                    "CTI",
                    "Radmon_Enabled",
                    "DH_Heater",
                    "ACIS_NIL_Undercover",
                    "SI",
                    "Cold_FP",
                    "FPTEMP_Limit",
                    "Within_Limit",
                ],
                "title": "ISIM: ACIS FP",
            },
        }

        self.propnames = [
            "PM1THV2T",
            "PM1THV2T_0",
            "PM2THV1T",
            "PM2THV1T_0",
            "PM2THV1T_1",
            "1PDEAAT",
            "PIN1AT",
            "TCYLAFT6",
            "TCYLAFT6_0",
            "1DPAMZT",
            "DPA0",
            "PFTANK2T",
            "PF0TANK2T",
            "SimPos",
            "chips",
            "FEP_Count",
            "CCD_Count",
            "Vid_Board",
            "Clocking",
            "AACCCDPT",
            "ACA0",
            "4RT700T",
            "4RT700T_0",
            "1DEAMZT",
            "DEA0",
            "Roll",
            "Sun_Body_Y",
            "PLINE03T",
            "PLINE03T_0",
            "PLINE04T",
            "PLINE04T_0",
            "2CEAHVPT",
            "CEA0",
            "CEA1",
            "15V",
            "24V",
            "HRCI",
            "HRCS",
            "Shield",
            "5V_A",
            "5V_B",
            "FPTEMP",
            "FPTEMP_Rel",
            "Solid_Angle",
            "in_out",
            "1CBAT",
            "CTI",
            "Radmon_Enabled",
            "DH_Heater",
            "ACIS_NIL_Undercover",
            "SI",
            "Cold_FP",
            "FPTEMP_Limit",
            "Within_Limit",
        ]

        self.plotorder = ["oba", "tank", "mups", "psmc", "dpa", "dea", "aca", "pline03t", "pline04t", "acisfp"]

        self.propschedule = propschedule
        self.reviewschedule = reviewschedule

        if reviewschedule == None:
            self.writePropData()
        else:
            self.writeChecklistData()

    def _readfile(self, filename, subheaderinfo):

        # Headerinfo should be a sub-dict of the original header info,
        # including only the information for the current model

        fin = open(filename, "rb")
        datalines = fin.readlines()
        fin.close()

        header = datalines.pop(0)

        data = {}

        for num, name in enumerate(subheaderinfo["names"]):
            if name.lower() in ["time", "si", "within_limit", "15v", "24v", "hrci", "hrcs", "shield", "5v_a", "5v_b"]:
                data.update(dict({name: np.array([line.strip().split()[num] for line in datalines])}))
            # elif name.lower() in ['si', 'Within_Limit']:
            #     data.update(dict( { name:np.array( [np.double(line.strip().split()[num]) for line in datalines]) } ))
            else:
                data.update(dict({name: np.array([np.double(line.strip().split()[num]) for line in datalines])}))

        return data

    def _writeReportData(self, outfile, propdata, reviewdata, names, modelname):

        # The 'names' list should not include time

        outfile.write(("-" * 79) + "\n")
        outfile.write("%s Report\n" % modelname)
        outfile.write(("-" * 79) + "\n\n")

        outfile.write("Propagation:\n")
        outfile.write("------------\n")

        outfile.write("Start:    %s\n" % (propdata["Time"][0]))

        for name in names:
            if name.lower() in ["time", "si", "within_limit", "15v", "24v", "hrci", "hrcs", "shield", "5v_a", "5v_b"]:
                outfile.write("    %s: %s\n" % (name, propdata[name][0]))
            else:
                outfile.write("    %s: %f\n" % (name, propdata[name][0]))

        outfile.write("\nReviewed Schedule:\n")
        outfile.write("-------------------\n")

        outfile.write("Start:    %s\n" % (reviewdata["Time"][0]))

        for name in names:
            if name.lower() in ["time", "si", "within_limit", "15v", "24v", "hrci", "hrcs", "shield", "5v_a", "5v_b"]:
                outfile.write("    %s: %s\n" % (name, reviewdata[name][0]))
            else:
                outfile.write("    %s: %f\n" % (name, reviewdata[name][0]))

        outfile.write("\nMax Values:\n")
        for name in names:
            if name.lower() not in [
                "time",
                "si",
                "within_limit",
                "15v",
                "24v",
                "hrci",
                "hrcs",
                "shield",
                "5v_a",
                "5v_b",
            ]:
                maxind = np.nanargmax(reviewdata[name])
                outfile.write("    %s: %f  (%s)\n" % (name, reviewdata[name][maxind], reviewdata["Time"][maxind]))

        outfile.write("\nMin Values:\n")
        for name in names:
            if name.lower() not in [
                "time",
                "si",
                "within_limit",
                "15v",
                "24v",
                "hrci",
                "hrcs",
                "shield",
                "5v_a",
                "5v_b",
            ]:
                minind = np.nanargmin(reviewdata[name])
                outfile.write("    %s: %f  (%s)\n" % (name, reviewdata[name][minind], reviewdata["Time"][minind]))

        outfile.write("\nEnd: %s\n" % (reviewdata["Time"][-1]))
        for name in names:
            if name.lower() in ["time", "si", "within_limit", "15v", "24v", "hrci", "hrcs", "shield", "5v_a", "5v_b"]:
                outfile.write("    %s: %s\n" % (name, reviewdata[name][-1]))
            else:
                outfile.write("    %s: %f\n" % (name, reviewdata[name][-1]))

        outfile.write("\n\n\n")

        return outfile

    def writeChecklistData(self):

        reviewfilename = self.reviewschedule + "_Thermal_Load_Review_Report.txt"
        outfile = open(reviewfilename, "w")

        for name in self.plotorder:

            filename = self.propschedule + self.fileparts[name]
            propdata = self._readfile(filename, self.headerinfo[name])

            filename = self.reviewschedule + self.fileparts[name]
            reviewdata = self._readfile(filename, self.headerinfo[name])

            datanames = self.headerinfo[name]["names"]
            datanames.pop(0)  # remove time

            self._writeReportData(outfile, propdata, reviewdata, datanames, self.headerinfo[name]["title"])
            self._writeReportData(sys.stdout, propdata, reviewdata, datanames, self.headerinfo[name]["title"])

        outfile.close()
        print(("Wrote thermal report data to " "%s_Thermal_Load_Review_Report.txt\n" % reviewfilename))

    def writePropData(self):

        propfilename = self.propschedule + "_Ending_Configuration.txt"
        outfile = open(propfilename, "w")

        for num, name in enumerate(self.plotorder):
            filename = self.propschedule + self.fileparts[name]
            propdata = self._readfile(filename, self.headerinfo[name])

            datanames = self.headerinfo[name]["names"][1:]

            if num == 0:
                outfile.write("Time of Validity:  %s\n" % (propdata["Time"][-1]))

            for loc in datanames:
                if loc in self.propnames:
                    outfile.write(" %s : %f\n" % (loc, propdata[loc][-1]))

        outfile.close()
        print(("Wrote propagation ending data to %s" % propfilename))


def force_link(src, dest):
    with TemporaryDirectory(dir=os.path.dirname(dest)) as d:
        tmpname = os.path.join(d, "foo")
        os.link(src, tmpname)
        os.replace(tmpname, dest)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--Propschedule")
    parser.add_argument("--Reviewschedule")
    parser.add_argument("--OutputPropEndingConfiguration", action="store_true", default=False)
    parser.add_argument("--OutputThermalReport", action="store_true", default=False)

    args = vars(parser.parse_args())

    if args["OutputPropEndingConfiguration"]:
        LoadReviewTools(propschedule=args["Propschedule"])

    if args["OutputThermalReport"]:
        LoadReviewTools(propschedule=args["Propschedule"], reviewschedule=args["Reviewschedule"])

    # Copy files to parent directory
    for file in glob.glob(args["Reviewschedule"] + "*"):
        # os.link(file, "../" + file)
        force_link(file, "../" + file)








