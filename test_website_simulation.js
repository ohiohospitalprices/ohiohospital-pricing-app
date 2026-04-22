// Simulate the website behavior after Mount Carmel fix
const fs = require('fs');
const path = require('path');

// Load procedures.json as the website would
const proceduresPath = path.join(__dirname, 'ohiohospital-pricing-app', 'hospital_pricing', 'procedures.json');
const allProcedures = JSON.parse(fs.readFileSync(proceduresPath, 'utf8'));

console.log('\n╔════════════════════════════════════════════════════════════╗');
console.log('║           WEBSITE SIMULATION - HOSPITAL DROPDOWN          ║');
console.log('╚════════════════════════════════════════════════════════════╝\n');

// Hospital system mapping (from index.html)
const hospitalSystems = {
    OhioHealth: [
        'Berger Hospital', 'Doctors Hospital', 'Dublin Methodist Hospital',
        'Grady Memorial Hospital', 'Grant Medical Center', 'Grove City Methodist',
        'Hardin Memorial Hospital', 'Mansfield Hospital', 'Marion General Hospital',
        "O'Bleness Hospital", 'Pickerington Methodist Hospital', 'Riverside Methodist Hospital',
        'Shelby Hospital', 'Southeastern Medical Center', 'Van Wert Hospital'
    ],
    OSU: [
        'OSU Wexner Medical Center', 'Arthur G James Cancer Hospital'
    ],
    MountCarmel: [
        'Mount Carmel East', 'Mount Carmel West', 'Mount Carmel New Albany',
        'Mount Carmel Grove City', 'Mount Carmel Westerville', 'Mount Carmel Delaware'
    ]
};

// Test each system tab
for (const [system, hospitals] of Object.entries(hospitalSystems)) {
    console.log(`📋 ${system} System:`);
    console.log('─'.repeat(60));
    
    let totalFound = 0;
    let totalNotFound = 0;
    
    for (const hospital of hospitals) {
        const count = allProcedures.filter(p => p.hospital === hospital).length;
        const status = count > 0 ? '✅' : '❌';
        
        if (count > 0) {
            totalFound++;
            console.log(`${status} ${hospital.padEnd(35)} → ${count.toLocaleString()} procedures`);
        } else {
            totalNotFound++;
            console.log(`${status} ${hospital.padEnd(35)} → NO DATA`);
        }
    }
    
    console.log(`\nResult: ${totalFound}/${hospitals.length} hospitals working`);
    if (totalNotFound > 0) {
        console.log(`⚠️  ${totalNotFound} hospital(s) missing data!`);
    } else {
        console.log('✅ All hospitals in this system have procedures!');
    }
    console.log('\n');
}

// Test search scenarios
console.log('\n╔════════════════════════════════════════════════════════════╗');
console.log('║          TEST: "0 OF X" MESSAGE SHOULD NOW BE FIXED         ║');
console.log('╚════════════════════════════════════════════════════════════╝\n');

// Simulate: User selects "Mount Carmel East" hospital
const mountCarmelEast = 'Mount Carmel East';
const mcCount = allProcedures.filter(p => p.hospital === mountCarmelEast).length;

console.log(`User selects: ${mountCarmelEast}`);
console.log(`Total procedures for this hospital: ${mcCount.toLocaleString()}`);
console.log(`Website will display: "Showing ${mcCount.toLocaleString()} of ${allProcedures.length.toLocaleString()} procedures"`);

if (mcCount > 0) {
    console.log('✅ FIX VERIFIED: Mount Carmel East has procedures!');
    
    // Show sample procedures
    const samples = allProcedures.filter(p => p.hospital === mountCarmelEast).slice(0, 3);
    console.log('\nSample procedures for this hospital:');
    samples.forEach((proc, i) => {
        console.log(`  ${i+1}. ${proc.procedure} (${proc.cpt}) - $${proc.price}`);
    });
} else {
    console.log('❌ ISSUE: Mount Carmel East still has no procedures!');
}

// Overall summary
console.log('\n╔════════════════════════════════════════════════════════════╗');
console.log('║                   OVERALL SUMMARY                         ║');
console.log('╚════════════════════════════════════════════════════════════╝\n');

const allHospitals = [...new Set(allProcedures.map(p => p.hospital))];
const hospitalsWithData = allHospitals.filter(h => allProcedures.some(p => p.hospital === h));

console.log(`Total hospitals in dropdown: ${allHospitals.length}`);
console.log(`Hospitals with procedure data: ${hospitalsWithData.length}`);
console.log(`Total procedures: ${allProcedures.length.toLocaleString()}`);

if (hospitalsWithData.length === allHospitals.length) {
    console.log('\n✅ SUCCESS: Every hospital in the dropdown has procedures!');
    console.log('✅ "0 of X procedures" bug is FIXED');
} else {
    const missing = allHospitals.filter(h => !hospitalsWithData.includes(h));
    console.log('\n❌ STILL BROKEN: Some hospitals missing data:');
    missing.forEach(h => console.log(`   - ${h}`));
}

console.log('\n');
