#!/bin/bash
# Fetch INTERMAGNET quasi-definitive data for Jan 6, 2026 (DOU, SUA)
# Uses INTERMAGNET web service API for near-real-time provisional data

STATIONS="dou sua"
DATE="2026-01-06"
OUTDIR="data/intermagnet_raw"

mkdir -p "$OUTDIR"

for station in $STATIONS; do
    STATION_UPPER=$(echo "$station" | tr '[:lower:]' '[:upper:]')
    
    # INTERMAGNET GetData web service URL (quasi-definitive, 1-minute)
    url="https://imag-data.bgs.ac.uk/GIN_V1/GINServices?Request=GetData"
    url="${url}&format=IAGA2002"
    url="${url}&testObsys=false"
    url="${url}&observatories=${STATION_UPPER}"
    url="${url}&dataStartDate=${DATE}"
    url="${url}&dataEndDate=${DATE}"
    url="${url}&samplesPerDay=minute"
    url="${url}&publicationState=adj-or-rep"  # adjusted/reported (quasi-definitive)
    url="${url}&recordTermination=UNIX"
    
    outfile="${OUTDIR}/${station}_${DATE//-/}.min"
    
    echo "Fetching ${STATION_UPPER} for ${DATE}..."
    curl -s "$url" -o "$outfile"
    
    # Check if file has data (IAGA2002 files have headers starting with "Format")
    if grep -q "Format" "$outfile"; then
        echo "✅ Downloaded ${STATION_UPPER} → $outfile"
    else
        echo "⚠️  Failed or no data:  ${STATION_UPPER}"
        rm -f "$outfile"
    fi
done

echo "✅ Fetch complete → ${OUTDIR}"
