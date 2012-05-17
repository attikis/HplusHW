## \package QCDfactorised
# Classes for extracting and calculating multijet background with factorised approach

from HiggsAnalysis.HeavyChHiggsToTauNu.datacardtools.Extractor import ExtractorMode,ExtractorBase
from HiggsAnalysis.HeavyChHiggsToTauNu.datacardtools.DatacardColumn import ExtractorResult,DatacardColumn
from HiggsAnalysis.HeavyChHiggsToTauNu.datacardtools.MulticrabPathFinder import MulticrabDirectoryDataType
from HiggsAnalysis.HeavyChHiggsToTauNu.tools.ShellStyles import *
from HiggsAnalysis.HeavyChHiggsToTauNu.tools.dataset import Count
from HiggsAnalysis.HeavyChHiggsToTauNu.datacardtools.ShapeHistoModifier import *
from math import pow,sqrt
import sys
import ROOT

## Extracts data-MC EWK counts from a given point in the analysis
class QCDEventCount():
    def __init__(self,
                 histoPrefix,
                 histoName,
                 dsetMgr,
                 dsetMgrDataColumn,
                 dsetMgrMCEWKColumn,
                 luminosity,
                 assumedMCEWKSystUncertainty):
        self._histoname = histoName
        self._assumedMCEWKSystUncertainty = assumedMCEWKSystUncertainty
        # Obtain histograms
        datasetRootHistoData = dsetMgr.getDataset(dsetMgrDataColumn).getDatasetRootHisto(histoPrefix+"/"+histoName)
        datasetRootHistoMCEWK = dsetMgr.getDataset(dsetMgrMCEWKColumn).getDatasetRootHisto(histoPrefix+"/"+histoName)
        datasetRootHistoMCEWK.normalizeToLuminosity(luminosity)
        self._hData = datasetRootHistoData.getHistogram()
        self._hMC = datasetRootHistoMCEWK.getHistogram()

    def clean(self):
        self._hData.IsA().Destructor(self._hData)
        self._hMC.IsA().Destructor(self._hMC)

    def is1D(self):
        return isinstance(self._hData,ROOT.TH1F) or isinstance(self._hData,ROOT.TH1D)

    def is2D(self):
        return isinstance(self._hData,ROOT.TH2F) or isinstance(self._hData,ROOT.TH2D)

    def is3D(self):
        return isinstance(self._hData,ROOT.TH3F) or isinstance(self._hData,ROOT.TH3D)

    def getNbinsX(self):
        return self._hData.GetNbinsX()

    def getNbinsY(self):
        return self._hData.GetNbinsY()

    def getNbinsZ(self):
        return self._hData.GetNbinsZ()

    def getClonedHisto(self, name):
        return self._hData.Clone(name)

    ## Getter for result of 1-dimensional factorisation
    # Returns Count object for data-MC
    def getCount1D(self,idx):
        if not (isinstance(self._hData,ROOT.TH1F) or isinstance(self._hData,ROOT.TH1D)):
            Exception(ErrorStyle()+"QCD factorised / factorisation data has more than 1 dimension!"+NormalStyle())
        # Obtain value
        myData = self._hData.GetBinContent(idx)
        myMC = self._hMC.GetBinContent(idx)
        myResult = myData - myMC
        # Obtain uncertainty
        myResultError = self.getTotalError(idx)
        # Check negative result
        if myResult < 0:
            print WarningStyle()+"Warning: QCD factorised: negative count (setting to zero) for %s bin %d (data=%f, MC=%f, result=%f"%(self._histoname, idx, myData, myMC, myResult) +NormalStyle()
            myResult = 0.0
            #myResultError = 0.0
        # Return result 
        return Count(myResult,myResultError)

    def getDataError1D(self,idx):
        if not (isinstance(self._hData,ROOT.TH1F) or isinstance(self._hData,ROOT.TH1D)):
            Exception(ErrorStyle()+"QCD factorised / factorisation data has more than 1 dimension!"+NormalStyle())
        return self._hData.GetBinError(idx)

    def getMCStatError1D(self,idx):
        if not (isinstance(self._hData,ROOT.TH1F) or isinstance(self._hData,ROOT.TH1D)):
            Exception(ErrorStyle()+"QCD factorised / factorisation data has more than 1 dimension!"+NormalStyle())
        return self._hMC.GetBinError(idx)

    def getMCSystError1D(self,idx):
        if not (isinstance(self._hData,ROOT.TH1F) or isinstance(self._hData,ROOT.TH1D)):
            Exception(ErrorStyle()+"QCD factorised / factorisation data has more than 1 dimension!"+NormalStyle())
        return self._hMC.GetBinError(idx) * self._assumedMCEWKSystUncertainty

    def getTotalError(self,idx):
        if not (isinstance(self._hData,ROOT.TH1F) or isinstance(self._hData,ROOT.TH1D)):
            Exception(ErrorStyle()+"QCD factorised / factorisation data has more than 1 dimension!"+NormalStyle())
        myDataError = self.getDataError1D(idx)
        myMCStatError = self.getMCStatError1D(idx)
        myMCSystError = self.getMCSystError1D(idx)
        myResultError = sqrt(pow(myDataError,2) + pow(myMCStatError,2) + pow(myMCSystError,2))
        return myResultError

    ## Getter for purity of 1-dimensional factorisation
    # Returns Count object for (data-MC)/data
    def getPurity1D(self,idx):
        if not (isinstance(self._hData,ROOT.TH1F) or isinstance(self._hData,ROOT.TH1D)):
            Exception(ErrorStyle()+"QCD factorised / factorisation data has more than 1 dimension!"+NormalStyle())
        myData = self._hData.GetBinContent(idx)
        myDataError = self._hData.GetBinError(idx)
        myQCD = self.getCount1D(idx)
        if myData > 0:
          myResult = myQCD.value() / myData
          myResultError = myResult*sqrt(pow(myQCD.uncertainty()/myQCD.value(),2)+pow(myDataError/myData,2))
        else:
          myResult = 0.0
          myResultError = 0.0
        return Count(myResult,myResultError)

    ## Returns a purity histogram
    def getPurityHistogram(self):
        h = self._hData.Clone("purity_"+self._histoname.replace("/","_"))
        h.Reset()
        h.SetYTitle("Purity")
        if isinstance(self._hData,ROOT.TH1F) or isinstance(self._hData,ROOT.TH1D):
            for i in range(1,h.GetNbinsX()+1):
                myPurity = self.getPurity1D(i)
                h.SetBinContent(i, myPurity.value())
                h.SetBinError(i, myPurity.uncertainty())
                if myPurity.value() > 0.0 and myPurity.value() < 0.5:
                    print WarningStyle()+"Warning: QCD factorised: Purity in %s bin %d is low (%f +- %f)!"%(self._histoname,i,myPurity.value(),myPurity.uncertainty())+NormalStyle()
        else:
            print WarningStyle()+"Warning: QCD factorised: Purity histogram generation not supported for histogram type ", h, NormalStyle()
        return h

## Helper class for calculating the result from three points of counting in the analysis
class QCDfactorisedCalculator():
    def __init__(self, basicCounts, leg1Counts, leg2Counts):
        self._NQCD = 0.0
        self._dataUncertainty = 0.0
        self._MCStatUncertainty = 0.0
        self._MCSystUncertainty = 0.0

        self._basicCount = basicCounts
        self._leg1Counts = leg1Counts
        self._leg2Counts = leg2Counts

        if (basicCounts.is1D()):
            self._count1D(basicCounts, leg1Counts, leg2Counts)
        else:
            print WarningStyle()+"Warning: QCD factorised: NQCD calculation not supported for more than 1 dimensions"+NormalStyle()

    def getNQCD(self):
        return self._NQCD

    def getDataUncertainty(self):
        return self._dataUncertainty / self._NQCD

    def getMCStatUncertainty(self):
        return self._MCStatUncertainty / self._NQCD

    def getMCSystUncertainty(self):
        return self._MCSystUncertainty / self._NQCD

    def getStatUncertainty(self):
        return sqrt(pow(self._dataUncertainty,2)+pow(self._MCStatUncertainty,2)) / self._NQCD

    def getSystUncertainty(self):
        return self.getMCSystUncertainty()

    def getTotalUncertainty(self):
        return sqrt(pow(self._dataUncertainty,2)+pow(self._MCStatUncertainty,2)+pow(self._getMCSystUncertainty,2)) / self._NQCD

    def getLeg1Efficiency1D(self,idx):
        return self._getEfficiency1D(self._leg1Counts, self._basicCount,idx)

    def getLeg2Efficiency1D(self,idx):
        return self._getEfficiency1D(self._leg2Counts, self._basicCount,idx)

    def _getEfficiency1D(self,nominator,denominator,idx):
        myValue = -1.0
        myError = 0.0
        nominatorCount = nominator.getCount1D(idx)
        denominatorCount = denominator.getCount1D(idx)
        #print "1D eff: nom=%f, denom=%f:"%(nominatorCount.value(),denominatorCount.value())
        if denominatorCount.value() > 0:
            myValue = nominatorCount.value() / denominatorCount.value()
            myError = myValue*sqrt(pow(nominatorCount.uncertainty()/nominatorCount.value(),2)+pow(denominatorCount.uncertainty()/denominatorCount.value(),2))
        return Count(myValue,myError)

    def getLeg1EfficiencyHistogram(self):
        return self._createEfficiencyHistogram(self._leg1Counts, self._basicCount, "leg1")

    def getLeg2EfficiencyHistogram(self):
        return self._createEfficiencyHistogram(self._leg2Counts, self._basicCount, "leg2")

    def _createEfficiencyHistogram(self, nominator, denominator, suffix=""):
        # Create histogram
        h = nominator.getClonedHisto("QCDfactEff_"+suffix)
        if nominator.is1D():
            h.SetYTitle("Efficiency")
            for i in range(1, h.GetNbinsX()+1):
                myEfficiency = self._getEfficiency1D(nominator,denominator,i)
                h.SetBinContent(i, myEfficiency.value())
                h.SetBinError(i, myEfficiency.uncertainty())
        else:
            print WarningStyle()+"Warning: QCD:Factorised: Efficiency histogram not yet supported for more than 1 dimensions"+NormalStyle()
        return h

    def _count1D(self, basicCounts, leg1Counts, leg2Counts):
        for i in range (1,basicCounts.getNbinsX()+1):
            myBasicCounts = basicCounts.getCount1D(i).value()
            myLeg1Counts = leg1Counts.getCount1D(i).value()
            myLeg2Counts = leg2Counts.getCount1D(i).value()
            myCount = 0.0
            myDataUncert = 0.0
            myMCStatUncert = 0.0
            myMCSystUncert = 0.0
            # Protect calculation against div by zero
            if (myBasicCounts > 0.0):
                myCount = myLeg1Counts * myLeg2Counts / myBasicCounts
                # Calculate uncertainty as f=a*b  (i.e. ignore basic counts uncertainty since it is the denominator to avoid double counting of uncertainties)
                myDataUncert = pow(myLeg2Counts*leg1Counts.getDataError1D(i)/myBasicCounts,2) + pow(myLeg1Counts*leg2Counts.getDataError1D(i)/myBasicCounts,2)
                myMCStatUncert = pow(myLeg2Counts*leg1Counts.getMCStatError1D(i)/myBasicCounts,2) + pow(myLeg1Counts*leg2Counts.getMCStatError1D(i)/myBasicCounts,2)
                myMCSystUncert = pow(myLeg2Counts*leg1Counts.getMCSystError1D(i)/myBasicCounts,2) + pow(myLeg1Counts*leg2Counts.getMCSystError1D(i)/myBasicCounts,2)
            # Make sum
            self._NQCD += myCount
            self._dataUncertainty += myDataUncert
            self._MCStatUncertainty += myMCStatUncert
            self._MCSystUncertainty += myMCSystUncert
        # Take sqrt of uncertainties (sum contains the variance)
        #print "nqcd=",self._NQCD," +- ", sqrt(self._dataUncertainty), "+- ", sqrt(self._MCStatUncertainty), "+-", sqrt(self._MCSystUncertainty)
        self._dataUncertainty = sqrt(self._dataUncertainty)
        self._MCStatUncertainty = sqrt(self._MCStatUncertainty)
        self._MCSystUncertainty = sqrt(self._MCSystUncertainty)

## class QCDfactorisedColumn
# Inherits from DatacardColumn and extends its functionality to calculate the QCD measurement and its result in one go
# Note that only method one needs to add is 'doDataMining'; other methods are private
class QCDfactorisedColumn(DatacardColumn):
    ## Constructor
    def __init__(self,
                 landsProcess = -999,
                 enabledForMassPoints = [],
                 nuisanceIds = [],
                 datasetMgrColumn = "",
                 datasetMgrColumnForQCDMCEWK = "",
                 additionalNormalisationFactor = 1.0,
                 dirPrefix = "",
                 QCDfactorisedInfo = None,
                 debugMode = False):
        DatacardColumn.__init__(self,
                                label = "QCDfact",
                                landsProcess = landsProcess,
                                enabledForMassPoints = enabledForMassPoints,
                                datasetType = "QCD factorised",
                                nuisanceIds = nuisanceIds,
                                datasetMgrColumn = datasetMgrColumn,
                                datasetMgrColumnForQCDMCEWK = datasetMgrColumnForQCDMCEWK,
                                additionalNormalisationFactor = additionalNormalisationFactor,
                                dirPrefix = dirPrefix)
        # Set source histograms
        self._afterBigboxSource = QCDfactorisedInfo["afterBigboxSource"]
        self._afterMETLegSource = QCDfactorisedInfo["afterMETLegSource"]
        self._afterTauLegSource = QCDfactorisedInfo["afterTauLegSource"]
        self._basicMtHisto = QCDfactorisedInfo["basicMtHisto"]
        self._assumedMCEWKSystUncertainty = QCDfactorisedInfo["assumedMCEWKSystUncertainty"]
        # Other initialisation
        self._infoHistograms = []
        self._debugMode = debugMode

    ## Do data mining and cache results
    def doDataMining(self, config, dsetMgr, luminosity, mainCounterTable, extractors):
        print "...",self._label
        # Make event count objects
        myBigBoxEventCount = QCDEventCount(histoPrefix=self._dirPrefix,
                                           histoName=self._afterBigboxSource,
                                           dsetMgr=dsetMgr,
                                           dsetMgrDataColumn=self._datasetMgrColumn,
                                           dsetMgrMCEWKColumn=self._datasetMgrColumnForQCDMCEWK,
                                           luminosity=luminosity,
                                           assumedMCEWKSystUncertainty=self._assumedMCEWKSystUncertainty)
        myMETLegEventCount = QCDEventCount(histoPrefix=self._dirPrefix,
                                           histoName=self._afterMETLegSource,
                                           dsetMgr=dsetMgr,
                                           dsetMgrDataColumn=self._datasetMgrColumn,
                                           dsetMgrMCEWKColumn=self._datasetMgrColumnForQCDMCEWK,
                                           luminosity=luminosity,
                                           assumedMCEWKSystUncertainty=self._assumedMCEWKSystUncertainty)
        myTauLegEventCount = QCDEventCount(histoPrefix=self._dirPrefix,
                                           histoName=self._afterTauLegSource,
                                           dsetMgr=dsetMgr,
                                           dsetMgrDataColumn=self._datasetMgrColumn,
                                           dsetMgrMCEWKColumn=self._datasetMgrColumnForQCDMCEWK,
                                           luminosity=luminosity,
                                           assumedMCEWKSystUncertainty=self._assumedMCEWKSystUncertainty)
        # Make purity histograms
        self._infoHistograms.append(myBigBoxEventCount.getPurityHistogram())
        self._infoHistograms.append(myMETLegEventCount.getPurityHistogram())
        self._infoHistograms.append(myTauLegEventCount.getPurityHistogram())
        # Calculate result of NQCD
        myQCDCalculator = QCDfactorisedCalculator(myBigBoxEventCount, myMETLegEventCount, myTauLegEventCount)
        # Make efficiency histograms
        self._infoHistograms.append(myQCDCalculator.getLeg1EfficiencyHistogram())
        self._infoHistograms.append(myQCDCalculator.getLeg2EfficiencyHistogram())
        # Make mT shape histogram
        myRateHistograms = []
        myRateHistograms.append(self._createMtShapeHistogram(config, dsetMgr, myQCDCalculator, myBigBoxEventCount, luminosity))
        # Cache result
        self._rateResult = ExtractorResult("rate",
                                           "rate",
                                           myQCDCalculator.getNQCD(),
                                           myRateHistograms)
        # Construct results for nuisances
        for nid in self._nuisanceIds:
            #sys.stdout.write("\r... data mining in progress: Column="+self._label+", obtaining Nuisance="+nid+"...                                              ")
            #sys.stdout.flush()
            myFoundStatus = False
            for e in extractors:
                if e.getId() == nid:
                    myFoundStatus = True
                    myResult = 0.0
                    # Obtain result
                    if e.getQCDmode() == "statistics":
                        myResult = myQCDCalculator.getStatUncertainty()
                    elif e.getQCDmode() == "systematics":
                        myResult = myQCDCalculator.getSystUncertainty()
                    # Obtain histograms
                    myHistograms = []
                    if e.isShapeNuisance():
                        print WarningStyle()+"FIXME: mT plot calculation missing in QCD factorised"+NormalStyle()
                        # FIXME
                        #myHistograms.extend(e.extractHistograms(self, dsetMgr, mainCounterTable, luminosity, self._additionalNormalisationFactor))
                    # Cache result
                    self._nuisanceResults.append(ExtractorResult(e.getId(),
                                                                 e.getMasterId(),
                                                                 myResult,
                                                                 myHistograms))
            if not myFoundStatus:
                print "\n"+ErrorStyle()+"Error (data group ='"+self._label+"'):"+NormalStyle()+" Cannot find nuisance with id '"+nid+"'!"
                sys.exit()
        #print "\nData mining done"

    def _createMtShapeHistogram(self, config, dsetMgr, QCDCalculator, QCDCount, luminosity):
        # Create mT histogram
        myShapeModifier = ShapeHistoModifier(config.ShapeHistogramsDimensions)
        h = myShapeModifier.createEmptyShapeHistogram(self._label)
        # Loop over bins
        if QCDCount.is1D():
            for i in range(1,QCDCount.getNbinsX()+1):
                # Get histograms for bin and normalise MC histograms
                histoName = self._dirPrefix+"/"+self._basicMtHisto+"_bin%d"%(i-1)
                dsetRootHistoMtData = dsetMgr.getDataset(self._datasetMgrColumn).getDatasetRootHisto(histoName)
                hMtData = dsetRootHistoMtData.getHistogram()
                if hMtData == None:
                    raise Exception(ErrorStyle()+"Error:"+NormalStyle()+" Cannot find histogram "+histoName+" for QCD factorised data!")
                dsetRootHistoMtMCEWK = dsetMgr.getDataset(self._datasetMgrColumnForQCDMCEWK).getDatasetRootHisto(histoName)
                dsetRootHistoMtMCEWK.normalizeToLuminosity(luminosity)
                hMtMCEWK = dsetRootHistoMtMCEWK.getHistogram()
                if hMtMCEWK == None:
                    raise Exception(ErrorStyle()+"Error:"+NormalStyle()+" Cannot find histogram "+histoName+" for QCD factorised MC EWK!")
                if self._debugMode:
                    print "  QCDfactorised / mT shape: bin %d, data=%f, MC EWK=%f, QCD=%f"%(i,hMtData.Integral(0,hMtData.GetNbinsX()+1),hMtMCEWK.Integral(0,hMtMCEWK.GetNbinsX()+1),hMtData.Integral(0,hMtData.GetNbinsX()+1)-hMtMCEWK.Integral(0,hMtMCEWK.GetNbinsX()+1))
                # Obtain empty histogram
                hMtBin = myShapeModifier.createEmptyShapeHistogram("QCDFact_MtShape_bin_%d"%i)
                # Add data and subtract MCEWK
                myShapeModifier.addShape(source=hMtData,dest=hMtBin)
                myMessages = []
                myMessages.extend(myShapeModifier.subtractShape(source=hMtMCEWK,dest=hMtBin,purityCheck=True))
                if len(myMessages) > 0:
                    myTotal = hMtBin.Integral(0,hMtBin.GetNbinsX()+1)
                    for m in myMessages:
                        # Filter out only important warnings of inpurity (impact more than one percent to whole bin)
                        if myTotal > 0.0:
                            if m[1] / myTotal > 0.01:
                                print WarningStyle()+"Warning:"+NormalStyle()+" low purity in QCD factorised mT shape for bin %d (impact %f events / total=%f : %s"%(i,m[1],myTotal,m[0])
                myShapeModifier.finaliseShape(dest=hMtBin)
                # Check for negative bins
                for k in range(1,hMtBin.GetNbinsX()+1):
                    if hMtBin.GetBinContent(k) < 0.0:
                        print WarningStyle()+"Warning: QCD factorised"+NormalStyle()+" in mT shape bin %d, histo bin %d is negative (%f / tot:%f), it is set to zero but total normalisation is maintained"%(i,k,hMtBin.GetBinContent(k),hMtBin.Integral())
                        myIntegral = hMtBin.Integral()
                        hMtBin.SetBinContent(k,0.0)
                        if (hMtBin.Integral() > 0.0):
                            hMtBin.Scale(myIntegral / hMtBin.Integral())
                # Multiply by efficiency of leg 2
                myEfficiency = QCDCalculator.getLeg2Efficiency1D(i)
                hMtBin.Scale(myEfficiency.value())
                if self._debugMode:
                    print "  QCDfactorised / mT shape: bin %d, eff=%f, eff*QCD=%f"%(i,myEfficiency.value(),hMtBin.Integral())
                # Add to total mT shape histogram
                myShapeModifier.addShape(source=hMtBin,dest=h)
                # Store mT bin histogram for info
                self._infoHistograms.append(hMtBin)
                # Delete data and MC EWK histograms from memory
                hMtData.IsA().Destructor(hMtData)
                hMtMCEWK.IsA().Destructor(hMtMCEWK)
        elif QCDCount.is2D():
            print "fixme"
        else:
            print WarningStyle()+"Warning: QCD:Factorised: mT histogram not yet supported for more than 1 dimensions"+NormalStyle()
        # Finalise
        myShapeModifier.finaliseShape(dest=h)
        # Normalise total mT histogram to NQCD
        h.Scale(QCDCalculator.getNQCD() / h.Integral(0,h.GetNbinsX()+2))
        return h

    ## Saves information histograms into a histogram
    def saveQCDInfoHistograms(self, outputDir):
        # Open root file for saving
        myRootFilename = outputDir+"/QCDMeasurementFactorisedInfo.root"
        myRootFile = ROOT.TFile.Open(myRootFilename, "RECREATE")
        if myRootFile == None:
            print ErrorStyle()+"Error:"+NormalStyle()+" Cannot open file '"+myRootFilename+"' for output!"
            sys.exit()
        # Loop over info histograms
        for h in self._infoHistograms:
            h.SetDirectory(myRootFile)
        # Close root file
        myRootFile.Write()
        myRootFile.Close()
        # Cleanup (closing the root file destroys the objects assigned to it, do not redestroy the histos in the _infoHistograms list
        self._infoHistograms = []
        print "QCD Measurement factorised info histograms saved to:",myRootFilename

    ## var _infoHistograms
    # Histograms for information and documentation of the QCD measurement

## QCDfactorisedExtractor class
# It is essentially wrapper for QCD mode string
class QCDfactorisedExtractor(ExtractorBase):
    ## Constructor
    def __init__(self, QCDmode, mode, exid = "", distribution = "lnN", description = ""):
        ExtractorBase.__init__(self, mode, exid, distribution, description)
        self._QCDmode = QCDmode

    ## Method for extracking information
    # Everything is processed 
    def extractResult(self, datasetColumn, datasetColumnForMCEWK, dsetMgr, luminosity, additionalNormalisation = 1.0):
        return 0.0

    ## Virtual method for extracting histograms
    # Returns the transverse mass plot
    def extractHistograms(self, datasetColumn, dsetMgr, mainCounterTable, luminosity, additionalNormalisation = 1.0):
        return []

    def getQCDmode(self):
        return self._QCDmode

    ## var _QCDmode
    # keyword for returning the stat, syst, or shapeStat results