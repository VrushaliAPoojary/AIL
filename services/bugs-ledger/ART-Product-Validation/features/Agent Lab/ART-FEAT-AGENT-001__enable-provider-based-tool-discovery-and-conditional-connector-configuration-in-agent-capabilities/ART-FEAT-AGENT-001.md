# ART-FEAT-AGENT-001 — Enable Provider-Based Tool Discovery and Conditional Connector Configuration in Agent Capabilities

- **Module:** Agent Lab
- **Classification:** ENHANCEMENT
- **Status:** PROPOSED
- **Priority:** P2
- **Azure Work Item ID:** #69198
- **Azure Sync Status:** SYNCED

## Problem / Opportunity

Agent Capability tool selection currently depends on enabling a connector before the associated provider's tools become available. This creates an unnecessary dependency for tools that do not require an external connector. As a result, users may be unable to discover or configure otherwise available tools when no connector exists.

## Current Behavior

Agent Capability tool selection depends on enabling a connector before the associated provider's tools become available. Tools cannot be discovered or configured without an existing connector, even if the tools do not require external authorization.

## Proposed Behavior

The Agent Capability interface should display available tool providers independently of connector configuration. When a user selects a provider, ART should display its available tools and determine the requirements for each tool. Tools that do not require a connector should be directly selectable. Tools that require a connector should retain the existing connector selection and authorization workflow.

## Business Impact

Improves tool discoverability, reduces unnecessary configuration steps, and enables broader use of available agent capabilities.

## User Experience

Users can browse providers and select tools without first creating unnecessary connectors. When a tool requires authorization, ART guides users through the existing connection process.

## Acceptance Criteria

1. Agent Capability displays all providers available to the current workspace, including providers without configured connectors.
2. Selecting a provider displays its available tools.
3. Tools requiring no connector can be added directly.
4. Tools requiring a connector prompt users to select or configure a valid connection.
5. Tools cannot be executed without their required credentials or permissions.
6. Existing connector-based tools continue functioning without regression.
7. Provider and tool visibility respects workspace permissions.
8. Saving and reopening an agent preserves its configured tools and connector associations.

## Implementation Guidance

Introduce or reuse tool-level connection requirements rather than relying solely on provider-level connector existence (e.g., NO_CONNECTION_REQUIRED, CONNECTION_REQUIRED). Do not change the backend data model until the existing ART capability and connector architecture has been inspected.

## Related Bugs / Dependencies

None identified.

## Evidence and Provenance

- **Provenance:** HUMAN_SUPPLIED
- **Created At:** 2026-10-13T05:08:33.152364+00:00
- **Updated At:** 2026-10-13T05:10:01.843512+00:00
- **Evidence Files:** None attached.
