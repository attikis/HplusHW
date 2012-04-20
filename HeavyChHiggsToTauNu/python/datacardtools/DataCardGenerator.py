#! /usr/bin/env python

import os
import sys

from ROOT import *

import HiggsAnalysis.HeavyChHiggsToTauNu.tools.dataset as dataset
import HiggsAnalysis.HeavyChHiggsToTauNu.tools.histograms as histograms
import HiggsAnalysis.HeavyChHiggsToTauNu.tools.counter as counter
import HiggsAnalysis.HeavyChHiggsToTauNu.tools.tdrstyle as tdrstyle
import HiggsAnalysis.HeavyChHiggsToTauNu.tools.styles as styles
import HiggsAnalysis.HeavyChHiggsToTauNu.tools.plots as plots
import HiggsAnalysis.HeavyChHiggsToTauNu.tools.crosssection as xsect

from HiggsAnalysis.HeavyChHiggsToTauNu.datacardtools.DatacardColumn import DatacardColumn
from HiggsAnalysis.HeavyChHiggsToTauNu.datacardtools.Extractor import *

import HiggsAnalysis.HeavyChHiggsToTauNu.datacardtools.MulticrabPathFinder as PathFinder

import HiggsAnalysis.HeavyChHiggsToTauNu.tools.dataset as dataset

from HiggsAnalysis.HeavyChHiggsToTauNu.tools.aux import sort

# main class for generating the datacards from a given cfg file

class DatacardQCDMethod:
    UNKNOWN = 0
    FACTORISED = 1
    INVERTED = 2

class DataCardGenerator:
    def __init__(self, config, opts):
	self._config = config
	self._opts = opts
        self._observation = None
        self._luminosity = -1
        self._columns = []
        self._nuisances = []
        self._QCDmethod = DatacardQCDMethod.UNKNOWN
       
        # Override options from command line and determine QCD measurement method
        self.overrideConfigOptionsFromCommandLine()
        
        # Check that all necessary parameters have been specified in config file
        self.checkCfgFile()
       
        # Create columns (dataset groups)
        self.createDatacardColumns()

        # Create extractors for nuisances (data miners for nuisances)
        self.createExtractors()

        for c in self._columns:
            print c._label, c.getRateValue(self._luminosity)
        print "done."
        sys.exit()
	#if (opts.debugConfig):
        #    config.DataGroups.Print()
        #    config.Nuisances.Print()

	#self.reportUnusedNuisances()

    def overrideConfigOptionsFromCommandLine(self):
        # Obtain QCD measurement method
        if self._config.QCDMeasurementMethod == None:
            self._QCDmethod = DatacardQCDMethod.UNKNOWN
        elif self._config.QCDMeasurementMethod == "QCD factorised":
            self._QCDmethod = DatacardQCDMethod.FACTORISED
        elif self._config.QCDMeasurementMethod == "QCD inverted":
            self._QCDmethod = DatacardQCDMethod.INVERTED
        else:
            self._QCDmethod = DatacardQCDMethod.UNKNOWN
        if self._opts.useQCDfactorised:
            self._QCDmethod = DatacardQCDMethod.FACTORISED
        if self._opts.useQCDinverted:
            self._QCDmethod = DatacardQCDMethod.INVERTED

    def checkCfgFile(self):
        mymsg = ""
        if self._config.DataCardName == None:
            mymsg += "- missing field 'DataCardName' (string, describes the name of the datacard)\n"
        if self._config.Path == None:
            mymsg += "- missing field 'Path' (string, path to directory containing all multicrab directories to be used for datacards)\n"
        elif not os.path.exists(self._config.Path):
            mymsg += "- 'Path' points to directory that does not exist!\n"
        if self._config.MassPoints == None:
            mymsg += "- missing field 'MassPoints' (list of integers, mass points for which datacard is generated)!\n"
        elif len(self._config.MassPoints) == 0:
            mymsg += "- field 'MassPoints' needs to have at least one entry! (list of integers, mass points for which datacard is generated)\n"
        if self._config.SignalAnalysis == None:
            mymsg += "- missing field 'SignalAnalysis' (string, name of EDFilter/EDAnalyzer process that produced the root files for signal analysis)\n"
        if self._QCDmethod == DatacardQCDMethod.FACTORISED and self._config.QCDFactorisedAnalysis == None:
            mymsg += "- missing field 'QCDFactorisedAnalysis' (string, name of EDFilter/EDAnalyzer process that produced the root files for QCD measurement factorised)\n"
        if self._QCDmethod == DatacardQCDMethod.INVERTED and self._config.QCDInvertedAnalysis == None:
            mymsg += "- missing field 'QCDInvertedAnalysis' (string, name of EDFilter/EDAnalyzer process that produced the root files for QCD measurement inverted)\n"
        if self._QCDmethod == DatacardQCDMethod.UNKNOWN:
            mymsg += "- missing field 'QCDMeasurementMethod' (string, name of QCD measurement method, options: 'QCD factorised' or 'QCD inverted')\n"
        if self._config.SignalRateCounter == None:
            mymsg += "- missing field 'SignalRateCounter' (string, label of counter to be used for rate)\n"
        if self._config.FakeRateCounter == None:
            mymsg += "- missing field 'FakeRateCounter' (string, label of counter to be used for rate)\n"
        if self._config.SignalShapeHisto == None:
            mymsg += "- missing field 'SignalShapeHisto' (string, name of histogram for the shape)\n"
        if self._config.FakeShapeHisto == None:
            mymsg += "- missing field 'FakeShapeHisto' (string, name of histogram for the shape)\n"
        if self._config.ShapeHistogramsDimensions == None:
            mymsg += "- missing field 'ShapeHistogramsDimensions' (list of number of bins, minimum, and maximum)\n"
        elif len(self._config.ShapeHistogramsDimensions) != 3:
            mymsg += "- field 'ShapeHistogramsDimensions' has to contain a list of three parameters (number of bins, minimum, and maximum)\n"
        if self._config.Observation == None:
            mymsg += "- missing field 'Observation' (ObservationInput object)\n"
        if self._config.DataGroups == None:
            mymsg += "- missing field 'DataGroups' (list of DataGroup objects)\n"
        elif len(self._config.DataGroups) == 0:
            mymsg += "- need to specify at least one DataGroup to field 'DataGroups' (list of DataGroup objects)\n"
        if self._config.Nuisances == None:
            mymsg += "- missing field 'Nuisances' (list of Nuisance objects)\n"
        elif len(self._config.Nuisances) == 0:
            mymsg += "- need to specify at least one Nuisance to field 'Nuisances' (list of Nuisance objects)\n"
        # determine if datacard was ok
        if mymsg != "":
            print "Error in config '"+self._opts.datacard+"'!\n"
            print mymsg
            sys.exit()

    ## Reads datagroup definitions from columns and initialises datasets
    def createDatacardColumns(self):
        # Obtain paths to multicrab directories
        multicrabPaths = PathFinder.MulticrabPathFinder(self._config.Path)
        mySignalPath = multicrabPaths.getSignalPath()
        if not os.path.exists(mySignalPath):
            print "Path for signal analysis ('"+mySignalPath+"') does not exist!"
            sys.exit()
        myEmbeddingPath = multicrabPaths.getEWKPath()
        if not os.path.exists(myEmbeddingPath):
            print "Path for embedding analysis ('"+myEmbeddingPath+"') does not exist!"
            sys.exit()
        myQCDPath = ""
        myQCDCounters = ""
        if self._QCDmethod == DatacardQCDMethod.FACTORISED:
            myQCDPath = multicrabPaths.getQCDFactorisedPath()
            myQCDCounters = self._config.QCDFactorisedAnalysis+"Counters"
        elif self._QCDmethod == DatacardQCDMethod.INVERTED:
            myQCDPath = multicrabPaths.getQCDInvertedPath()
            myQCDCounters = self._config.QCDInvertedAnalysis+"Counters"
        if not os.path.exists(myQCDPath):
            print "Path for QCD measurement ('"+myQCDPath+"') does not exist!"
            sys.exit()
        # Make merges (a unique merge for each data group; used to access counters and histograms)
        for dg in self._config.DataGroups:
            print "Making merged dataset for data group: \033[1;37m"+dg.label+"\033[0;0m"
            myDsetMgr = 0
            mMergedName = ""
            myMergedNameForQCDMCEWK = ""
            if dg.datasetType != "None":
                if dg.datasetType == "Signal":
                    myDsetMgr = dataset.getDatasetsFromMulticrabCfg(cfgfile=mySignalPath+"/multicrab.cfg", counters=self._config.SignalAnalysis+"Counters")
                elif dg.datasetType == "Embedding":
                    myDsetMgr = dataset.getDatasetsFromMulticrabCfg(cfgfile=myEmbeddingPath+"/multicrab.cfg", counters=self._config.SignalAnalysis+"Counters")
                elif dg.datasetType == "QCD factorised" or dg.datasetType == "QCD inverted":
                    myDsetMgr = dataset.getDatasetsFromMulticrabCfg(cfgfile=myQCDPath+"/multicrab.cfg", counters=myQCDCounters)
                # update normalisation info
                #myDsetMgr.updateNAllEventsToPUWeighted() // FIXME enable as soon as new full multicrab dirs exist
                myDsetMgr.loadLuminosities()
                # find dataset names
                allDatasetNames = myDsetMgr.getAllDatasetNames()
                myFoundNames = self.findDatasetNames(dg.label, allDatasetNames, dg.datasetDefinitions)
                # make merged set
                if self._opts.debugConfig:
                    print "Adding datasets to data group '"+dg.label+"':"
                    for n in myFoundNames:
                        print "  "+n
                myMergedName = "dset_"+dg.label.replace(" ","_")
                myDsetMgr.merge(myMergedName, myFoundNames)
                # find datasets and make merged set for QCD MC EWK
                if dg.datasetType == "QCD factorised":
                    myFoundNames = self.findDatasetNames(dg.label, allDatasetNames, dg.MCEWKDatasetDefinitions)
                    # make merged set
                    if self._opts.debugConfig:
                        print "Adding MC EWK datasets to QCD:"
                        for n in myFoundNames:
                            print "  "+n
                    myMergedNameForQCDMCEWK = "dset_"+dg.label.replace(" ","_")+"_MCEWK"
                    myDsetMgr.merge(myMergedNameForQCDMCEWK, myFoundNames)
            # Construct dataset column object
            myColumn = DatacardColumn(label=dg.label,
                                      landsProcess=dg.landsProcess,
                                      enabledForMassPoints = dg.validMassPoints,
                                      datasetType = dg.datasetType,
                                      rateCounter = dg.rateCounter,
                                      nuisances = dg.nuisances,
                                      datasetMgr = myDsetMgr,
                                      datasetMgrColumn = myMergedName,
                                      datasetMgrColumnForQCDMCEWK = myMergedNameForQCDMCEWK, 
                                      additionalNormalisationFactor = dg.additionalNormalisation,
                                      dirPrefix = dg.dirPrefix,
                                      shapeHisto = dg.shapeHisto)
            self._columns.append(myColumn)
            if self._opts.debugConfig:
                myColumn.printDebug()
        # Make datacard column object for observation
        myDsetMgr = dataset.getDatasetsFromMulticrabCfg(cfgfile=mySignalPath+"/multicrab.cfg", counters=self._config.SignalAnalysis+"Counters")
        # update normalisation info
        #myDsetMgr.updateNAllEventsToPUWeighted() // FIXME enable as soon as new full multicrab dirs exist
        myDsetMgr.loadLuminosities()
        allDatasetNames = myDsetMgr.getAllDatasetNames()
        myFoundNames = self.findDatasetNames("Observation", allDatasetNames, self._config.Observation.datasetDefinitions)
        if self._opts.debugConfig:
            print "Adding datasets to data group 'Observation':"
            for n in myFoundNames:
                print "  "+n
        myObservationName = "dset_observation"
        myDsetMgr.merge(myObservationName, myFoundNames)
        self._observation = DatacardColumn(label = "Observation",
                                           enabledForMassPoints = self._config.MassPoints,
                                           datasetType = "Observation",
                                           rateCounter = self._config.Observation.rateCounter,
                                           datasetMgr = myDsetMgr,
                                           datasetMgrColumn = myObservationName,
                                           dirPrefix = self._config.Observation.dirPrefix,
                                           shapeHisto = self._config.Observation.shapeHisto)
        if self._opts.debugConfig:
            self._observation.printDebug()
        # Obtain luminosity from observation
        self._luminosity = myDsetMgr.getDataset(myObservationName).getLuminosity()
        print "Luminosity is set to \033[1;37m%f 1/pb\033[0;0m"%self._luminosity # FIXME: should this be set to all the other datasets?
        print "Data groups converted to datacard columns"

    ## Helper function for finding datasets
    def findDatasetNames(self, label, allNames, searchNames):
        myResult = []
        for dset in searchNames:
            myFoundStatus = False
            for dsetfull in allNames:
                if dset in dsetfull:
                    myResult.append(dsetfull)
                    myFoundStatus = True
            if not myFoundStatus:
                print "Error in dataset group '"+label+"': cannot find datasetDefinition '"+dset+"'!"
                print "Options are:"
                for dsetfull in allNames:
                    print "  "+dsetfull
                sys.exit()
        return myResult

    ## Creates extractors for nuisances
    def createExtractors(self):
        for n in self._config.Nuisances:
            myMode = ExtractorMode.NUISANCE
            if n.function == "Constant":
                if n.upperValue > 0:
                    myMode = ExtractorMode.ASYMMETRICNUISANCE
                self._nuisances.append(ConstantExtractor(exid = n.id,
                                                         constantValue = n.value,
                                                         constantUpperValue = n.upperValue,
                                                         distribution = n.distr,
                                                         description = n.label,
                                                         mode = myMode))
            elif n.function == "Counter":
                self._nuisances.append(CounterExtractor(exid = n.id,
                                                        counterItem = n.counter,
                                                        distribution = n.distr,
                                                        description = n.label,
                                                        mode = myMode))
            elif n.function == "maxCounter":
                print "fixme"
            elif n.function == "Shape":
                print "fixme"
            elif n.function == "ScaleFactor":
                print "fixme"
            elif n.function == "Ratio":
                print "fixme"
            elif n.function == "QCDFactorised":
                print "fixme"
            elif n.function == "QCDInverted":
                print "fixme"
            else:
                print "Error in nuisance with id='"+n.id+"': unknown or missing field function '"+n.function+"' (string)!"
                print "Options are: 'Constant', 'Counter', 'maxCounter', 'Shape', 'ScaleFactor', 'Ratio', 'QCDFactorised'"
                sys.exit()

# FIXME legacy code beyond this point

    def reportUnusedNuisances(self):
	usedNuisances = []
        for nuisance in self._config.Nuisances.nuisances.keys():
	    for datagroup in self._config.DataGroups.datagroups.keys():
		for usedNuisance in self._config.DataGroups.get(datagroup).nuisances:
		    if usedNuisance == nuisance:
			usedNuisances.append(nuisance)
	usedNuisances = self.rmDuplicates(usedNuisances)
	unUsedNuisances = []
	for nuisance in self._config.Nuisances.nuisances.keys():
	    if nuisance not in usedNuisances:
		#print "UNUSED NUISANCE"
		#config.Nuisances.get(nuisance).Print
		unUsedNuisances.append(nuisance)
	print "Unused nuisances",sort(unUsedNuisances)

    def rmDuplicates(self,list):
	retlist = []
	for element in list:
	    if element not in retlist:
		retlist.append(element)
	return retlist

    #def generate(self):
	#signalDir = []
	#signalDir.append(self._config.multicrabPaths.getSignalPath())
	#datasets = dataset.getDatasetsFromMulticrabDirs(signalDir,counters=self._config.CounterDir)
	#datasets.loadLuminosities()
	#plots.mergeRenameReorderForDataMC(datasets)
	#luminosity = datasets.getDataset("Data").getLuminosity()
        #print "Luminosity = ",luminosity

