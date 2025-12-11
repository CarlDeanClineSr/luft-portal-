#include "FWCore/Framework/interface/EDAnalyzer.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "DataFormats/SiPixelDigi/interface/SiPixelDigiCollection.h"
#include "DataFormats/SiStripDigi/interface/SiStripDigi.h"
#include "DataFormats/EcalRecHit/interface/EcalRecHitCollections.h"
#include "DataFormats/HcalRecHit/interface/HcalRecHitCollections.h"
#include "DataFormats/CSCRecHit/interface/CSCRecHit2D.h"
#include <fstream>
#include <json/json.h>

class OccupancyAnalyzer : public edm::EDAnalyzer {
public:
  explicit OccupancyAnalyzer(edm::ParameterSet const& p):
    pixelTag_(p.getParameter<edm::InputTag>("pixelDigis")),
    stripTag_(p.getParameter<edm::InputTag>("stripDigis")),
    ecalEBTag_(p.getParameter<edm::InputTag>("ecalEBRecHits")),
    hcalHBHETag_(p.getParameter<edm::InputTag>("hcalHBHERecHits")),
    outFile_(p.getParameter<std::string>("output"))
  {
    outfile_.open(outFile_);
  }
  ~OccupancyAnalyzer() override { outfile_.close(); }

  void analyze(edm::Event const& ev, edm::EventSetup const&) override {
    Json::Value root;
    root["event_id"] = (Json::UInt64) ev.id().event();
    root["run"] = (Json::UInt64) ev.id().run();
    if (ev.isLuminosityBlock())
      root["lumi_section"] = (Json::UInt64) ev.id().luminosityBlock();

    // Pixel
    edm::Handle<SiPixelDigiCollection> pixelDigis;
    ev.getByLabel(pixelTag_, pixelDigis);
    unsigned pixelHits = 0;
    for (auto const& detUnit : *pixelDigis) {
      pixelHits += detUnit.second->size();
    }
    root["subdetector"]["pixel_hits"] = pixelHits;

    // (Similar logic for strips, ecal, hcal, muon segments)
    // Placeholder fractions (should divide by known maxima or reference counts)
    root["occupancy"]["pixel_fraction"] = pixelHits / 6.6e7;

    // Energy flow bins placeholder:
    Json::Value ef(Json::arrayValue);
    for (int i=0;i<8;++i) ef.append(0.0);
    root["energy_flow_bins"] = ef;
    root["entropy_H"] = 0.0;
    root["overflow_flag"] = false;

    outfile_ << Json::FastWriter().write(root);
  }

  void endJob() override {}

private:
  edm::InputTag pixelTag_, stripTag_, ecalEBTag_, hcalHBHETag_;
  std::string outFile_;
  std::ofstream outfile_;
};

DEFINE_FWK_MODULE(OccupancyAnalyzer);
