 # Fast clone (recommended for quick access)
git clone --depth 1 [https://github.com/CarlDeanClineSr/luft-portal-.git](https://github.com/CarlDeanClineSr/luft-portal-.git)
cd luft-portal-

# Install dependencies
pip install pandas numpy matplotlib scipy

# Run the Autonomous Substrate Crawler to audit the telemetry
python scripts/luft_omni_crawler.py
