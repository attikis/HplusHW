import FWCore.ParameterSet.Config as cms
import copy

from PhysicsTools.PatAlgos.patEventContent_cff import patEventContentNoCleaning
from PhysicsTools.PatAlgos.tools.jetTools import addJetCollection
from PhysicsTools.PatAlgos.tools.cmsswVersionTools import run36xOn35xInput
from PhysicsTools.PatAlgos.tools.tauTools import addTauCollection, classicTauIDSources
from PhysicsTools.PatAlgos.tools.metTools import addTcMET, addPfMET
from PhysicsTools.PatAlgos.tools.trigTools import switchOnTrigger
from PhysicsTools.PatAlgos.tools.coreTools import removeMCMatching, restrictInputToAOD
import HiggsAnalysis.HeavyChHiggsToTauNu.HChTrigger_cfi as HChTrigger
import HiggsAnalysis.HeavyChHiggsToTauNu.ChargedHiggsTauIDDiscrimination_cfi as HChTauDiscriminators
import HiggsAnalysis.HeavyChHiggsToTauNu.ChargedHiggsTauIDDiscriminationContinuous_cfi as HChTauDiscriminatorsCont
import HiggsAnalysis.HeavyChHiggsToTauNu.ChargedHiggsCaloTauIDDiscrimination_cfi as HChCaloTauDiscriminators
import HiggsAnalysis.HeavyChHiggsToTauNu.ChargedHiggsCaloTauIDDiscriminationContinuous_cfi as HChCaloTauDiscriminatorsCont
import HiggsAnalysis.HeavyChHiggsToTauNu.HChTaus_cfi as HChTaus
import HiggsAnalysis.HeavyChHiggsToTauNu.HChTausCont_cfi as HChTausCont

# Assumes that process.out is the output module
#
#
# process      cms.Process object
# dataVersion  Version of the input data (needed for the trigger info process name) 
def addPat(process, dataVersion):
    out = None
    outdict = process.outputModules_()
    if outdict.has_key("out"):
        out = outdict["out"]

    # Tau Discriminators
    process.load("RecoTauTag.Configuration.RecoTCTauTag_cff")
    HChTauDiscriminators.addHplusTauDiscriminationSequence(process, dataVersion)
    HChTauDiscriminatorsCont.addHplusTauDiscriminationSequenceCont(process, dataVersion)

    HChCaloTauDiscriminators.addHplusCaloTauDiscriminationSequence(process)
    HChCaloTauDiscriminatorsCont.addHplusCaloTauDiscriminationSequenceCont(process)

    # These are already in 36X AOD, se remove them from the tautagging
    # sequence
    if not dataVersion.is35X():
        process.tautagging.remove(process.jptRecoTauProducer)
        process.tautagging.remove(process.caloRecoTauProducer)
        process.tautagging.remove(process.caloRecoTauDiscriminationAgainstElectron)
        process.tautagging.remove(process.caloRecoTauDiscriminationByIsolation)
        process.tautagging.remove(process.caloRecoTauDiscriminationByLeadingTrackFinding)
        process.tautagging.remove(process.caloRecoTauDiscriminationByLeadingTrackPtCut)
        
    process.load("RecoTauTag.Configuration.HPSPFTaus_cfi")

    # PAT Layer 0+1
    process.load("PhysicsTools.PatAlgos.patSequences_cff")

    # Count the number of primary vertices, and put into event
    process.primaryVertexNumber = cms.EDProducer("HPlusVertexCountProducer",
        src = cms.InputTag('offlinePrimaryVertices'),
        alias = cms.string("primaryVertexNumber")
    )
    if out != None:
        out.outputCommands.append("keep int_primaryVertexNumber_*_*")

    process.hplusPatSequence = cms.Sequence(
	process.tautagging *
        process.hplusTauDiscriminationSequence *
	process.hplusTauDiscriminationSequenceCont *
	process.produceAndDiscriminateHPSPFTaus *
	process.hplusCaloTauDiscriminationSequence *
	process.hplusCaloTauDiscriminationSequenceCont *
        process.patDefaultSequence *
        process.primaryVertexNumber
    )

    # Restrict input to AOD
    restrictInputToAOD(process, ["All"])

    # Remove MC stuff if we have collision data (has to be done any add*Collection!)
    if dataVersion.isData():
        removeMCMatching(process, ["All"])

    # Jets
    process.patJets.jetSource = cms.InputTag("ak5CaloJets")
    process.patJets.trackAssociationSource = cms.InputTag("ak5JetTracksAssociatorAtVertex")
    process.patJets.addJetID = False
    if dataVersion.is38X():
        process.patJets.addTagInfos = False

    addJetCollection(process,cms.InputTag('JetPlusTrackZSPCorJetAntiKt5'),
                     'AK5', 'JPT',
                     doJTA        = True,
                     doBTagging   = True,
                     jetCorrLabel = ('AK5','JPT'),
                     doType1MET   = False,
                     doL1Cleaning = False,
                     doL1Counters = True,
                     genJetCollection = cms.InputTag("ak5GenJets"),
                     doJetID      = False
                     )
    if out != None:
        out.outputCommands.append("keep *_selectedPatJetsAK5JPT_*_*")

    #### needed for CMSSW35x data
    if dataVersion.is35X():
        process.load("RecoJets.Configuration.GenJetParticles_cff")
        process.load("RecoJets.Configuration.RecoGenJets_cff")
        ## creating JPT jets
        process.load('JetMETCorrections.Configuration.DefaultJEC_cff')
        process.load('RecoJets.Configuration.RecoJPTJets_cff')

        run36xOn35xInput(process)


    # Taus

    # Set default PATTauProducer options here, they should be
    # replicated to all added tau collections (and the first call to
    # addTauCollection should replace the default producer modified
    # here)
    # process.patTaus.embedLeadTrack = True

    # For some reason, embedding these for 35X data does NOT work for
    # calotaus (output module complains about trying to persist
    # transient Ref/Ptr, so I'd guess there's transient RefVector of
    # tracks somewhere in the calotau reconstruction process

    # Update: Apparently it doesn't work on 36X collision data
    # either...

    #if not dataVersion.is35X():
    #    process.patTaus.embedSignalTracks = True
    #    process.patTaus.embedIsolationTracks = True

    # There's probably a bug in pat::Tau which in practice prevents
    # the emedding of PFCands. Therefore we keep the PFCandidates
    # collection in the event so that the PFCands can be accessed via
    # edm::Refs. (note: PFCand embedding works, so it is just the
    # collection embedding which doesn't. The PFCand embedding is
    # disabled for consistenty and saving even some disk space.

    # process.patTaus.embedLeadPFCand = True
    # process.patTaus.embedLeadPFChargedHadrCand = True
    # process.patTaus.embedLeadPFNeutralCand = True
    # process.patTaus.embedSignalPFCands = True
    # process.patTaus.embedSignalPFChargedHadrCands = True
    # process.patTaus.embedSignalPFNeutralHadrCands = True
    # process.patTaus.embedSignalPFGammaCands = True
    # process.patTaus.embedIsolationPFCands = True
    # process.patTaus.embedIsolationPFChargedHadrCands = True
    # process.patTaus.embedIsolationPFNeutralHadrCands = True
    # process.patTaus.embedIsolationPFGammaCands = True

    classicTauIDSources.extend( HChTaus.HChTauIDSources )
    classicTauIDSources.extend( HChTausCont.HChTauIDSourcesCont )

    addTauCollection(process,cms.InputTag('caloRecoTauProducer'),
		algoLabel = "caloReco",
		typeLabel = "Tau")

    addTauCollection(process,cms.InputTag('shrinkingConePFTauProducer'),
                algoLabel = "shrinkingCone",
                typeLabel = "PFTau")

    if not dataVersion.is38X():
        addTauCollection(process,cms.InputTag('fixedConePFTauProducer'),
                         algoLabel = "fixedCone",
                         typeLabel = "PFTau")

    addTauCollection(process,cms.InputTag('hpsPFTauProducer'),
                algoLabel = "hps",
                typeLabel = "PFTau")
    

    # Add PAT default event content
    if out != None:
        out.outputCommands.extend(patEventContentNoCleaning)
	out.outputCommands.extend(["drop *_selectedPatTaus_*_*",
                                   #"keep *_cleanPatTaus_*_*",
                                   #"drop *_cleanPatTaus_*_*",
                                   #"keep *_patTaus*_*_*",
                                   #"keep *_patPFTauProducerFixedCone_*_*",
                                   # keep these until the embedding problem with pat::Tau is fixed
                                   "keep recoPFCandidates_particleFlow_*_*",
                                   "keep recoTracks_generalTracks_*_*"
                                   ])

    # MET
    addTcMET(process, 'TC')
    addPfMET(process, 'PF')
    if out != None:
        out.outputCommands.extend(["keep *_patMETsPF_*_*", "keep *_patMETsTC_*_*"])


    # Trigger
    switchOnTrigger(process)
    HChTrigger.customise(process, dataVersion)

    # Build sequence
    seq = cms.Sequence()
    if dataVersion.is35X():
        process.hplusJptSequence = cms.Sequence(
            process.genJetParticles *
            process.ak5GenJets *
            process.recoJPTJets
        )
        seq *= process.hplusJptSequence

    seq *= process.hplusPatSequence

    return seq
    
