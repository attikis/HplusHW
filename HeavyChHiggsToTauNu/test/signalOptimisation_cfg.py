import FWCore.ParameterSet.Config as cms
from HiggsAnalysis.HeavyChHiggsToTauNu.HChOptions import getOptions
from HiggsAnalysis.HeavyChHiggsToTauNu.HChDataVersion import DataVersion

dataVersion = "35X"
#dataVersion = "35Xredigi"
#dataVersion = "36X"
#dataVersion = "36Xspring10"
#dataVersion = "37X"
#dataVersion = "38X"
#dataVersion = "data" # this is for collision data 

options = getOptions()
if options.dataVersion != "":
    dataVersion = options.dataVersion

print "Assuming data is ", dataVersion
dataVersion = DataVersion(dataVersion) # convert string to object

process = cms.Process("HChSignalOptimisation")

process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(-1) )
#process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(20000) )
#process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(100) )


process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
process.GlobalTag.globaltag = cms.string(dataVersion.getGlobalTag())

process.source = cms.Source('PoolSource',
    duplicateCheckMode = cms.untracked.string('noDuplicateCheck'),
    fileNames = cms.untracked.vstring(
        # For testing in lxplus
        dataVersion.getAnalysisDefaultFileCastor()
        # For testing in jade
        #dataVersion.getAnalysisDefaultFileMadhatter()
        #dataVersion.getAnalysisDefaultFileMadhatterDcap()
  )
)
if options.doPat != 0:
    process.source.fileNames = cms.untracked.vstring(dataVersion.getPatDefaultFileMadhatter())


################################################################################

process.load("HiggsAnalysis.HeavyChHiggsToTauNu.HChCommon_cfi")
process.MessageLogger.categories.append("EventCounts")
process.MessageLogger.cerr.FwkReport.reportEvery = 1000

# Uncomment the following in order to print the counters at the end of
# the job (note that if many other modules are being run in the same
# job, their INFO messages are printed too)
#process.MessageLogger.cerr.threshold = cms.untracked.string("INFO")
process.TFileService.fileName = "signalOptimisation.root"

from HiggsAnalysis.HeavyChHiggsToTauNu.HChDataSelection import addDataSelection
from HiggsAnalysis.HeavyChHiggsToTauNu.HChPatTuple import *
process.patSequence = cms.Sequence()
if options.doPat != 0:
    print "Running PAT on the fly"

    process.collisionDataSelection = cms.Sequence()
    if dataVersion.isData():
        trigger = ""
        if dataVersion.isRun2010A():
            trigger = "HLT_SingleLooseIsoTau20"
        elif dataVersion.isRun2010B():
            trigger = "HLT_SingleIsoTau20_Trk15_MET20"
        else:
            raise Exception("Unsupported data version!")

        process.collisionDataSelection = addDataSelection(process, dataVersion, trigger)

    process.patSequence = cms.Sequence(
        process.collisionDataSelection *
        addPat(process, dataVersion)
    )


process.genRunInfo = cms.EDAnalyzer("HPlusGenRunInfoAnalyzer",
    src = cms.untracked.InputTag("generator")
)
process.configInfo = cms.EDAnalyzer("HPlusConfigInfoAnalyzer")
if options.crossSection >= 0.:
    process.configInfo.crossSection = cms.untracked.double(options.crossSection)
    print "Dataset cross section has been set to %g pb" % options.crossSection
if options.luminosity >= 0:
    process.configInfo.luminosity = cms.untracked.double(options.luminosity)
    print "Dataset integrated luminosity has been set to %g pb^-1" % options.luminosity
process.infoPath = cms.Path(
    process.genRunInfo +
    process.configInfo
)

# Signal analysis module
import HiggsAnalysis.HeavyChHiggsToTauNu.HChSignalOptimisationParameters_cff as param
process.signalOptimisation = cms.EDProducer("HPlusSignalOptimisationProducer",
    trigger = param.trigger,
#    TriggerMETEmulation = param.TriggerMETEmulation,
    tauSelection = param.tauSelection,
    useFactorizedTauID = cms.untracked.bool(False), #param.useFactorizedTauID,
    jetSelection = param.jetSelection,
    MET = param.MET,
    bTagging = param.bTagging,
    transverseMassCut = param.transverseMassCut,
    EvtTopology = param.EvtTopology,
    GlobalMuonVeto = param.GlobalMuonVeto,
    GlobalElectronVeto = param.GlobalElectronVeto
)
print "TauSelection algorithm:", process.signalAnalysis.tauSelection.selection
print "TauSelection src:", process.signalAnalysis.tauSelection.src
print "TauSelection factorization used:", process.signalAnalysis.useFactorizedTauID

#if dataVersion.isMC() and dataVersion.is38X():
#    process.trigger.trigger = "HLT_SingleIsoTau20_Trk5_MET20"

# Counter analyzer (in order to produce compatible root file with the
# python approach)
process.signalOptimisationCounters = cms.EDAnalyzer("HPlusEventCountAnalyzer",
    counterNames = cms.untracked.InputTag("signalOptimisation", "counterNames"),
    counterInstances = cms.untracked.InputTag("signalOptimisation", "counterInstances"),
    verbose = cms.untracked.bool(True)
)
process.signalOptimisationPath = cms.Path(
    process.patSequence * # supposed to be empty, unless "doPat=1" command line argument is given
    process.signalOptimisation *
    process.signalOptimisationCounters
)

# An example how to create an array of analyzers to do the same
# analysis by varying a single parameter. It is significantly more
# efficienct to run many analyzers in single crab job than to run many
# crab jobs with a single analyzer.
#
#
# def setTauPt(m, val):
#     m.tauSelection.ptCut = val
# from HiggsAnalysis.HeavyChHiggsToTauNu.HChTools import addAnalysisArray
# addAnalysisArray(process, "signalOptimisationTauPt", process.signalOptimisation, setTauPt,
#                  [10, 20, 30, 40, 50])


# Print tau discriminators from one tau from one event
process.tauDiscriminatorPrint = cms.EDAnalyzer("HPlusTauDiscriminatorPrintAnalyzer",
    src = process.signalOptimisation.tauSelection.src
)
#process.tauDiscriminatorPrintPath = cms.Path(
#    process.patSequence *
#    process.tauDiscriminatorPrint
#)

################################################################################
process.out = cms.OutputModule("PoolOutputModule",
    fileName = cms.untracked.string('output.root'),
    outputCommands = cms.untracked.vstring(
        "keep *_*_*_HChSignalOptimisation",
        "drop *_*_counterNames_*",
        "drop *_*_counterInstances_*"
#	"drop *",
#        "keep edmMergeableCounter_*_*_*"
    )
)
# Uncomment the following line to get also the event output (can be
# useful for debugging purposes)
#process.outpath = cms.EndPath(process.out)

