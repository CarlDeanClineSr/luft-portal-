import os
import datetime

class ImperialGuardEvaluator:
    def __init__(self):
        # Define the terms that trigger a rejection or rework
        self.academic_ghost_terms = ["lattice", "nets", "grids", "fluidic", "substrate"]
        self.report = {
            "total_scans": 0,
            "rejections": 0,
            "corrections_made": [],
            "system_status": "ONLINE"
        }

    def process_text(self, text, source_name):
        """Scans the text for invalid descriptors and reworks them."""
        self.report["total_scans"] += 1
        original_text = text.lower()
        modified = False
        
        # Rework language if ghost terms are found
        for term in self.academic_ghost_terms:
            if term in original_text:
                self.report["rejections"] += 1
                modified = True
                self.report["corrections_made"].append({
                    "source": source_name,
                    "flagged_term": term,
                    "action": "REJECTED and REWORKED"
                })
                # Replaces the invalid term directly in the text
                text = text.replace(term, "[REDACTED - OBSERVED AS MAGNETIC FIELD]")
        
        return text, modified

    def generate_state_report(self):
        """Outputs the final status of the program's logic filter."""
        print("="*60)
        print(" IMPERIAL PHYSICS OBSERVATORY - PROGRAM STATE REPORT ")
        print("="*60)
        print(f"Timestamp: {datetime.datetime.now()}")
        print(f"Total Telemetry Scans: {self.report['total_scans']}")
        print(f"Total Term Rejections: {self.report['rejections']}")
        print("-" * 60)
        
        if self.report["rejections"] > 0:
            print("Log of Reworked Ghost Descriptions:")
            for entry in self.report["corrections_made"]:
                print(f" -> Source: {entry['source']} | Flagged: '{entry['flagged_term']}' | Action: {entry['action']}")
        else:
            print("Status: 100% Mathematical Compliance. No ghost terms detected.")
        print("="*60)

# ---------------------------------------------------------
# Execution Block for Colab / Main
# ---------------------------------------------------------
if __name__ == "__main__":
    evaluator = ImperialGuardEvaluator()
    
    # Sample data mimicking a telemetry feed or external academic input
    feed_1 = "The substrate of the vacuum interacts with the mass."
    feed_2 = "Magnetic field mapping confirms standard mathematical values."
    feed_3 = "A fluidic lattice structure is observed in the data."

    print("Processing Data Streams...\n")
    
    # Run the processing logic
    clean_1, mod_1 = evaluator.process_text(feed_1, "Data_Stream_Alpha")
    clean_2, mod_2 = evaluator.process_text(feed_2, "Data_Stream_Beta")
    clean_3, mod_3 = evaluator.process_text(feed_3, "Data_Stream_Gamma")

    # Output the cleaned strings to see the rework
    print(f"Output Alpha: {clean_1}")
    print(f"Output Beta:  {clean_2}")
    print(f"Output Gamma: {clean_3}\n")

    # Generate the final Copilot-style report
    evaluator.generate_state_report()
