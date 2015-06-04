#include "DataFormat/interface/Event.h"

#include "boost/optional.hpp"

#include <stdexcept>

Event::Event(const ParameterSet& config): 
  fTriggerTauCollection("HLTTau"),
  fPFCandidates("PFCands"),
  fGenMET("GenMET"),
  fMET_Type1("MET_Type1"),
  fCaloMET("CaloMET"),
  fL1MET("L1MET"),
  fIsMC(config.isMC())
{
  // Trigger
  boost::optional<std::vector<std::string>> triggerOR = config.getParameterOptional<std::vector<std::string>>("Trigger.triggerOR");
  if(triggerOR) {
    fTriggerOr.setBranchNames(*triggerOR);
  }
  boost::optional<std::vector<std::string>> triggerOR2 = config.getParameterOptional<std::vector<std::string>>("Trigger.triggerOR2");
  if(triggerOR2) {
    fTriggerOr2.setBranchNames(*triggerOR2);
  }

  bool variationAssigned = false;
  // Systematics
  boost::optional<std::string> jetSyst = config.getParameterOptional<std::string>("JetSelection.systematicVariation");
  if(jetSyst) {
    fJetCollection.setEnergySystematicsVariation(*jetSyst);
    fMET_Type1.setEnergySystematicsVariation(*jetSyst);
    variationAssigned = true;
  }

  boost::optional<std::string> tauSyst = config.getParameterOptional<std::string>("TauSelection.systematicVariation");
  if(tauSyst) {
    if(variationAssigned) {
      throw std::runtime_error("Trying to set systematicVariation for taus, but a variation has already been set for jets! Only one variation per analyzer is allowed");
    }
    fTauCollection.setEnergySystematicsVariation(*tauSyst);
    fMET_Type1.setEnergySystematicsVariation(*tauSyst);
    variationAssigned = true;
  }

  // Tau discriminators
  boost::optional<std::vector<std::string> > tauDiscr = config.getParameterOptional<std::vector<std::string> >("TauSelection.discriminators");
  if(tauDiscr) {
    fTauCollection.setConfigurableDiscriminators(*tauDiscr);
  }
  fTauCollection.setAgainstElectronDiscriminator(config.getParameter<std::string>("TauSelection.againstElectronDiscr"));
  fTauCollection.setAgainstMuonDiscriminator(config.getParameter<std::string>("TauSelection.againstMuonDiscr"));
  fTauCollection.setIsolationDiscriminator(config.getParameter<std::string>("TauSelection.isolation"));
  
  // Muon discriminators
  // FIXME
  // Electron discriminators
  // FIXME
  // Jet discriminators
  // FIXME
}

Event::~Event() {}

void Event::setupBranches(BranchManager& mgr) {
  fEventID.setupBranches(mgr);

  fNPU.setupBranches(mgr);

  fTriggerOr.setupBranches(mgr);
  fTriggerOr2.setupBranches(mgr);

  fTriggerTauCollection.setupBranches(mgr);
  fTauCollection.setupBranches(mgr);
  fJetCollection.setupBranches(mgr);
  fGenJetCollection.setupBranches(mgr);
  fMuonCollection.setupBranches(mgr);
  fElectronCollection.setupBranches(mgr);
  fGenParticleCollection.setupBranches(mgr);
  fGenMET.setupBranches(mgr);
  fMET_Type1.setupBranches(mgr);
  fCaloMET.setupBranches(mgr);
  fL1MET.setupBranches(mgr);
  fPFCandidates.setupBranches(mgr);
}
