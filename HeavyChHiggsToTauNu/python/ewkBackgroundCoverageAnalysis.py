import FWCore.ParameterSet.Config as cms

def createEDAnalyze(param):
    return cms.EDAnalyzer("HPlusEwkBackgroundCoverageAnalyzer",
        histogramAmbientLevel = param.histogramAmbientLevel,
        trigger = param.trigger.clone(),
        primaryVertexSelection = param.primaryVertexSelection.clone(),
        GlobalElectronVeto = param.GlobalElectronVeto.clone(),
        GlobalMuonVeto = param.GlobalMuonVeto.clone(),
        tauSelection = param.tauSelectionHPSMediumTauBased.clone(),
        jetSelection = param.jetSelection.clone(),
        MET = param.MET.clone(),
        bTagging = param.bTagging.clone(),
        deltaPhiTauMET = param.deltaPhiTauMET,

        eventCounter = param.eventCounter.clone(),
        genParticleSrc = cms.untracked.InputTag("genParticles"),
#        embeddingMuonSrc = cms.untracked.InputTag(param.GlobalMuonVeto.MuonCollectionName.value()),
        embeddingMuonSrc = cms.untracked.InputTag("tauEmbeddingMuons"), # it is the responsibility of _cfg.py to make sure "tauEmbeddingMuons" exists
        tauPtCut = cms.untracked.double(41.0),
        tauEtaCut = cms.untracked.double(2.1),

        # for tree
        muonSrc = cms.InputTag("dummy"),
        muonFunctions = cms.PSet(
            dB = cms.string("dB()"),

            chargedHadronIso = cms.string("chargedHadronIso()"),
            neutralHadronIso = cms.string("neutralHadronIso()"),
            photonIso = cms.string("photonIso()"),
            puChargedHadronIso = cms.string("puChargedHadronIso()"),
        ),

        # Options below are not really used, they're just needed to
        # use the same configuration code
        triggerEfficiencyScaleFactor = param.triggerEfficiencyScaleFactor.clone(),
        vertexWeight = param.vertexWeight.clone(),
        vertexWeightReader = param.vertexWeightReader.clone(),
        Tree = param.tree.clone(),
        tauEmbeddingStatus = cms.untracked.bool(False),
    )
