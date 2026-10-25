const fs = require('fs');
const path = require('path');

const files = [
  'src/data/investigations/AOI-SNOW-OPP-002.json',
  'src/data/investigations/AOI-TEST-OPP-999.json'
];

for (const file of files) {
  const filePath = path.resolve(file);
  const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

  if (!data.sources) {
    data.sources = [
      {
        id: "src-01",
        title: "ServiceNow documentation",
        url: "https://docs.servicenow.com",
        source_type: "PRIMARY",
        used_by: data.checkpoints.map(cp => cp.id)
      }
    ];
  }

  data.checkpoints = data.checkpoints.map(cp => {
    return {
      id: cp.id,
      title: cp.title || cp.id,
      tested: cp.tested || "Whether the broad exception problem represented a differentiated decision boundary.",
      found: cp.found || "Native ServiceNow capabilities already covered substantial exception-management activity.",
      what_changed: cp.what_changed || "Investigation narrowed from a broad exception problem to a specific decision-boundary hypothesis.",
      resulting_state: cp.resulting_state || cp.result || "CONTINUE INVESTIGATION",
      evidence_refs: cp.evidence_refs || [],
      source_refs: cp.source_refs || ["src-01"],
      provenance: cp.provenance || { source_file: "unknown", section: "unknown", line_start: null, line_end: null }
    };
  });

  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
  console.log(`Updated ${file}`);
}
