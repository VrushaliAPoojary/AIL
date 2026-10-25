# GitHub MVP Persistence

## Current purpose

GitHub is used as the MVP durable persistence layer for contributor profiles, contributions, and activity records.
The application keeps the browser free of privileged credentials by routing writes through the Next.js server API.

Target flow:

```text
Browser
↓
AIL Next API
↓
InvestigationStore
↓
GitHubInvestigationStore
↓
Private GitHub data repository
```

## Good fit

- low-volume collaboration
- append-oriented research contributions
- auditable change history
- simple versioned JSON records

## Poor fit

- high-frequency realtime events
- relational querying
- large file binaries
- complex filtering
- large user volumes
- high write concurrency

## Storage shape

Each record is stored as one JSON file:

```text
data/
├── contributors/
│   └── <contributor-id>.json
├── contributions/
│   └── <contribution-id>.json
└── activity/
    └── <event-id>.json
```

## Future replacement

Because the application depends on `InvestigationStore`, the backing store can later be replaced with something like `PostgresInvestigationStore` without rewriting the onboarding and contribution flows.

## Security boundary

GitHub credentials remain server-only through environment variables and never reach the browser.
