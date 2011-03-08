#!/usr/bin/env python

###########################################################################
#
# This script is only intended as an example, please do NOT modify it.
# For example, start from scratch and look here for help, or make a
# copy of it and modify the copy (including removing all unnecessary
# code).
#
###########################################################################

import ROOT
import HiggsAnalysis.HeavyChHiggsToTauNu.tools.dataset as dataset
import HiggsAnalysis.HeavyChHiggsToTauNu.tools.histograms as histograms
import HiggsAnalysis.HeavyChHiggsToTauNu.tools.plots as plots
import HiggsAnalysis.HeavyChHiggsToTauNu.tools.tdrstyle as tdrstyle
import HiggsAnalysis.HeavyChHiggsToTauNu.tools.styles as styles

# Go to batch mode, comment if interactive mode is wanted (see on the
# bottom of the script how to make it to wait input from user)
ROOT.gROOT.SetBatch(True)

# Apply TDR style
style = tdrstyle.TDRStyle()


# Construct datasets as stated in the multicrab.cfg of the execution
# directory. The returned object is of type DatasetManager.
datasets = dataset.getDatasetsFromMulticrabCfg(counters = "signalAnalysisTauSelectionHPSTightTauBasedCounters")

# Construct datasets from the given list of CRAB task directories
#datasets = dataset.getDatasetsFromCrabDirs(["QCD_Pt120to170"])
#datasets = dataset.getDatasetsFromCrabDirs(["TTbar_Htaunu_M80"])

# Construct datasets from a given list of (name, pathToRooTFile) pairs
#datasets = dataset.getDatasetsFromRootFiles([("QCD_Pt120to170", "QCD_Pt120to170/res/histograms-QCD_Pt120to170.root")])

datasets.remove(["WJets_TuneD6T_Winter10", "TTJets_TuneD6T_Winter10","TTToHplusBWB_M120_Winter10"])

# Load dataset luminosities from a 'lumi.json' file
datasets.loadLuminosities()

# Merge:
#  - all data datasets to 'Data'
#  - all QCD datasets to 'QCD'
#  - all single top datasets to 'SingleTop'
# Rename the physical dataset names to logical (essentially drop the Tune and Winter10)
# Reorder to the 'standard' order, all 'nonstandard' are left to the end
plots.mergeRenameReorderForDataMC(datasets)

# Override the data luminosity (should not be used except for testing)
#datasets.getDataset("Data").setLuminosity(35)

# Create the plot, latter argument is the path to the histogram in the ROOT files
h = plots.DataMCPlot(datasets, "signalAnalysisTauSelectionHPSTightTauBased/TauEmbeddingAnalysis_afterTauId_selectedTauPt")

h.histoMgr.forEachHisto(lambda h: h.getRootHisto().Rebin(5))

# Stack MC histograms
h.stackMCHistograms()
#tauPt.stackMCHistograms(stackSignal=True) # Stack also the signal datasets?

h.addMCUncertainty()

# Create canvas and frame for only the distributions
#h.createFrame("taupt_new", ymin=0.1, ymax=1e4)
h.createFrame("tauPtEmbedding_afterTauId", ymin=0.01, ymaxfactor=2)
h.frame.GetXaxis().SetTitle("p_{T}^{#tau jet} (GeV/c)")
h.frame.GetYaxis().SetTitle("Events / 5 GeV/c")

# Create legend
h.setLegend(histograms.createLegend())

#cf = histograms.CanvasFrame(tauPts, "taupt")
#cf = histograms.CanvasFrame(tauPts, "taupt", ymin=10, ymax=1e9) # for logy
ROOT.gPad.SetLogy(True)

# Draw the histograms and the legend
h.draw()

# Add the necessary pieces of text
histograms.addCmsPreliminaryText()
histograms.addEnergyText()
h.addLuminosityText()

# Save to .png, .eps and .C file
h.save()

#  counters = "qcdMeasurementMethod2Part1Counters/weighted"
# Same, but create two pads, one for the distributions and another for
# the data/MC
h = plots.DataMCPlot(datasets, "signalAnalysisTauSelectionHPSTightTauBased/TauEmbeddingAnalysis_begin_selectedTauPt")
h.stackMCHistograms()
h.addMCUncertainty()
h.createFrameFraction("tauPtEmbedding_afterTauId2",)
h.frame.GetXaxis().SetTitle("p_{T}^{#tau jet} (GeV/c)")
h.frame.GetYaxis().SetTitle("Events / 5 GeV/c")
h.setLegend(histograms.createLegend())
h.draw()
histograms.addCmsPreliminaryText()
histograms.addEnergyText()
h.addLuminosityText()
h.save()

# Script execution can be paused like this, it will continue after
# user has given some input (which must include enter)
#raw_input("Hit enter to continue")
