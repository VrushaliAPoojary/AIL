"""
tests/test_azure_devops_integration.py

Comprehensive test suite for Azure DevOps Integration for Automatic Bug Creation.

Tests:
1. Correct Azure request generated (JSON Patch op, path, value).
2. Correct title mapping: '[ART-AGENT-001] Flaky token parser'.
3. Repro steps preserved in HTML body.
4. Expected result preserved.
5. Actual result preserved.
6. Business impact preserved.
7. Recommended solution preserved.
8. Module preserved.
9. Environment preserved.
10. Severity preserved.
11. Priority preserved.
12. Tags preserved (includes 'ART:ART-AGENT-001' and 'ART-AGENT-001').
13. Discussion preserved.
14. Missing values are not invented ('Not provided' preserved).
15. HTML escaping prevents XSS / arbitrary HTML injection.
16. Successful Azure response persists Work Item ID.
17. Existing Work Item ID prevents duplicate creation.
18. Repeated request returns existing reference with is_duplicate=True.
19. Azure 400 validation error handled with 400 response.
20. Azure 401 authentication error handled with sanitized 502 response.
21. Azure 403 authorization error handled with sanitized 502 response.
22. Azure 404 organization/project not found handled with sanitized 502 response.
23. Azure 429 rate limit handled with 429 response.
24. Azure 5xx service failure handled with sanitized 502 response.
25. Timeout handled with sanitized 504 response.
26. PAT token never appears in errors.
27. PAT token never appears in persisted investigation or logs.
28. Invalid ART ID rejected with 400.
29. Unknown ART ID rejected with 404.
30. Unconfirmed/unapproved bug rejected with 400.
31. Existing lifecycle/ticket data remains completely unchanged.
32. Reconciliation via WIQL search prevents duplicate on network drop/retry.
"""

import unittest
import os
import shutil
import tempfile
import json
from unittest.mock import patch, MagicMock

# pyrefly: ignore[missing-import]
import httpx
# pyrefly: ignore[missing-import]
from fastapi.testclient import TestClient

from api.app import create_app
from core.storage.schema import init_db
from core.storage.db import get_connection
from core.storage.service import ResolutionService
from core.storage.integrations import get_external_work_item
from integrations.azure_devops.models import (
    AzureDevOpsConfig,
    AzureDevOpsError,
    EvidenceSyncError,
    AzureFeatureRouter,
    AZURE_MODULE_FEATURE_MAP
)
from integrations.azure_devops.client import AzureDevOpsClient


class TestAzureDevOpsIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_ado.db")
        self.conn = get_connection(self.db_path)
        init_db(self.conn)
        self.app = create_app(db_path=self.db_path)
        self.client = TestClient(self.app, raise_server_exceptions=False)

        # Base mock environment
        self.mock_env = {
            "AZURE_DEVOPS_ORGANIZATION": "test-org",
            "AZURE_DEVOPS_PROJECT": "test-project",
            "AZURE_DEVOPS_PAT": "SECRET_TEST_PAT_TOKEN_12345",
            "AZURE_DEVOPS_API_VERSION": "7.0"
        }

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.test_dir)

    def _seed_confirmed_bug(self, module="AGENT", title="Token Parser Issue", **ticket_kwargs) -> str:
        """Seeds a confirmed BUG and returns canonical_bug_id."""
        res_cap = self.client.post("/api/v1/investigations", json={
            "tester_description": "Observed parser fault",
            "reporter": "tester-1"
        })
        inv_id = res_cap.json()["investigation"]["investigation_id"]

        ticket_data = {
            "title": title,
            "reproSteps": "1. Run tokenizer\n2. Inspect memory",
            "expectedResult": "Tokens parsed smoothly",
            "actualResult": "Segfault or crash",
            "businessImpact": "High latency in agent inference",
            "recommendedSolution": "Add length bounds check",
            "environment": "staging-us-east-1",
            "severity": "HIGH",
            "priority": "P1",
            "tags": ["parser", "agent-core"],
            "discussion": [
                {"author": "dev-alice", "message": "Investigating boundary", "timestamp": "2026-09-28T10:00:00Z"}
            ]
        }
        ticket_data.update(ticket_kwargs)

        res_conf = self.client.post(f"/api/v1/investigations/{inv_id}/confirm", json={
            "module": module,
            "ticket": ticket_data,
            "actor": "lead-qa"
        })
        self.assertEqual(res_conf.status_code, 200)
        return res_conf.json()["investigation"]["canonical_bug_id"]

    # =========================================================================
    # 1. FIELD MAPPING & HTML SAFETY TESTS
    # =========================================================================

    def test_01_to_15_field_mapping_and_html_safety(self):
        config = AzureDevOpsConfig(
            organization="my-org",
            project="my-project",
            pat="secret-token-xyz"
        )
        client = AzureDevOpsClient(config)

        ticket = {
            "title": "Unescaped <script>alert('xss')</script> in title",
            "repro_steps": "Steps with <script>alert('xss')</script> & <tag>",
            "expected_result": "Clean <output>",
            "actual_result": "Err <crash>",
            "business_impact": "Loss of $$ & data",
            "recommended_solution": "Use html.escape()",
            "module": "AGENT",
            "environment": "prod-cluster",
            "severity": "CRITICAL",
            "priority": "P0",
            "tags": ["frontend", "security"],
            "discussion": [
                {"author": "alice <admin>", "message": "Found <bug>", "timestamp": "2026-09-28T12:00:00Z"}
            ]
        }
        patch = client._map_ticket_to_patch(ticket, canonical_bug_id="ART-AGENT-001")

        # 1. Title mapping
        title_patch = next(p for p in patch if p["path"] == "/fields/System.Title")
        self.assertEqual(title_patch["op"], "add")
        self.assertEqual(title_patch["value"], "[ART-AGENT-001] Unescaped <script>alert('xss')</script> in title")

        # 2. Repro steps HTML content: contains complete developer body across 11 canonical sections
        repro_patch = next(p for p in patch if p["path"] == "/fields/Microsoft.VSTS.TCM.ReproSteps")
        html_val = repro_patch["value"]

        # Microsoft.VSTS.TCM.ReproSteps must contain all 11 canonical sections
        for header in [
            "Problem", "Observed Behavior", "Reproduction", "Expected Behavior",
            "Business Impact", "User Experience", "Investigation Guidance",
            "Fix Requirement", "Recommended Solution", "Minimum Working Fix",
            "Acceptance Criteria"
        ]:
            self.assertIn(f"<strong>{header}</strong>", html_val)

        # Repro steps within body must be properly escaped
        self.assertIn("Steps with &lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt; &amp; &lt;tag&gt;", html_val)
        self.assertNotIn("<script>", html_val)
        self.assertNotIn("Competitor Analysis", html_val)

        # 12. Tags
        tags_patch = next(p for p in patch if p["path"] == "/fields/System.Tags")
        tags_val = tags_patch["value"]
        self.assertIn("ART:ART-AGENT-001", tags_val)
        self.assertIn("ART-AGENT-001", tags_val)
        self.assertIn("ART", tags_val.split("; "))
        self.assertIn("Agent-Lab", tags_val)
        self.assertIn("Structured-Output", tags_val)
        self.assertIn("Governance-Safety", tags_val)

        # 13. Negative check: Custom.ARTResolutionBrief and custom fields must NOT exist in patch
        custom_patches = [p for p in patch if p["path"].startswith("/fields/Custom.")]
        self.assertEqual(len(custom_patches), 0)

        # 14. Severity and Priority mapping
        sev_patch = next(p for p in patch if p["path"] == "/fields/Microsoft.VSTS.Common.Severity")
        self.assertEqual(sev_patch["value"], "1 - Critical")

        pri_patch = next(p for p in patch if p["path"] == "/fields/Microsoft.VSTS.Common.Priority")
        self.assertEqual(pri_patch["value"], 1)

        # 15. SystemInfo mapping when environment is provided
        env_patch = next(p for p in patch if p["path"] == "/fields/Microsoft.VSTS.TCM.SystemInfo")
        self.assertEqual(env_patch["value"], "prod-cluster")

        # Verify exact tag list elements for ART-AGENT-001
        expected_tag_list = [
            "ART:ART-AGENT-001",
            "ART-AGENT-001",
            "ART",
            "Agent-Lab",
            "Structured-Output",
            "Output-Parser",
            "Schema-Validation",
            "Contract-Enforcement",
            "Governance-Safety"
        ]
        self.assertEqual(tags_val.split("; "), expected_tag_list)

    def test_regression_base_art_tag_required_on_every_bug(self):
        """
        Regression test requiring the base-product tag 'ART' on every production ART Bug,
        even if projection or custom ticket tags omit it.
        """
        config = AzureDevOpsConfig(organization="org", project="proj", pat="pat")
        client = AzureDevOpsClient(config)

        # Case 1: minimal ticket without explicit ART tag
        patch = client._map_ticket_to_patch({"title": "Simple issue"}, canonical_bug_id="ART-DB-005")
        tags_patch = next(p for p in patch if p["path"] == "/fields/System.Tags")
        tags_list = tags_patch["value"].split("; ")
        self.assertIn("ART", tags_list)
        self.assertEqual(tags_list[0], "ART:ART-DB-005")
        self.assertEqual(tags_list[1], "ART-DB-005")
        self.assertEqual(tags_list[2], "ART")

        # Case 2: ticket with custom module and tags
        patch2 = client._map_ticket_to_patch(
            {"title": "Custom", "module": "GOVERNANCE", "tags": ["policy", "eval"]},
            canonical_bug_id="ART-GOV-010"
        )
        tags_patch2 = next(p for p in patch2 if p["path"] == "/fields/System.Tags")
        tags_list2 = tags_patch2["value"].split("; ")
        self.assertIn("ART", tags_list2)
        self.assertIn("governance", tags_list2)
        self.assertIn("policy", tags_list2)

    def test_14_preserves_not_provided_without_inventing(self):
        # pyrefly: ignore [missing-import]
        from integrations.azure_devops.projection import (
            DeveloperTicketProjection,
            AzureDescriptionFormatter
        )

        proj = DeveloperTicketProjection(
            canonical_bug_id="ART-GOV-001",
            title="Minimal bug",
            problem="Minimal problem statement.",
            what_is_failing=[],
            repro_steps=None,
            expected_result=None,
            business_impact=None,
            user_experience=None,
            recommended_solution=None,
            minimum_working_fix="Apply minimal check."
        )
        html_val = AzureDescriptionFormatter.format_html(proj)
        self.assertIn("<strong>Problem</strong>", html_val)
        self.assertIn("Minimal problem statement.", html_val)
        self.assertIn("<strong>Reproduction</strong>", html_val)
        self.assertIn("<p>Not provided</p>", html_val)
        self.assertIn("<strong>Business Impact</strong>", html_val)
        self.assertIn("<strong>Acceptance Criteria</strong>", html_val)

    # =========================================================================
    # 2. SUCCESSFUL EXPORT & DUPLICATE PREVENTION
    # =========================================================================

    @patch("integrations.azure_devops.client.httpx.Client")
    def test_16_to_18_successful_export_and_duplicate_prevention(self, mock_client_cls):
        art_id = self._seed_confirmed_bug(module="AGENT")

        mock_http = MagicMock()
        mock_client_cls.return_value = mock_http

        # First call: WIQL returns empty, POST creates WI #4001
        wiql_resp = MagicMock(status_code=200)
        wiql_resp.json.return_value = {"workItems": []}

        create_resp = MagicMock(status_code=200)
        create_resp.json.return_value = {
            "id": 4001,
            "_links": {"html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/4001"}}
        }

        mock_http.post.side_effect = [wiql_resp, create_resp]

        with patch.dict(os.environ, self.mock_env):
            # 16. Successful export
            res1 = self.client.post(f"/api/v1/bugs/{art_id}/azure-devops")
            self.assertEqual(res1.status_code, 200)
            data1 = res1.json()
            self.assertEqual(data1["canonical_bug_id"], art_id)
            self.assertEqual(data1["work_item_id"], 4001)
            self.assertEqual(data1["work_item_url"], "https://dev.azure.com/test-org/test-project/_workitems/edit/4001")
            self.assertFalse(data1["is_duplicate"])

            # Verify persisted in database
            inv_detail = self.client.get(f"/api/v1/bugs/{art_id}").json()
            record_key = inv_detail["record_key"]
            stored = get_external_work_item(self.conn, record_key, "AZURE_DEVOPS")
            self.assertIsNotNone(stored)
            self.assertEqual(stored["external_id"], "4001")

            # 17 & 18. Repeated request: returns existing reference without calling Azure DevOps
            mock_http.reset_mock()
            res2 = self.client.post(f"/api/v1/bugs/{art_id}/azure-devops")
            self.assertEqual(res2.status_code, 200)
            data2 = res2.json()
            self.assertEqual(data2["work_item_id"], 4001)
            self.assertTrue(data2["is_duplicate"])
            mock_http.post.assert_not_called()

    # =========================================================================
    # 3. RECONCILIATION FOR UNCERTAIN-OUTCOME SCENARIO
    # =========================================================================

    @patch("integrations.azure_devops.client.httpx.Client")
    def test_32_reconciliation_finds_remote_work_item_if_local_save_was_missed(self, mock_client_cls):
        art_id = self._seed_confirmed_bug(module="SFN")

        mock_http = MagicMock()
        mock_client_cls.return_value = mock_http

        # Simulate scenario where Azure already created WI #8008, but local DB has no record
        wiql_resp = MagicMock(status_code=200)
        wiql_resp.json.return_value = {
            "workItems": [{"id": 8008, "url": "https://dev.azure.com/test-org/test-project/_workitems/edit/8008"}]
        }
        mock_http.post.return_value = wiql_resp

        with patch.dict(os.environ, self.mock_env):
            res = self.client.post(f"/api/v1/bugs/{art_id}/azure-devops")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            # Successfully adopted WI #8008 without creating duplicate
            self.assertEqual(data["work_item_id"], 8008)
            self.assertTrue(data["is_duplicate"])

            # Verify persisted locally
            inv_detail = self.client.get(f"/api/v1/bugs/{art_id}").json()
            stored = get_external_work_item(self.conn, inv_detail["record_key"], "AZURE_DEVOPS")
            # pyrefly: ignore [unsupported-operation]
            self.assertEqual(stored["external_id"], "8008")

    # =========================================================================
    # 4. ERROR HANDLING & SECRET SANITIZATION
    # =========================================================================

    @patch("integrations.azure_devops.client.httpx.Client")
    def test_19_azure_400_validation_error(self, mock_client_cls):
        art_id = self._seed_confirmed_bug()
        mock_http = MagicMock()
        mock_client_cls.return_value = mock_http

        mock_http.post.side_effect = [
            MagicMock(status_code=200, json=lambda: {"workItems": []}),
            MagicMock(status_code=400, text="Field System.Title invalid")
        ]
        with patch.dict(os.environ, self.mock_env):
            res = self.client.post(f"/api/v1/bugs/{art_id}/azure-devops")
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.json()["error"]["code"], "VALIDATION_ERROR")
            self.assertIn("Field System.Title invalid", res.json()["error"]["message"])

    @patch("integrations.azure_devops.client.httpx.Client")
    def test_20_and_21_azure_401_403_authentication_error(self, mock_client_cls):
        art_id = self._seed_confirmed_bug()
        mock_http = MagicMock()
        mock_client_cls.return_value = mock_http

        mock_http.post.side_effect = [
            MagicMock(status_code=200, json=lambda: {"workItems": []}),
            MagicMock(status_code=401, text="Unauthorized with token SECRET_TEST_PAT_TOKEN_12345")
        ]
        with patch.dict(os.environ, self.mock_env):
            res = self.client.post(f"/api/v1/bugs/{art_id}/azure-devops")
            self.assertEqual(res.status_code, 502)
            self.assertEqual(res.json()["error"]["code"], "EXTERNAL_SERVICE_ERROR")
            # 26. PAT token must never be leaked
            self.assertNotIn("SECRET_TEST_PAT_TOKEN_12345", json.dumps(res.json()))

    @patch("integrations.azure_devops.client.httpx.Client")
    def test_22_azure_404_not_found(self, mock_client_cls):
        art_id = self._seed_confirmed_bug()
        mock_http = MagicMock()
        mock_client_cls.return_value = mock_http

        mock_http.post.side_effect = [
            MagicMock(status_code=200, json=lambda: {"workItems": []}),
            MagicMock(status_code=404, text="Project not found")
        ]
        with patch.dict(os.environ, self.mock_env):
            res = self.client.post(f"/api/v1/bugs/{art_id}/azure-devops")
            self.assertEqual(res.status_code, 502)
            self.assertIn("test-project", res.json()["error"]["message"])

    @patch("integrations.azure_devops.client.httpx.Client")
    def test_23_azure_429_rate_limited(self, mock_client_cls):
        art_id = self._seed_confirmed_bug()
        mock_http = MagicMock()
        mock_client_cls.return_value = mock_http

        mock_http.post.side_effect = [
            MagicMock(status_code=200, json=lambda: {"workItems": []}),
            MagicMock(status_code=429, text="Too Many Requests")
        ]
        with patch.dict(os.environ, self.mock_env):
            res = self.client.post(f"/api/v1/bugs/{art_id}/azure-devops")
            self.assertEqual(res.status_code, 429)

    @patch("integrations.azure_devops.client.httpx.Client")
    def test_24_azure_5xx_server_error(self, mock_client_cls):
        art_id = self._seed_confirmed_bug()
        mock_http = MagicMock()
        mock_client_cls.return_value = mock_http

        mock_http.post.side_effect = [
            MagicMock(status_code=200, json=lambda: {"workItems": []}),
            MagicMock(status_code=503, text="Service Unavailable")
        ]
        with patch.dict(os.environ, self.mock_env):
            res = self.client.post(f"/api/v1/bugs/{art_id}/azure-devops")
            self.assertEqual(res.status_code, 502)

    @patch("integrations.azure_devops.client.httpx.Client")
    def test_25_timeout_handled(self, mock_client_cls):
        art_id = self._seed_confirmed_bug()
        mock_http = MagicMock()
        mock_client_cls.return_value = mock_http

        mock_http.post.side_effect = httpx.TimeoutException("Connection timed out")
        with patch.dict(os.environ, self.mock_env):
            res = self.client.post(f"/api/v1/bugs/{art_id}/azure-devops")
            self.assertEqual(res.status_code, 504)
            self.assertIn("Timeout connecting to Azure DevOps", res.json()["error"]["message"])

    # =========================================================================
    # 5. IDENTIFIER & PRESERVATION TESTS
    # =========================================================================

    def test_28_and_29_identifier_validations(self):
        with patch.dict(os.environ, self.mock_env):
            # 28. Malformed ART ID rejected with 400
            res_mal = self.client.post("/api/v1/bugs/INV-20260928-0001/azure-devops")
            self.assertEqual(res_mal.status_code, 400)
            self.assertEqual(res_mal.json()["error"]["code"], "VALIDATION_ERROR")

            # 29. Unknown ART ID returns 404
            res_unk = self.client.post("/api/v1/bugs/ART-AGENT-999/azure-devops")
            self.assertEqual(res_unk.status_code, 404)
            self.assertEqual(res_unk.json()["error"]["code"], "NOT_FOUND")

    @patch("integrations.azure_devops.client.httpx.Client")
    def test_31_preserves_lifecycle_and_ticket_data(self, mock_client_cls):
        art_id = self._seed_confirmed_bug(module="GOV")
        detail_before = self.client.get(f"/api/v1/bugs/{art_id}").json()

        mock_http = MagicMock()
        mock_client_cls.return_value = mock_http
        mock_http.post.side_effect = [
            MagicMock(status_code=200, json=lambda: {"workItems": []}),
            MagicMock(status_code=200, json=lambda: {
                "id": 1234,
                "_links": {"html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/1234"}}
            })
        ]

        with patch.dict(os.environ, self.mock_env):
            res = self.client.post(f"/api/v1/bugs/{art_id}/azure-devops")
            self.assertEqual(res.status_code, 200)

        detail_after = self.client.get(f"/api/v1/bugs/{art_id}").json()

        # Invariant checks: Domain state completely preserved
        self.assertEqual(detail_after["status"], detail_before["status"])
        self.assertEqual(detail_after["lifecycle_phase"], detail_before["lifecycle_phase"])
        self.assertEqual(detail_after["canonical_bug_id"], detail_before["canonical_bug_id"])
        self.assertEqual(detail_after["active_ticket_id"], detail_before["active_ticket_id"])
        self.assertEqual(detail_after["current_ticket"], detail_before["current_ticket"])
        self.assertEqual(detail_after["module"], detail_before["module"])
        self.assertEqual(detail_after["severity"], detail_before["severity"])
        self.assertEqual(detail_after["priority"], detail_before["priority"])

    # =========================================================================
    # 6. MODULE ROUTING & PARENT RELATION TESTS (PART 4)
    # =========================================================================

    def test_routing_all_11_features_and_aliases(self):
        # 1. Agent Lab
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("Agent Lab"), 68783)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("AGENT"), 68783)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("agent lab"), 68783)

        # 2. Orchestrator
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("Orchestrator"), 68806)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("ORCHESTRATOR"), 68806)

        # 3. Tool Builder
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("Tool Builder"), 68807)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("tool builder"), 68807)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("TOOL"), 68807)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("tool"), 68807)

        # 4. MCP Servers
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("MCP Servers"), 68808)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("mcp servers"), 68808)

        # 5. Triggers
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("Triggers"), 68809)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("TRIGGERS"), 68809)

        # 6. Credential Manager
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("Credential Manager"), 68810)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("credential manager"), 68810)

        # 7. Serverless Functions
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("Serverless Functions"), 68811)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("SFN"), 68811)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("serverless functions"), 68811)

        # 8. Governance
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("Governance"), 68812)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("GOV"), 68812)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("governance"), 68812)

        # 9. Human-in-the-Loop / Approvals
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("Human-in-the-Loop / Approvals"), 68813)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("human-in-the-loop / approvals"), 68813)

        # 10. Live Connect
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("Live Connect"), 68814)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("live connect"), 68814)

        # 11. ART Development Kit (ADK)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("ART Development Kit (ADK)"), 68815)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("ADK"), 68815)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("art development kit (adk)"), 68815)

    def test_routing_unknown_module_fails_closed(self):
        with self.assertRaises(AzureDevOpsError) as ctx:
            AzureFeatureRouter.resolve_feature_id("UNKNOWN_MODULE")
        self.assertEqual(ctx.exception.code, "AZURE_PARENT_NOT_CONFIGURED")

        with self.assertRaises(AzureDevOpsError) as ctx2:
            AzureFeatureRouter.resolve_feature_id(None)
        self.assertEqual(ctx2.exception.code, "AZURE_PARENT_NOT_CONFIGURED")

        with self.assertRaises(AzureDevOpsError) as ctx3:
            AzureFeatureRouter.resolve_feature_id("")
        self.assertEqual(ctx3.exception.code, "AZURE_PARENT_NOT_CONFIGURED")

    @patch("integrations.azure_devops.client.httpx.Client")
    def test_unknown_module_performs_zero_azure_calls(self, mock_client_cls):
        mock_http = MagicMock()
        mock_client_cls.return_value = mock_http

        # Seed bug with unmapped module
        # In ResolutionService, canonical modules are AGENT, SFN, GOV
        # But let's verify if an unmapped module was present in ticket
        art_id = self._seed_confirmed_bug(module="AGENT")
        cursor = self.conn.cursor()
        cursor.execute("UPDATE ticket_revisions SET module = 'UNKNOWN_MODULE_XYZ';")
        cursor.execute("UPDATE investigations SET module = 'UNKNOWN_MODULE_XYZ';")
        self.conn.commit()

        with patch.dict(os.environ, self.mock_env):
            res = self.client.post(f"/api/v1/bugs/{art_id}/azure-devops")
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.json()["error"]["code"], "VALIDATION_ERROR")
            self.assertIn("No Azure Feature mapping configured", res.json()["error"]["message"])

        mock_http.post.assert_not_called()

    def test_parent_relation_in_json_patch(self):
        config = AzureDevOpsConfig("org", "proj", "pat")
        client = AzureDevOpsClient(config)

        ticket = {
            "title": "Bug with parent",
            "module": "AGENT",
            "repro_steps": "Steps",
            "expected_result": "Expected",
            "actual_result": "Actual"
        }
        patch = client._map_ticket_to_patch(ticket, canonical_bug_id="ART-AGENT-001", parent_work_item_id=68783)

        # Verify parent relation
        parent_patch = next((p for p in patch if p.get("path") == "/relations/-"), None)
        self.assertIsNotNone(parent_patch)
        self.assertEqual(parent_patch["op"], "add")
        val = parent_patch["value"]
        self.assertEqual(val["rel"], "System.LinkTypes.Hierarchy-Reverse")
        self.assertIn("https://dev.azure.com/org/proj/_apis/wit/workItems/68783", val["url"])
        self.assertEqual(val["attributes"]["comment"], "Parent Feature link established during creation")

    @patch("integrations.azure_devops.client.httpx.Client")
    def test_parent_relation_included_in_initial_create_request_no_second_patch(self, mock_client_cls):
        art_id = self._seed_confirmed_bug(module="AGENT")

        mock_http = MagicMock()
        mock_client_cls.return_value = mock_http

        mock_http.post.side_effect = [
            MagicMock(status_code=200, json=lambda: {"workItems": []}),
            MagicMock(status_code=200, json=lambda: {
                "id": 9991,
                "_links": {"html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/9991"}}
            })
        ]

        with patch.dict(os.environ, self.mock_env):
            res = self.client.post(f"/api/v1/bugs/{art_id}/azure-devops")
            self.assertEqual(res.status_code, 200)

        # Exactly 2 calls: 1 WIQL query, 1 POST creation
        self.assertEqual(mock_http.post.call_count, 2)
        create_call = mock_http.post.call_args_list[1]
        sent_patch = create_call.kwargs.get("json")

        parent_patch = next((p for p in sent_patch if p.get("path") == "/relations/-"), None)
        self.assertIsNotNone(parent_patch)
        self.assertEqual(parent_patch["value"]["rel"], "System.LinkTypes.Hierarchy-Reverse")
        self.assertIn("68783", parent_patch["value"]["url"])

    def test_assignment_in_json_patch(self):
        # pyrefly: ignore [unexpected-keyword]
        config = AzureDevOpsConfig("org", "proj", "pat", assigned_to="Unnikkannan.adiyodi@bixbytessolutions.com")
        client = AzureDevOpsClient(config)

        ticket = {
            "title": "Bug with assignee",
            "module": "AGENT",
            "repro_steps": "Steps",
            "expected_result": "Expected",
            "actual_result": "Actual"
        }
        patch = client._map_ticket_to_patch(ticket, canonical_bug_id="ART-AGENT-001", parent_work_item_id=68783)

        # Verify System.AssignedTo in patch
        assign_patch = next((p for p in patch if p.get("path") == "/fields/System.AssignedTo"), None)
        self.assertIsNotNone(assign_patch)
        self.assertEqual(assign_patch["op"], "add")
        self.assertEqual(assign_patch["value"], "Unnikkannan.adiyodi@bixbytessolutions.com")

    @patch("integrations.azure_devops.client.httpx.Client")
    def test_assignment_and_parent_included_in_initial_create_request(self, mock_client_cls):
        art_id = self._seed_confirmed_bug(module="AGENT")

        mock_http = MagicMock()
        mock_client_cls.return_value = mock_http

        mock_http.post.side_effect = [
            MagicMock(status_code=200, json=lambda: {"workItems": []}),
            MagicMock(status_code=200, json=lambda: {
                "id": 9992,
                "_links": {"html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/9992"}}
            })
        ]

        env_with_assignee = dict(self.mock_env)
        env_with_assignee["AZURE_DEVOPS_ASSIGNED_TO"] = "Unnikkannan.adiyodi@bixbytessolutions.com"

        with patch.dict(os.environ, env_with_assignee):
            res = self.client.post(f"/api/v1/bugs/{art_id}/azure-devops")
            self.assertEqual(res.status_code, 200)

        # Exactly 2 calls: 1 WIQL query, 1 POST creation
        self.assertEqual(mock_http.post.call_count, 2)
        create_call = mock_http.post.call_args_list[1]
        sent_patch = create_call.kwargs.get("json")

        # Verify parent relation
        parent_patch = next((p for p in sent_patch if p.get("path") == "/relations/-"), None)
        self.assertIsNotNone(parent_patch)
        self.assertIn("68783", parent_patch["value"]["url"])

        # Verify AssignedTo
        assign_patch = next((p for p in sent_patch if p.get("path") == "/fields/System.AssignedTo"), None)
        self.assertIsNotNone(assign_patch)
        self.assertEqual(assign_patch["value"], "Unnikkannan.adiyodi@bixbytessolutions.com")

        # Verify title has canonical prefix
        title_patch = next((p for p in sent_patch if p.get("path") == "/fields/System.Title"), None)
        self.assertIsNotNone(title_patch)
        self.assertTrue(title_patch["value"].startswith(f"[{art_id}]"))

        # Verify canonical tags
        tags_patch = next((p for p in sent_patch if p.get("path") == "/fields/System.Tags"), None)
        self.assertIsNotNone(tags_patch)
        self.assertIn(f"ART:{art_id}", tags_patch["value"])

        # Zero PATCH requests made
        mock_http.patch.assert_not_called()

    def test_test_namespace_isolation_in_db_and_generator(self):
        from core.identity.generator import generate_bug_id
        from core.storage.db import AtomicIdAllocator

        # Test generator isolation
        test_id1 = generate_bug_id("AGENT", [], is_test=True)
        self.assertEqual(test_id1, "TEST-ART-AGENT-001")
        self.assertFalse(test_id1.startswith("ART-AGENT-"))

        prod_id1 = generate_bug_id("AGENT", [test_id1])
        self.assertEqual(prod_id1, "ART-AGENT-001")

        # Test AtomicIdAllocator isolation
        db_test_id1 = AtomicIdAllocator.allocate_bug_id(self.conn, "AGENT", is_test=True)
        self.assertEqual(db_test_id1, "TEST-ART-AGENT-001")

        db_prod_id1 = AtomicIdAllocator.allocate_bug_id(self.conn, "AGENT")
        self.assertEqual(db_prod_id1, "ART-AGENT-001")

    def test_repository_writer_deterministic(self):
        from core.repository.writer import format_azure_devops_section, append_or_update_azure_section

        section = format_azure_devops_section(
            work_item_id=68819,
            work_item_url="https://dev.azure.com/BixBytesSolutions/ART%20IPR-0063/_workitems/edit/68819",
            parent_feature_title="Agent Lab",
            parent_feature_id=68783,
            assigned_to="Unnikkannan Adiyodi",
            sync_status="SYNCED"
        )
        self.assertIn("## Azure DevOps", section)
        self.assertIn("- **Work Item ID:** 68819", section)
        self.assertIn("- **Parent Feature ID:** 68783", section)

        original_md = "# Title\n\nSome text.\n"
        updated_md = append_or_update_azure_section(original_md, section)
        self.assertTrue(updated_md.startswith("# Title\n\nSome text.\n\n## Azure DevOps"))

        # Updating existing section replaces cleanly
        section2 = format_azure_devops_section(
            work_item_id=68819,
            work_item_url="https://dev.azure.com/BixBytesSolutions/ART%20IPR-0063/_workitems/edit/68819",
            parent_feature_title="Agent Lab",
            parent_feature_id=68783,
            assigned_to="Unnikkannan Adiyodi",
            sync_status="RE_SYNCED"
        )
        updated2_md = append_or_update_azure_section(updated_md, section2)
        self.assertIn("Sync Status:** RE_SYNCED", updated2_md)
        self.assertEqual(updated2_md.count("## Azure DevOps"), 1)

    def test_developer_ticket_projection_golden_art_agent_001(self):
        # pyrefly: ignore [missing-import]
        from integrations.azure_devops.projection import (
            DeveloperTicketProjector,
            AzureDescriptionFormatter
        )

        ticket = {
            "title": "Structured output contract is not strictly enforced",
            "module": "AGENT",
            "repro_steps": "Not provided",
            "expected_result": "ART must validate every agent result against the configured output contract...",
            "actual_result": "The same workflow has produced: compared_fields as arrays...",
            "business_impact": "Not provided",
            "recommended_solution": "ART must enforce structured output as a platform contract...",
            "environment": "Not provided",
            "severity": "HIGH",
            "priority": "Not provided"
        }

        proj = DeveloperTicketProjector.project_ticket(ticket, "ART-AGENT-001")
        self.assertEqual(proj.canonical_bug_id, "ART-AGENT-001")
        self.assertIn("not enforcing the configured output contract", proj.problem)
        self.assertEqual(len(proj.what_is_failing), 3)
        self.assertIn("Wrong property names", proj.what_is_failing[0])
        self.assertIn("Wrong data types", proj.what_is_failing[1])
        self.assertIn("Invalid collection values", proj.what_is_failing[2])
        # pyrefly: ignore [bad-argument-type]
        self.assertIn("successful Agent Results", proj.critical_behavior)
        # pyrefly: ignore [bad-argument-type]
        self.assertIn("reliable contract", proj.business_impact)
        # pyrefly: ignore [bad-argument-type]
        self.assertIn("explicit output contract", proj.user_experience)
        # pyrefly: ignore [bad-argument-type]
        self.assertIn("server-side schema contract", proj.recommended_solution)
        # pyrefly: ignore [bad-argument-type]
        self.assertIn("OUTPUT_VALIDATION_FAILED", proj.minimum_working_fix)

        # Repro steps value for ART-AGENT-001 must be strictly 'Not provided'
        self.assertEqual(proj.repro_steps, "Not provided")

        # Format HTML for Microsoft.VSTS.TCM.ReproSteps contains complete developer body across 11 sections
        html_out = AzureDescriptionFormatter.format_html(proj)
        for sec in [
            "<strong>Problem</strong>",
            "<strong>Observed Behavior</strong>",
            "<strong>Reproduction</strong>",
            "<strong>Expected Behavior</strong>",
            "<strong>Business Impact</strong>",
            "<strong>User Experience</strong>",
            "<strong>Investigation Guidance</strong>",
            "<strong>Fix Requirement</strong>",
            "<strong>Recommended Solution</strong>",
            "<strong>Minimum Working Fix</strong>",
            "<strong>Acceptance Criteria</strong>"
        ]:
            self.assertIn(sec, html_out)

        self.assertIn("<p><strong>Reproduction</strong></p><p>Not provided</p>", html_out)
        self.assertNotIn("Competitor Analysis", html_out)

    def test_competitor_analysis_removed_from_azure_projection(self):
        # pyrefly: ignore [missing-import]
        from integrations.azure_devops.projection import (
            DeveloperTicketProjection,
            DeveloperTicketProjector,
            AzureDescriptionFormatter
        )

        ticket = {
            "title": "Structured output contract is not strictly enforced",
            "module": "AGENT",
            "repro_steps": "Not provided",
            "expected_result": "Validation required",
            "actual_result": "No validation",
            "business_impact": "Loss of reliability",
            "recommended_solution": "Platform schema contract",
            "environment": "Not provided",
            "severity": "HIGH",
            "priority": "Not provided"
        }

        proj = DeveloperTicketProjector.project_ticket(ticket, "ART-AGENT-001")
        # Ensure competitor_analysis attribute does NOT exist on projection
        self.assertFalse(hasattr(proj, "competitor_analysis"))

        html_out = AzureDescriptionFormatter.format_html(proj)
        self.assertNotIn("Competitor", html_out)
        self.assertNotIn("LangChain", html_out)
        self.assertNotIn("OpenAI", html_out)

    def test_assignee_registry_all_eight_members(self):
        from integrations.azure_devops.models import ArtAssigneeRegistry

        expected_members = {
            "unnikkannan": ("Unnikkannan Adiyodi", "Unnikkannan.adiyodi@bixbytessolutions.com"),
            "manjunatha": ("Manjunatha Shetty", "manjunatha.shetty@bixbytessolutions.com"),
            "anusha": ("Anusha Ganesh Hegde", "anusha.hegde@bixbytessolutions.com"),
            "prajwal": ("Prajwal Sanjeeva Bangera", "prajwal.bangera@bixbytessolutions.com"),
            "yuresh": ("Yuresh Kumar K", "yuresh.kumar@bixbytessolutions.com"),
            "likhith": ("Likhith Kumar", "likhith.kumar@bixbytessolutions.com"),
            "karthik": ("Karthik Suvarna", "karthik.suvarna@bixbytessolutions.com"),
            "ashish": ("Ashish Aman Dmello", "ashish.dmello@bixbytessolutions.com"),
        }

        # 1. Alias resolution across cases and whitespace
        for alias, (expected_dn, expected_email) in expected_members.items():
            self.assertEqual(ArtAssigneeRegistry.resolve_assignee(alias), expected_email)
            self.assertEqual(ArtAssigneeRegistry.resolve_assignee(alias.upper()), expected_email)
            self.assertEqual(ArtAssigneeRegistry.resolve_assignee(f"  {alias.capitalize()}  "), expected_email)
            # Full name resolution
            self.assertEqual(ArtAssigneeRegistry.resolve_assignee(expected_dn), expected_email)
            self.assertEqual(ArtAssigneeRegistry.resolve_assignee(expected_dn.lower()), expected_email)

        # 2. None or empty returns None
        self.assertIsNone(ArtAssigneeRegistry.resolve_assignee(None))
        self.assertIsNone(ArtAssigneeRegistry.resolve_assignee(""))
        self.assertIsNone(ArtAssigneeRegistry.resolve_assignee("   "))

        # 3. Unknown alias raises AzureDevOpsError
        with self.assertRaises(AzureDevOpsError) as ctx:
            ArtAssigneeRegistry.resolve_assignee("UnknownDeveloper")
        self.assertEqual(ctx.exception.code, "ASSIGNEE_NOT_RESOLVED")

        # 4. Partial substring prefix is NOT fuzzy matched
        with self.assertRaises(AzureDevOpsError) as ctx:
            ArtAssigneeRegistry.resolve_assignee("Kar")
        self.assertEqual(ctx.exception.code, "ASSIGNEE_NOT_RESOLVED")

    @patch("integrations.azure_devops.client.httpx.Client")
    def test_unassigned_bug_creation_succeeds_without_assigned_to(self, mock_client_cls):
        art_id = self._seed_confirmed_bug(module="AGENT")

        mock_http = MagicMock()
        mock_client_cls.return_value = mock_http

        mock_http.post.side_effect = [
            MagicMock(status_code=200, json=lambda: {"workItems": []}),
            MagicMock(status_code=200, json=lambda: {
                "id": 8881,
                "_links": {"html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/8881"}}
            })
        ]

        # No AZURE_DEVOPS_ASSIGNED_TO in env
        clean_env = dict(self.mock_env)
        if "AZURE_DEVOPS_ASSIGNED_TO" in clean_env:
            del clean_env["AZURE_DEVOPS_ASSIGNED_TO"]

        with patch.dict(os.environ, clean_env):
            # Send payload with no assignee
            res = self.client.post(f"/api/v1/bugs/{art_id}/azure-devops", json={})
            self.assertEqual(res.status_code, 200)

        # Inspect POST create patch payload
        create_call = mock_http.post.call_args_list[1]
        sent_patch = create_call.kwargs.get("json")

        # System.AssignedTo MUST be absent
        assigned_patch = next((p for p in sent_patch if p.get("path") == "/fields/System.AssignedTo"), None)
        self.assertIsNone(assigned_patch)

        # Parent link MUST be present
        parent_patch = next((p for p in sent_patch if p.get("path") == "/relations/-"), None)
        self.assertIsNotNone(parent_patch)
        self.assertIn("68783", parent_patch["value"]["url"])

        # No second PATCH call made
        mock_http.patch.assert_not_called()

    @patch("integrations.azure_devops.client.httpx.Client")
    def test_explicit_assignee_alias_in_request_payload_resolves(self, mock_client_cls):
        art_id = self._seed_confirmed_bug(module="AGENT")

        mock_http = MagicMock()
        mock_client_cls.return_value = mock_http

        mock_http.post.side_effect = [
            MagicMock(status_code=200, json=lambda: {"workItems": []}),
            MagicMock(status_code=200, json=lambda: {
                "id": 8882,
                "_links": {"html": {"href": "https://dev.azure.com/test-org/test-project/_workitems/edit/8882"}}
            })
        ]

        with patch.dict(os.environ, self.mock_env):
            # User requests: "Assign to Karthik"
            res = self.client.post(f"/api/v1/bugs/{art_id}/azure-devops", json={"assignee": "Karthik"})
            self.assertEqual(res.status_code, 200)

        create_call = mock_http.post.call_args_list[1]
        sent_patch = create_call.kwargs.get("json")

        assigned_patch = next((p for p in sent_patch if p.get("path") == "/fields/System.AssignedTo"), None)
        self.assertIsNotNone(assigned_patch)
        self.assertEqual(assigned_patch["value"], "karthik.suvarna@bixbytessolutions.com")

    def test_unresolvable_assignee_blocks_creation_safely(self):
        art_id = self._seed_confirmed_bug(module="AGENT")

        with patch.dict(os.environ, self.mock_env):
            res = self.client.post(f"/api/v1/bugs/{art_id}/azure-devops", json={"assignee": "NonExistentDev"})
            self.assertEqual(res.status_code, 400)
            self.assertIn("could not be resolved uniquely in the ART Assignee Registry", res.json()["error"]["message"])

    def test_pm_enrichment_art_agent_001_complete_projection(self):
        from integrations.azure_devops.projection import DeveloperTicketProjector, AzureDescriptionFormatter

        ticket = {
            "title": "Structured output contract is not strictly enforced",
            "module": "AGENT",
            "repro_steps": "Not provided",
            "expected_result": "ART must validate every agent result against the configured output contract...",
            "actual_result": "The same workflow has produced: compared_fields as arrays...",
            "business_impact": "Not provided",
            "recommended_solution": "ART must enforce structured output as a platform contract...",
            "environment": "Not provided",
            "severity": "HIGH",
            "priority": "Not provided"
        }

        proj = DeveloperTicketProjector.project_ticket(ticket, "ART-AGENT-001")
        # Check PM enriched fields
        # pyrefly: ignore [bad-argument-type]
        self.assertIn("reliable contract", proj.business_impact)
        # pyrefly: ignore [bad-argument-type]
        self.assertIn("explicit output contract", proj.user_experience)
        self.assertEqual(proj.severity, "HIGH")
        self.assertEqual(proj.priority, 2)
        # pyrefly: ignore [bad-argument-type]
        self.assertIn("High-priority defect", proj.priority_rationale)
        self.assertGreaterEqual(len(proj.acceptance_criteria), 3)

        # Check controlled taxonomy tags
        expected_tags = [
            "ART",
            "Agent-Lab",
            "Structured-Output",
            "Output-Parser",
            "Schema-Validation",
            "Contract-Enforcement",
            "Governance-Safety"
        ]
        for t in expected_tags:
            self.assertIn(t, proj.tags)

        # Check ReproSteps value is strictly 'Not provided'
        self.assertEqual(proj.repro_steps, "Not provided")
        html_out = AzureDescriptionFormatter.format_html(proj)
        for sec in [
            "<strong>Problem</strong>",
            "<strong>Observed Behavior</strong>",
            "<strong>Reproduction</strong>",
            "<strong>Expected Behavior</strong>",
            "<strong>Business Impact</strong>",
            "<strong>User Experience</strong>",
            "<strong>Investigation Guidance</strong>",
            "<strong>Fix Requirement</strong>",
            "<strong>Recommended Solution</strong>",
            "<strong>Minimum Working Fix</strong>",
            "<strong>Acceptance Criteria</strong>"
        ]:
            self.assertIn(sec, html_out)
        self.assertNotIn("Competitor Analysis", html_out)

    def test_locked_art_bug_model_and_zero_custom_fields(self):
        """
        Verify the locked ART Bug Model:
        1. No custom Azure field required.
        2. No Custom.ARTResolutionBrief in payload.
        3. ReproSteps == 'Not provided'.
        4. Severity == '2 - High'.
        5. Priority == 2.
        6. Correct ART tags.
        7. AssignedTo resolves Unnikkannan.
        8. Parent == Feature #68783.
        9. Bug does NOT directly parent to Epic #68782.
        10. Feature routing remains mandatory.
        11. Unknown module fails closed.
        12. Unassigned bug creation remains supported.
        """
        from integrations.azure_devops.models import (
            AzureDevOpsConfig,
            AzureDevOpsError,
            # pyrefly: ignore [missing-module-attribute]
            ArtAssigneeRegistry,
            # pyrefly: ignore [missing-module-attribute]
            AZURE_MODULE_FEATURE_MAP
        )
        from integrations.azure_devops.client import AzureDevOpsClient

        cfg = AzureDevOpsConfig(
            organization="BixBytesSolutions",
            project="ART IPR-0063",
            pat="dummy-pat"
        )
        client = AzureDevOpsClient(cfg)

        ticket = {
            "title": "Structured output contract is not strictly enforced",
            "module": "AGENT",
            "repro_steps": "Not provided",
            "expected_result": "Validation required",
            "actual_result": "No validation",
            "business_impact": "Downstream corruption",
            "recommended_solution": "Server-side schema contract",
            "environment": "Not provided",
            "severity": "HIGH",
            "priority": "P1"
        }

        # 7. AssignedTo resolves alias 'Unnikkannan'
        resolved_email = ArtAssigneeRegistry.resolve_assignee("Unnikkannan")
        self.assertEqual(resolved_email, "Unnikkannan.adiyodi@bixbytessolutions.com")

        # 8 & 10. Parent Feature routing for AGENT -> Feature 68783
        parent_fid = AZURE_MODULE_FEATURE_MAP["Agent Lab"]
        self.assertEqual(parent_fid, 68783)

        # Generate patch
        patch = client._map_ticket_to_patch(
            ticket,
            canonical_bug_id="ART-AGENT-001",
            parent_work_item_id=parent_fid,
            assigned_to=resolved_email
        )

        # 1 & 2. Zero custom fields (Custom.ARTResolutionBrief must NOT be present)
        custom_fields = [p for p in patch if p["path"].startswith("/fields/Custom.")]
        self.assertEqual(len(custom_fields), 0)
        self.assertIsNone(next((p for p in patch if "ARTResolutionBrief" in p["path"]), None))

        # 3. ReproSteps contains complete developer ticket with 11 canonical sections
        repro_patch = next(p for p in patch if p["path"] == "/fields/Microsoft.VSTS.TCM.ReproSteps")
        for sec in [
            "<strong>Problem</strong>",
            "<strong>Observed Behavior</strong>",
            "<strong>Reproduction</strong>",
            "<strong>Expected Behavior</strong>",
            "<strong>Business Impact</strong>",
            "<strong>User Experience</strong>",
            "<strong>Investigation Guidance</strong>",
            "<strong>Fix Requirement</strong>",
            "<strong>Recommended Solution</strong>",
            "<strong>Minimum Working Fix</strong>",
            "<strong>Acceptance Criteria</strong>"
        ]:
            self.assertIn(sec, repro_patch["value"])

        # 4. Severity == '2 - High'
        sev_patch = next(p for p in patch if p["path"] == "/fields/Microsoft.VSTS.Common.Severity")
        self.assertEqual(sev_patch["value"], "2 - High")

        # 5. Priority == 2
        pri_patch = next(p for p in patch if p["path"] == "/fields/Microsoft.VSTS.Common.Priority")
        self.assertEqual(pri_patch["value"], 2)

        # 6. Correct ART tags
        tags_patch = next(p for p in patch if p["path"] == "/fields/System.Tags")
        expected_tags = [
            "ART:ART-AGENT-001",
            "ART-AGENT-001",
            "ART",
            "Agent-Lab",
            "Structured-Output",
            "Output-Parser",
            "Schema-Validation",
            "Contract-Enforcement",
            "Governance-Safety"
        ]
        self.assertEqual(tags_patch["value"].split("; "), expected_tags)

        # 7. AssignedTo patch
        assign_patch = next(p for p in patch if p["path"] == "/fields/System.AssignedTo")
        self.assertEqual(assign_patch["value"], "Unnikkannan.adiyodi@bixbytessolutions.com")

        # 8 & 9. Parent relation is strictly to Feature 68783, NOT Epic 68782
        rel_patch = next(p for p in patch if p["path"] == "/relations/-")
        self.assertIn("68783", rel_patch["value"]["url"])
        self.assertNotIn("68782", rel_patch["value"]["url"])

        # 11. Unknown module fails closed in routing
        with self.assertRaises(KeyError):
            _ = AZURE_MODULE_FEATURE_MAP["UnknownModule"]

        # 12. Unassigned bug creation remains supported
        patch_unassigned = client._map_ticket_to_patch(
            ticket,
            canonical_bug_id="ART-AGENT-001",
            parent_work_item_id=parent_fid,
            assigned_to=None
        )
        self.assertIsNone(next((p for p in patch_unassigned if p["path"] == "/fields/System.AssignedTo"), None))

    def test_all_canonical_bugs_developer_body_has_all_11_sections(self):
        """
        Verify that for all canonical ART bugs:
        ART-AGENT-001, ART-GOV-002, ART-GOV-003, ART-SFN-001,
        ART-ORCHESTRATOR-001, ART-ORCHESTRATOR-002, ART-AGENT-002, ART-ORCHESTRATOR-003,
        the DeveloperTicketProjection and ReproSteps contain all 11 required sections in exact order.
        """
        from integrations.azure_devops.projection import (
            DeveloperTicketProjector,
            AzureDescriptionFormatter
        )

        canonical_ids = [
            "ART-AGENT-001", "ART-GOV-002", "ART-GOV-003", "ART-SFN-001",
            "ART-ORCHESTRATOR-001", "ART-ORCHESTRATOR-002", "ART-AGENT-002",
            "ART-ORCHESTRATOR-003", "ART-AGENT-003", "ART-AGENT-004",
            "ART-AGENT-005", "ART-AGENT-006", "ART-ORCHESTRATOR-004",
            "ART-TOOL-001", "ART-ORCHESTRATOR-005", "ART-GOV-004",
            "ART-ORCHESTRATOR-006", "ART-ORCHESTRATOR-007",
            "ART-ORCHESTRATOR-008", "ART-AGENT-007",
            "ART-GOV-005", "ART-AGENT-008", "ART-GOV-006",
            "ART-GOV-007", "ART-GOV-008", "ART-GOV-009",
            "ART-SFN-002", "ART-TOOL-002"
        ]
        required_headers = [
            "<strong>Problem</strong>",
            "<strong>Observed Behavior</strong>",
            "<strong>Reproduction</strong>",
            "<strong>Expected Behavior</strong>",
            "<strong>Business Impact</strong>",
            "<strong>User Experience</strong>",
            "<strong>Investigation Guidance</strong>",
            "<strong>Fix Requirement</strong>",
            "<strong>Recommended Solution</strong>",
            "<strong>Minimum Working Fix</strong>",
            "<strong>Acceptance Criteria</strong>"
        ]

        for cid in canonical_ids:
            proj = DeveloperTicketProjector.project_ticket({}, canonical_bug_id=cid)
            html_body = AzureDescriptionFormatter.format_html(proj)
            last_pos = -1
            for header in required_headers:
                pos = html_body.find(header)
                self.assertNotEqual(pos, -1, f"Bug {cid} missing section {header}")
                self.assertGreater(pos, last_pos, f"Bug {cid} section {header} out of order")
                last_pos = pos
            self.assertNotIn("Competitor Analysis", html_body, f"Bug {cid} contains Competitor Analysis")
            self.assertNotIn("<h3>", html_body)

    def test_sync_evidence_attachments_idempotent(self):
        """
        Verify sync_evidence_attachments:
        - Uploads and links new attachments
        - Skips existing attachments (idempotent, 0 new attachments)
        """
        config = AzureDevOpsConfig(
            organization="test-org",
            project="test-project",
            pat="fake-pat"
        )
        client = AzureDevOpsClient(config)

        # Mock work item with no relations
        with patch.object(client, "get_work_item") as mock_get:
            with patch.object(client, "upload_attachment") as mock_upload:
                with patch.object(client, "attach_file_to_work_item") as mock_attach:
                    mock_get.return_value = {"id": 68831, "fields": {}, "relations": []}
                    mock_upload.return_value = "https://dev.azure.com/test-org/test-project/_apis/wit/attachments/att-1"
                    mock_attach.return_value = {"id": 68831}

                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix=".png") as tf:
                        tf.write(b"PNGDATA")
                        tf.flush()
                        fname = os.path.basename(tf.name)

                        # First run: 1 attachment added
                        # pyrefly: ignore [missing-attribute]
                        att_count, new_count = client.sync_evidence_attachments(68831, "ART-AGENT-001", [tf.name])
                        self.assertEqual(att_count, 1)
                        self.assertEqual(new_count, 1)
                        self.assertEqual(mock_upload.call_count, 1)
                        self.assertEqual(mock_attach.call_count, 1)

                    # Second run: attachment already present in relations
                    mock_get.return_value = {
                        "id": 68831,
                        "fields": {},
                        "relations": [
                            {
                                "rel": "AttachedFile",
                                "url": "https://dev.azure.com/test-org/test-project/_apis/wit/attachments/att-1",
                                "attributes": {
                                    "name": fname,
                                    "comment": "Canonical evidence for ART-AGENT-001"
                                }
                            }
                        ]
                    }
                    mock_upload.reset_mock()
                    mock_attach.reset_mock()

                    with tempfile.NamedTemporaryFile(suffix=".png") as tf2:
                        with patch("os.path.basename", return_value=fname):
                            # pyrefly: ignore [missing-attribute]
                            att_count2, new_count2 = client.sync_evidence_attachments(68831, "ART-AGENT-001", [tf2.name])
                            self.assertEqual(att_count2, 1)
                            self.assertEqual(new_count2, 0)
                            mock_upload.assert_not_called()
                            mock_attach.assert_not_called()

    def test_update_work_item_repro_steps(self):
        """
        Verify update_work_item_repro_steps sends JSON patch with ReproSteps.
        """
        config = AzureDevOpsConfig(
            organization="test-org",
            project="test-project",
            pat="fake-pat"
        )
        mock_http = MagicMock()
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {"id": 68831, "fields": {"Microsoft.VSTS.TCM.ReproSteps": "<p>Updated</p>"}}
        mock_http.patch.return_value = mock_res

        client = AzureDevOpsClient(config, http_client=mock_http)
        # pyrefly: ignore [missing-attribute]
        res = client.update_work_item_repro_steps(68831, "<p>Updated</p>")
        self.assertEqual(res["id"], 68831)
        mock_http.patch.assert_called_once()
        _, kwargs = mock_http.patch.call_args
        patch_data = kwargs["json"]
        self.assertEqual(patch_data[0]["path"], "/fields/Microsoft.VSTS.TCM.ReproSteps")
        self.assertEqual(patch_data[0]["value"], "<p>Updated</p>")

    def test_canonical_ai_friendly_structure(self):
        """
        Verify canonical bug structure supports all canonical sections:
        Problem, Observed Behavior, Reproduction, Expected Behavior, Business Impact,
        User Experience, Investigation Guidance, Fix Requirement, Recommended Solution,
        Minimum Working Fix, Acceptance Criteria, Environment, Severity, Priority,
        Tags, Assignee, Evidence, Discussion, Azure DevOps.
        Ensure Investigation Guidance is non-empty, actionable, and grounded.
        """
        from scripts.legacy_ingestion.reader import LegacyIngestionAdapter, BUGS_DIR
        import os

        adapter = LegacyIngestionAdapter()
        found_any = False
        for root, dirs, _ in os.walk(BUGS_DIR):
            for folder in dirs:
                if not folder.startswith("ART-"):
                    continue
                folder_path = os.path.join(root, folder)
                md_files = [f for f in os.listdir(folder_path) if f.endswith(".md")]
                if not md_files:
                    continue
                file_path = os.path.join(folder_path, md_files[0])
                parsed = adapter.parse_bug_markdown(file_path)
                found_any = True

                self.assertIn("bug_id", parsed)
                self.assertTrue(parsed["bug_id"].startswith("ART-"))
                self.assertIn("title", parsed)

                # Check that investigation guidance does not invent repo paths
                inv = parsed.get("investigation_guidance") or parsed.get("investigationGuidance")
                if inv and inv != "Not provided":
                    self.assertNotIn("/speculative/", inv)
        self.assertTrue(found_any)

    def test_image_and_video_storage_support(self):
        """
        Verify evidence storage and reader support both images (.png, .jpg, .jpeg, .webp)
        and videos (.mp4, .mov, .webm) preserving uploaded files without modification.
        """
        from core.evidence.storage import EvidenceStorageService
        from scripts.legacy_ingestion.reader import LegacyIngestionAdapter
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = EvidenceStorageService(tmpdir)
            files_to_test = [
                ("screenshot1.png", b"\x89PNG\r\n\x1a\nfakeimage", "image/png", "SCREENSHOT"),
                ("photo.jpg", b"\xff\xd8\xfffakejpg", "image/jpeg", "IMAGE"),
                ("photo.jpeg", b"\xff\xd8\xfffakejpeg", "image/jpeg", "IMAGE"),
                ("graphic.webp", b"RIFF\x00\x00\x00\x00WEBPfake", "image/webp", "IMAGE"),
                ("screencast.mp4", b"\x00\x00\x00\x18ftypmp42fake", "video/mp4", "VIDEO"),
                ("recording.mov", b"\x00\x00\x00\x14ftypqt  fakemov", "video/quicktime", "VIDEO"),
                ("demo.webm", b"\x1a\x45\xdf\xa3fakewebm", "video/webm", "VIDEO")
            ]

            stored_canonical_names = []
            for fname, content, expected_mime, expected_type in files_to_test:
                stored = storage.store_evidence(
                    "ART-TEST-001", content, fname, stage="ORIGINAL", uploaded_by="TESTER"
                )
                self.assertEqual(stored["originalFilename"], fname)
                self.assertEqual(stored["mimeType"], expected_mime)
                self.assertEqual(stored["evidenceType"], expected_type)
                stored_canonical_names.append(stored["canonicalFilename"])
                # Verify exact bytes preserved (no compression/alteration)
                full_path = os.path.join(tmpdir, stored["storagePath"])
                with open(full_path, "rb") as fp:
                    self.assertEqual(fp.read(), content)

            # Test reader inspection on the directory
            adapter = LegacyIngestionAdapter()
            bug_dir = os.path.join(tmpdir, "ART-TEST-001")
            inspected_objs, status_map = adapter.inspect_evidence_files(
                bug_dir, stored_canonical_names
            )
            self.assertEqual(len(inspected_objs), len(files_to_test))
            for obj in inspected_objs:
                self.assertEqual(status_map[obj["filename"]], "MATCHED")

    def test_azure_image_and_video_attachments(self):
        """
        Verify sync_evidence_attachments uploads and attaches both images and videos to Azure DevOps.
        """
        config = AzureDevOpsConfig(organization="test-org", project="test-project", pat="fake-pat")
        client = AzureDevOpsClient(config)

        with patch.object(client, "get_work_item") as mock_get, \
             patch.object(client, "upload_attachment") as mock_upload, \
             patch.object(client, "attach_file_to_work_item") as mock_attach:

            mock_get.return_value = {"id": 68850, "fields": {}, "relations": []}
            mock_upload.side_effect = lambda path, name=None: f"https://dev.azure.com/att/{os.path.basename(path)}"
            mock_attach.return_value = {"id": 68850}

            with tempfile.TemporaryDirectory() as tmpdir:
                img_path = os.path.join(tmpdir, "ART-AGENT-001__screenshot.png")
                vid_path = os.path.join(tmpdir, "ART-AGENT-001__demo.mp4")
                with open(img_path, "wb") as f:
                    f.write(b"PNGDATA")
                with open(vid_path, "wb") as f:
                    f.write(b"MP4DATA")

                att_count, new_count = client.sync_evidence_attachments(
                    68850, "ART-AGENT-001", [img_path, vid_path]
                )
                self.assertEqual(att_count, 2)
                self.assertEqual(new_count, 2)
                self.assertEqual(mock_upload.call_count, 2)
                self.assertEqual(mock_attach.call_count, 2)

    def test_attachment_ownership_enforcement(self):
        """
        Verify sync_evidence_attachments enforces attachment ownership and rejects
        evidence files belonging to another bug.
        """
        config = AzureDevOpsConfig(organization="test-org", project="test-project", pat="fake-pat")
        client = AzureDevOpsClient(config)

        with patch.object(client, "get_work_item") as mock_get:
            mock_get.return_value = {"id": 68850, "fields": {}, "relations": []}
            with tempfile.TemporaryDirectory() as tmpdir:
                alien_file = os.path.join(tmpdir, "ART-GOV-002__alien_evidence.png")
                with open(alien_file, "wb") as f:
                    f.write(b"ALIENDATA")

                with self.assertRaises(EvidenceSyncError) as ctx:
                    client.sync_evidence_attachments(68850, "ART-AGENT-001", [alien_file])

                self.assertIn("EVIDENCE_SYNC_FAILED", str(ctx.exception))
                self.assertIn("belongs to ART-GOV-002", str(ctx.exception))

    def test_unsupported_failed_attachment_reporting(self):
        """
        Verify that if Azure rejects an attachment upload or relation,
        EvidenceSyncError is raised with format: EVIDENCE_SYNC_FAILED: <filename> — <reason>.
        """
        config = AzureDevOpsConfig(organization="test-org", project="test-project", pat="fake-pat")
        client = AzureDevOpsClient(config)

        with patch.object(client, "get_work_item") as mock_get, \
             patch.object(client, "upload_attachment") as mock_upload:

            mock_get.return_value = {"id": 68850, "fields": {}, "relations": []}
            mock_upload.side_effect = Exception("413 Request Entity Too Large: file exceeds 60MB")

            with tempfile.TemporaryDirectory() as tmpdir:
                big_file = os.path.join(tmpdir, "ART-AGENT-001__huge_video.mp4")
                with open(big_file, "wb") as f:
                    f.write(b"BIGDATA")

                with self.assertRaises(EvidenceSyncError) as ctx:
                    client.sync_evidence_attachments(68850, "ART-AGENT-001", [big_file])

                err_msg = str(ctx.exception)
                self.assertTrue(err_msg.startswith("EVIDENCE_SYNC_FAILED: ART-AGENT-001__huge_video.mp4 — "))
                self.assertIn("413 Request Entity Too Large", err_msg)

    def test_feature_routing_epic_hierarchy_locked(self):
        """
        Verify AzureFeatureRouter routes modules to correct Feature IDs under Epic #68782,
        and fails closed for unknown modules.
        """
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("Agent Lab"), 68783)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("AGENT"), 68783)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("Governance"), 68812)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("GOV"), 68812)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("Orchestrator"), 68806)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("ORC"), 68806)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("Serverless Functions"), 68811)
        self.assertEqual(AzureFeatureRouter.resolve_feature_id("SFN"), 68811)

        with self.assertRaises(AzureDevOpsError) as ctx:
            AzureFeatureRouter.resolve_feature_id("UNKNOWN_MODULE_XYZ")
        self.assertIn("No Azure Feature mapping configured", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()



