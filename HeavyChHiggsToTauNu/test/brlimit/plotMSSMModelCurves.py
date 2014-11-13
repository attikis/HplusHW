#!/usr/bin/env python

import HiggsAnalysis.HeavyChHiggsToTauNu.tools.histograms as histograms
import HiggsAnalysis.HeavyChHiggsToTauNu.tools.tdrstyle as tdrstyle
#import HiggsAnalysis.HeavyChHiggsToTauNu.tools.styles as styles
import HiggsAnalysis.HeavyChHiggsToTauNu.tools.plots as plots

import os
import array

import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.PyConfig.IgnoreCommandLineOptions = True

class DatabaseReader:
    def __init__(self, mssmModel, mHp):
        self._mssmModel = mssmModel
        self._mHp = mHp
        self._results = {} # dictionary, where key is tanbeta
        # Read results
        self._readFromDatabase()
    
    def _readFromDatabase(self):
        myRootFilename = "%s-LHCHXSWG.root"%self._mssmModel
        if not os.path.exists(myRootFilename):
            raise Exception("Error: The root file '%s' for the MSSM model does not exist in this directory!"%myRootFilename)
        # Open root file and obtain branch
        backup = ROOT.gErrorIgnoreLevel
        ROOT.gErrorIgnoreLevel = ROOT.kError
        f = ROOT.TFile.Open(myRootFilename)
        ROOT.gErrorIgnoreLevel = backup
        _treename = "FeynHiggs_results"
        myTree = f.Get(_treename)
        if myTree == None:
            f.Close()
            raise Exception("Error: Could not find tree '%s' in root file '%s'!"%(_treename, myRootFilename))
        # Set branch adresses for reading
        tanbInTree = array.array('d',[0])
        mHpInTree = array.array('d',[0])
        brTauNuInTree = array.array('d',[0])
        brTbInTree = array.array('d',[0])
        sigmaInTree = array.array('d',[0])
        myTree.SetBranchAddress("mHp", mHpInTree)
        myTree.SetBranchAddress("tanb", tanbInTree)
        myTree.SetBranchAddress("BR_Hp_taunu", brTauNuInTree)
        myTree.SetBranchAddress("BR_Hp_tb", brTbInTree)
        myTree.SetBranchAddress("tHp_xsec", sigmaInTree)
        # Find values for requested mHp
        myTanBetaValueFoundStatus = False
        myBranching = None
        i = 0
        nentries = myTree.GetEntries()
        while i < nentries:
            myTree.GetEvent(i)
            if abs(mHpInTree[0] - float(self._mHp)) < 0.0001:
                if tanbInTree[0] > 1.0:
                    # Store value
                    result = {}
                    sigma = sigmaInTree[0]*2.0*0.001 # both charges of H+; fb->pb
                    result["taunu"] = sigma*brTauNuInTree[0];
                    result["tb"] = sigma*brTbInTree[0];
                    result["other"] = sigma*(1.0-brTauNuInTree[0]-brTbInTree[0])
                    result["bigtwo"] = sigma*(brTauNuInTree[0]+brTbInTree[0])
                    self._results["%04.1f"%tanbInTree[0]] = result
            i += 1
        f.Close()

    def getBrGraph(self, resultKey):
        myTanBetaKeys = self._results.keys()
        myTanBetaKeys.sort()
        g = ROOT.TGraph(len(myTanBetaKeys))
        for i in range(0, len(myTanBetaKeys)):
            results = self._results[myTanBetaKeys[i]]
            g.SetPoint(i, float(myTanBetaKeys[i]), results[resultKey])
        return g



def main(opts, taunuContainer, tbContainer, m, scen):
    resultKeys = ["observed", "observedPlusTheorUncert", "observedMinusTheorUncert", "expected", "expectedPlus1Sigma", "expectedPlus2Sigma", "expectedMinus1Sigma", "expectedMinus2Sigma"]
    #resultKeys = ["observed","expected"]
    for myKey in resultKeys:
        scanRanges(opts, taunuContainer, tbContainer, m, 1.1, 75, myKey, scen)
    
    outtxt = ""
    # Print results
    myTanBetaKeys = taunuContainer._results.keys()
    myTanBetaKeys.sort()
    for myResultKey in resultKeys:
        outtxt += "\nTan beta limit scan (%s) for m=%s and key: %s\n"%(scen, m,myResultKey)
        for k in myTanBetaKeys:
            theory = taunuContainer.getResult(k)["sigmaTheory"]
            combineResult = ""
            if taunuContainer.getFailedStatus(k):
                combineResult = "failed"
            else:
                combineResult = "%f pb"%getattr(taunuContainer.getResult(k)["combineResult"], myResultKey)
            outtxt += "  tan beta=%s, xsecTheor=%f pb, limit(%s)=%s, passed=%d\n"%(k, theory, myResultKey, combineResult, taunuContainer.getPassedStatus(k, myResultKey))
    
    # Find limits
    outtxt += "\nAllowed tan beta ranges (%s) for m=%s (linear interpolation used)\n"%(scen, m)
    for myResultKey in resultKeys:
        myLowTanBetaLimit = 1.0
        myHighTanBetaLimit = 75
        myPreviousStatus = None
        for i in range(0, len(myTanBetaKeys)):
            if not taunuContainer.getFailedStatus(myTanBetaKeys[i]):
                myCurrentStatus = taunuContainer.getPassedStatus(myTanBetaKeys[i], myResultKey)
                if myPreviousStatus != None:
                    if myPreviousStatus != myCurrentStatus:
                        # Cross-over point, check direction
                        myTbvalue = linearCrossOverOfTanBeta(taunuContainer, myTanBetaKeys[i-1], myTanBetaKeys[i], myResultKey)
                        if not myPreviousStatus:
                            myLowTanBetaLimit = myTbvalue
                        else:
                            myHighTanBetaLimit = myTbvalue
                myPreviousStatus = myCurrentStatus
        outtxt +=  "  key='%s' allowed range: %.2f - %.2f\n"%(myResultKey, myLowTanBetaLimit, myHighTanBetaLimit)
    
    print outtxt
    f = open(_resultFilename, "a")
    f.write(outtxt)
    f.close()

if __name__ == "__main__":
    def updateStyle(g, scen):
        g.SetMarkerSize(1.0)
        if scen == "mhmaxup":
            g.SetMarkerStyle(20)
        elif scen == "mhmodm":
            g.SetMarkerStyle(23)
        elif scen == "mhmodp":
            g.SetMarkerStyle(22)
        elif scen == "lightstau":
            g.SetMarkerStyle(25)
        elif scen == "lightstop":
            g.SetMarkerStyle(27)
        elif scen == "tauphobic":
            g.SetMarkerStyle(28)

    def scenToLabel(scen):
        if scen == "mhmaxup":
            return "Updated m_{h}^{max}"
        elif scen == "mhmodm":
            return "m_{h}^{mod+}"
        elif scen == "mhmodp":
            return "m_{h}^{mod-}"
        elif scen == "lightstau":
            return "Light stau"
        elif scen == "lightstop":
            return "Light stop"
        elif scen == "tauphobic":
            return "#tau-phobic"
  
    style = tdrstyle.TDRStyle()
  
    # MSSM scenario settings
    myScenarios = ["mhmaxup", "mhmodm", "mhmodp", "lightstau", "lightstop", "tauphobic"]
    myScenarios = ["mhmaxup", "mhmodm", "mhmodp"]# "lightstau", "lightstop", "tauphobic"]
    #myScenarios = ["mhmaxup"]
    myMassPoints = ["200", "220", "250", "300", "400", "500", "600"]

    for m in myMassPoints:
        myPlotObjects = []
        myTauNuLegend = {}
        myLegend = {}
        for scen in myScenarios:
            # Read 
            myReader = DatabaseReader(scen, float(m))
            # Obtain graph for taunu
            gTauNu = myReader.getBrGraph("taunu")
            gTauNu.SetMarkerColor(ROOT.kBlue)
            gTauNu.SetLineColor(ROOT.kBlue)
            updateStyle(gTauNu, scen)
            myPlotObjects.append(histograms.HistoGraph(gTauNu, "taunu%s"%scen, drawStyle="PL", legendStyle="lp"))
            myLegend["taunu%s"%scenToLabe(scen)] = "%s, #sigma#timesBr(H^{+}#rightarrow#tau^{+}#nu_{#tau})"%scen
        for scen in myScenarios:
            # Read 
            myReader = DatabaseReader(scen, float(m))
            # Obtain graph for tb
            gTB = myReader.getBrGraph("tb")
            gTB.SetMarkerColor(ROOT.kRed)
            gTB.SetLineColor(ROOT.kRed)
            updateStyle(gTB, scen)
            myPlotObjects.append(histograms.HistoGraph(gTB, "tb%s"%scen, drawStyle="PL", legendStyle="lp"))
            myLegend["tb%s"%scenToLabe(scen)] = "%s, #sigma#timesBr(H^{+}#rightarrowt#bar{b})"%scen
        for scen in myScenarios:
            # Read 
            myReader = DatabaseReader(scen, float(m))
            # Obtain graph for other
            gOther = myReader.getBrGraph("other")
            gOther.SetMarkerColor(ROOT.kGreen+2)
            gOther.SetLineColor(ROOT.kGreen+2)
            updateStyle(gOther, scen)
            myPlotObjects.append(histograms.HistoGraph(gOther, "other%s"%scen, drawStyle="PL", legendStyle="lp"))
            myLegend["other%s"%scenToLabe(scen)] = "%s, #sigma#timesBr(H^{+}#rightarrowother)"%scen
        # Do plot
        plot = plots.PlotBase(myPlotObjects, saveFormats=[".png", ".pdf", ".C"])
        plot.histoMgr.setHistoLegendLabelMany(myLegend)
        x = 0.2
        dy = 0.10
        plot.setLegend(histograms.createLegend(x-0.01, 0.50+dy, x+0.45, 0.80+dy))
        name = "mssmCurvesHpm%s"%m
        plot.createFrame(name, opts={"ymin": 1e-5, "ymax": 20, "xmin": 1, "xmax": 75})
        print plot.getPad()
        plot.getPad().SetLogy(True)
        plot.frame.GetXaxis().SetTitle("tan #beta")
        plot.frame.GetYaxis().SetTitle("#sigma#timesBr (pb)")
        plot.draw()
        plot.save()
        print "Created plot %s"%name
