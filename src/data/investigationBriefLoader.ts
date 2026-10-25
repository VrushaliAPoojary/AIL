import { validateInvestigationBrief } from './investigationBriefValidator';
import type { InvestigationBrief } from '../types/investigationBrief';

import opp13 from './investigations/industries/Healthcare/nayati_medicity/OPP-013.json';
import opp16 from './investigations/industries/Healthcare/nayati_medicity/OPP-016.json';
import opp12 from './investigations/industries/Healthcare/fortis_healthcare_bengaluru/OPP-012.json';
import opp14 from './investigations/industries/Healthcare/aiims_bhopal/OPP-014.json';
import opp01 from './investigations/industries/Healthcare/apollo_hospitals/OPP-001.json';
import opp11 from './investigations/industries/Healthcare/fortis_hospital_mohali/OPP-011.json';
import bmc03 from './investigations/industries/IT & Business Services/BMC Helix/OPP-003.json';
import bmc02 from './investigations/industries/IT & Business Services/BMC Helix/OPP-002.json';
import bmc04 from './investigations/industries/IT & Business Services/BMC Helix/OPP-004.json';
import bmc01 from './investigations/industries/IT & Business Services/BMC Helix/OPP-001.json';
import sn06 from './investigations/industries/IT & Business Services/servicenow/OPP-006.json';
import sn09 from './investigations/industries/IT & Business Services/servicenow/OPP-009.json';
import sn08 from './investigations/industries/IT & Business Services/servicenow/OPP-008.json';
import sn02 from './investigations/industries/IT & Business Services/servicenow/OPP-002.json';
import sn07 from './investigations/industries/IT & Business Services/servicenow/OPP-007.json';
import imp01 from './investigations/imported/Healthcare_and_Pharmaceuticals/Baby_Memorial_Hospital_Kozhikode/opportunity - 01/OPP-001.json';
import imp08 from './investigations/imported/IT_and_Business_Services/servicenow/opportunity08/OPP-008.json';
import imp06 from './investigations/imported/IT_and_Business_Services/servicenow/opportunity06/OPP-006.json';

const rawJsonFiles = [
  opp13, opp16, opp12, opp14, opp01, opp11,
  bmc03, bmc02, bmc04, bmc01,
  sn06, sn09, sn08, sn02, sn07,
  imp01, imp08, imp06
];

export function loadAllInvestigationBriefs(): InvestigationBrief[] {
  const briefs: InvestigationBrief[] = [];

  for (const data of rawJsonFiles) {
    try {
      const validation = validateInvestigationBrief(data as any);

      if (validation.valid && validation.brief) {
        briefs.push(validation.brief);
      } else {
        console.error(`Validation failed for brief:`, validation.errors);
        throw new Error(`Validation failed for brief: AIL cannot render this Investigation Brief.`);
      }
    } catch (e) {
      console.error(`Failed to parse or validate brief:`, e);
      throw e;
    }
  }

  return briefs;
}
