import { Kafka } from 'gcn-kafka';
import fs from 'fs';
import path from 'path';

// Pull credentials from GitHub Secrets
const CLIENT_ID = process.env.GCN_CLIENT_ID;
const CLIENT_SECRET = process.env.GCN_CLIENT_SECRET;
const CSV_FILE = path.join(process.cwd(), 'data', 'neutrino_events', 'icecube_strikes.csv');

async function runTrap() {
    console.log(`[${new Date().toISOString()}] Arming LUFT Neutrino Trap (v1.0.0)...`);

    const kafka = new Kafka({
        client_id: CLIENT_ID,
        client_secret: CLIENT_SECRET,
    });

    const consumer = kafka.consumer();
    
    // Explicit connect call required in v1.0.0
    await consumer.connect(); 

    // Subscribe to both classic Astrotrack feeds (Gold and Bronze)
    await consumer.subscribe({
        topics: [
            'gcn.classic.text.ICECUBE_ASTROTRACK_GOLD',
            'gcn.classic.text.ICECUBE_ASTROTRACK_BRONZE'
        ]
    });

    // Ensure the data directory exists
    const dir = path.dirname(CSV_FILE);
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }

    // Set a timeout to shut the trap down after 5 minutes so GitHub Actions doesn't hang
    const timeout = setTimeout(() => {
        console.log("5-minute scan complete. Disarming trap to preserve Actions budget.");
        consumer.disconnect();
        process.exit(0);
    }, 300000);

    await consumer.run({
        eachMessage: async ({ topic, partition, message }) => {
            console.log("\n==================================================");
            console.log(`KINETIC STRIKE DETECTED ON CHANNEL: ${topic}`);
            console.log("==================================================");
            
            const rawData = message.value.toString();
            console.log(`Raw Telemetry: ${rawData.substring(0, 200)}...`);

            // Extract the basic timestamp
            const strikeTime = new Date().toISOString();
            
            // Append to the LUFT ledger
            const csvLine = `${strikeTime},${topic}\n`;
            fs.appendFileSync(CSV_FILE, csvLine);
            console.log(`Strike logged to ${CSV_FILE}`);
        },
    });
}

runTrap().catch(console.error);
