# Mycelium Dual-Purpose Architecture Diagrams

## Table of Contents

1. [Overall Structure](#overall-structure)
1. [Installation Flows](#installation-flows)
1. [User Interaction Models](#user-interaction-models)
1. [Plugin Relationships](#plugin-relationships)
1. [Community Ecosystem](#community-ecosystem)

______________________________________________________________________

## Overall Structure

### Repository Layout (Before & After)

#### Before: Single-Purpose Plugin

```
mycelium/
├── agents/
│   ├── 01-core-development/
│   ├── 02-language-specialists/
│   ├── ... (11 categories)
├── commands/
│   ├── infra-check.md
│   ├── team-status.md
│   └── pipeline-status.md
├── hooks/
├── lib/
├── docs/
├── tests/
├── README.md
├── INSTALL.md
└── package.json

Purpose: Single Claude Code plugin
Installation: Direct git clone or symlink
```

#### After: Dual-Purpose (Plugin + Marketplace)

```
mycelium/
├── .claude-plugin/                    # MARKETPLACE METADATA
│   └── marketplace.json               # Registry of all plugins
├── plugins/                           # PLUGIN COLLECTION
│   ├── mycelium-core/                 # Core plugin
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json            # Plugin metadata
│   │   ├── agents/
│   │   │   ├── 01-core-development/
│   │   │   ├── 02-language-specialists/
│   │   │   └── ... (11 categories)
│   │   ├── commands/
│   │   │   ├── infra-check.md
│   │   │   ├── team-status.md
│   │   │   └── pipeline-status.md
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── README.md
│   ├── mycelium-voice-kit/            # Future: Domain plugin
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   └── agents/
│   └── [community-plugins]/           # Community contributions
├── docs/
│   ├── patterns/
│   ├── examples/
│   └── marketplace/                   # NEW: Marketplace docs
│       ├── SUBMISSION_GUIDE.md
│       └── PLUGIN_DEVELOPMENT.md
├── tests/
├── README.md                          # Updated for dual purpose
├── MARKETPLACE_README.md              # NEW: Marketplace focus
├── INSTALL.md                         # Updated installation guide
├── CONTRIBUTING.md
└── package.json

Purpose: Plugin marketplace + core plugin
Installation: Via marketplace OR direct plugin install
```

______________________________________________________________________

## Installation Flows

### Flow 1: Marketplace Installation (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│                    User's Claude Code                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Step 1: Add marketplace
                 │ /plugin marketplace add gsornsen/mycelium
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Marketplace Registry (Local)                    │
│  ~/.claude/plugins/marketplaces/mycelium/                   │
│      - marketplace.json (synced)                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Step 2: Browse plugins
                 │ /plugin
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Plugin Selection Interface                      │
│  Shows:                                                      │
│    - mycelium-core (130+ agents, coordination)             │
│    - [future community plugins]                             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Step 3: Install plugin
                 │ /plugin install mycelium-core@mycelium
                 ▼
┌─────────────────────────────────────────────────────────────┐
│            Plugin Installation (Local)                       │
│  ~/.claude/plugins/mycelium-core/                           │
│      - Downloaded from GitHub                               │
│      - Agents, commands, hooks active                       │
└─────────────────────────────────────────────────────────────┘
                 │
                 │ Step 4: Use functionality
                 │ /infra-check, /team-status
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   Plugin Active                              │
│  All agents, commands, and hooks available                  │
└─────────────────────────────────────────────────────────────┘
```

### Flow 2: Direct Plugin Installation

```
┌─────────────────────────────────────────────────────────────┐
│                    User's Claude Code                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Single command installation
                 │ claude plugin install \
                 │   git+https://github.com/gsornsen/mycelium.git#plugins/mycelium-core
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Direct Git Clone                                │
│  Fetches: plugins/mycelium-core/ only                       │
│  Installs to: ~/.claude/plugins/mycelium-core/              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Automatic
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   Plugin Active                              │
│  All agents, commands, and hooks available                  │
│  (No marketplace functionality)                             │
└─────────────────────────────────────────────────────────────┘
```

### Flow 3: Development Installation

```
┌─────────────────────────────────────────────────────────────┐
│                Developer's Machine                           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Step 1: Clone full repository
                 │ git clone https://github.com/gsornsen/mycelium.git
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Local Repository                                │
│  /home/gerald/git/mycelium/                                 │
│    - Full source code                                       │
│    - All plugins                                            │
│    - Development tools                                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Step 2: Create symlink
                 │ ln -s $(pwd)/plugins/mycelium-core \
                 │       ~/.claude/plugins/mycelium-core
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Symlinked Plugin                                │
│  ~/.claude/plugins/mycelium-core → /home/.../mycelium/.../  │
│    - Live updates                                           │
│    - Hot reloading                                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Step 3: Edit and test
                 │ Changes reflect immediately
                 ▼
┌─────────────────────────────────────────────────────────────┐
│            Development Workflow                              │
│  Edit → Test → Commit → Push → Share                        │
└─────────────────────────────────────────────────────────────┘
```

______________________________________________________________________

## User Interaction Models

### Persona 1: End User (Wants functionality)

```
┌─────────────────────────────────────────────────────────────┐
│                        End User                              │
│  "I want Claude Code to help with multi-agent workflows"    │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Discovery
                 ▼
┌─────────────────────────────────────────────────────────────┐
│           Finds Mycelium on GitHub/Marketplace               │
└────────────────┬────────────────────────────────────────────┘
                 │
           ┌─────┴─────┐
           │           │
    Option A       Option B
    Marketplace    Direct Install
           │           │
           ▼           ▼
    ┌───────────┐ ┌───────────┐
    │ Add       │ │ Install   │
    │ Market-   │ │ Plugin    │
    │ place     │ │ Directly  │
    └─────┬─────┘ └─────┬─────┘
          │             │
          │             │
          └──────┬──────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│              Plugin Installed & Active                       │
│  Uses: /infra-check, /team-status, agents                   │
└─────────────────────────────────────────────────────────────┘
```

### Persona 2: Plugin Developer (Wants to contribute)

```
┌─────────────────────────────────────────────────────────────┐
│                    Plugin Developer                          │
│  "I want to create a specialized Mycelium plugin"           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Step 1: Research
                 ▼
┌─────────────────────────────────────────────────────────────┐
│         Read MARKETPLACE_README.md                           │
│         Review docs/marketplace/                             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Step 2: Development
                 ▼
┌─────────────────────────────────────────────────────────────┐
│      Fork Repository → Create Plugin                         │
│         plugins/my-plugin/                                   │
│           .claude-plugin/plugin.json                         │
│           agents/                                            │
│           commands/                                          │
│           README.md                                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Step 3: Test locally
                 ▼
┌─────────────────────────────────────────────────────────────┐
│      Symlink & Test                                          │
│        ln -s plugins/my-plugin ~/.claude/plugins/            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Step 4: Submit
                 ▼
┌─────────────────────────────────────────────────────────────┐
│      Create PR                                               │
│        - Add plugin to marketplace.json                      │
│        - Include documentation                               │
│        - Pass quality checks                                 │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Step 5: Review & Merge
                 ▼
┌─────────────────────────────────────────────────────────────┐
│      Plugin Available in Marketplace                         │
│        All users can discover and install                    │
└─────────────────────────────────────────────────────────────┘
```

### Persona 3: Mycelium Core Developer

```
┌─────────────────────────────────────────────────────────────┐
│                 Mycelium Core Developer                      │
│  "I'm maintaining and enhancing Mycelium core"              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Step 1: Clone full repo
                 ▼
┌─────────────────────────────────────────────────────────────┐
│      Full Repository Access                                  │
│        - All plugins                                         │
│        - Marketplace metadata                                │
│        - Documentation                                       │
│        - Tests                                               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Step 2: Work on core
                 ▼
┌─────────────────────────────────────────────────────────────┐
│      Edit plugins/mycelium-core/                             │
│        - Agents                                              │
│        - Commands                                            │
│        - Coordination library                                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Step 3: Test across ecosystem
                 ▼
┌─────────────────────────────────────────────────────────────┐
│      Ensure compatibility                                    │
│        - Test with other plugins                            │
│        - Verify marketplace installation                     │
│        - Run integration tests                              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Step 4: Release
                 ▼
┌─────────────────────────────────────────────────────────────┐
│      Version Bump & Publish                                  │
│        - Update plugin.json version                         │
│        - Update marketplace.json                            │
│        - Tag release                                        │
│        - All users get update                               │
└─────────────────────────────────────────────────────────────┘
```

______________________________________________________________________

## Plugin Relationships

### Coordination Substrate Model

```
┌────────────────────────────────────────────────────────────────┐
│                     Application Layer                          │
│                      (User Requests)                           │
└───────────────────────────┬────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
    ┌──────────────┐ ┌──────────┐ ┌──────────────┐
    │ mycelium-    │ │Community │ │   Future     │
    │    core      │ │ Plugin 1 │ │ Plugins...   │
    │              │ │          │ │              │
    │ 130+ agents  │ │Specialist│ │   Domain     │
    │ Commands     │ │  Agents  │ │  Specific    │
    │ Hooks        │ │          │ │              │
    └──────┬───────┘ └─────┬────┘ └──────┬───────┘
           │               │              │
           └───────────────┼──────────────┘
                           │
                           │ All plugins can use
                           ▼
    ┌──────────────────────────────────────────────┐
    │     Coordination Substrate (lib/)            │
    │  - CoordinationClient                        │
    │  - WorkflowClient                            │
    │  - Event Publishing/Subscription             │
    └───────────────────┬──────────────────────────┘
                        │
              ┌─────────┼─────────┐
              ▼         ▼         ▼
         ┌────────┐ ┌───────┐ ┌─────────┐
         │ Redis  │ │TaskQueue│ │Markdown│
         │  MCP   │ │  MCP   │ │ Files  │
         └────────┘ └────────┘ └─────────┘
```

### Plugin Dependency Graph

```
mycelium-core (Foundation)
    │
    ├─→ Provides: Coordination substrate
    │             Agent patterns
    │             Hook system
    │             Command patterns
    │
    └─→ Used by: mycelium-voice-kit
                 mycelium-web3
                 mycelium-homelab
                 [community plugins]

Example: Voice Kit Plugin
┌────────────────────────────────┐
│     mycelium-voice-kit         │
│  Specialized voice agents      │
└────────────────┬───────────────┘
                 │
                 │ Depends on
                 ▼
┌────────────────────────────────┐
│       mycelium-core            │
│  - Uses CoordinationClient     │
│  - Reports to orchestrator     │
│  - Publishes events            │
└────────────────────────────────┘
```

______________________________________________________________________

## Community Ecosystem

### Growth Model

```
Phase 1: Launch (v1.1.0)
┌────────────────────────────────┐
│  Marketplace Infrastructure    │
│    - mycelium-core only        │
│    - Submission process ready  │
└────────────────────────────────┘

Phase 2: Early Adoption (Weeks 1-4)
┌────────────────────────────────┐
│  First Community Plugins       │
│    - mycelium-core             │
│    - 2-3 community plugins     │
│    - Feedback collection       │
└────────────────────────────────┘

Phase 3: Growth (Months 2-3)
┌────────────────────────────────┐
│  Expanding Ecosystem           │
│    - mycelium-core             │
│    - 10+ community plugins     │
│    - Quality standards refined │
│    - Active community          │
└────────────────────────────────┘

Phase 4: Maturity (Months 4+)
┌────────────────────────────────┐
│  Vibrant Marketplace           │
│    - mycelium-core             │
│    - 25+ specialized plugins   │
│    - Domain coverage           │
│    - Self-sustaining community │
└────────────────────────────────┘
```

### Plugin Categories (Future Vision)

```
Mycelium Marketplace
├── Core
│   └── mycelium-core (Official)
│
├── Development
│   ├── mycelium-web3 (Blockchain specialists)
│   ├── mycelium-game-dev (Game development agents)
│   └── mycelium-mobile (iOS/Android experts)
│
├── Data & AI
│   ├── mycelium-voice-kit (Voice cloning & TTS)
│   ├── mycelium-cv (Computer vision specialists)
│   └── mycelium-nlp (NLP/LLM workflows)
│
├── Infrastructure
│   ├── mycelium-homelab (Home lab automation)
│   ├── mycelium-cloud (Multi-cloud management)
│   └── mycelium-k8s-extended (Advanced K8s ops)
│
├── Domain Specific
│   ├── mycelium-research (Academic workflows)
│   ├── mycelium-legal (Legal document analysis)
│   └── mycelium-medical (Healthcare compliance)
│
└── Workflow Tools
    ├── mycelium-reporting (Automated reports)
    ├── mycelium-testing (Advanced test suites)
    └── mycelium-deployment (CD pipelines)
```

### Contribution Flywheel

```
                  ┌──────────────┐
                  │  User finds  │
                  │   problem    │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │Creates custom│
                  │    agent     │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  Packages as │
                  │    plugin    │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  Submits to  │
                  │ marketplace  │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │Other users   │
                  │  discover    │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  They install│
                  │  and improve │
                  └──────┬───────┘
                         │
                         └──────→ Back to top
```

______________________________________________________________________

## Comparison: Single vs Dual Purpose

### Single-Purpose Plugin

```
User
  │
  │ Discovers Mycelium
  ▼
Clone/Install
  │
  │ One option only
  ▼
Use Mycelium
  │
  │ Limited extensibility
  ▼
Fork if customization needed
```

**Limitations:**

- No plugin discovery mechanism
- Customizations remain private
- No community ecosystem
- One-size-fits-all approach

### Dual-Purpose (Plugin + Marketplace)

```
User
  │
  │ Discovers Mycelium
  ▼
┌───────────────┐
│  Installation │
│    Choice     │
└───┬───────┬───┘
    │       │
Marketplace Direct
    │       │
    ▼       ▼
 Browse   Core
Plugins   Only
    │       │
    └───┬───┘
        │
        ▼
  Use Mycelium
        │
    ┌───┴───┐
    │       │
Satisfied Create
    │     Plugin
    │       │
    │       ▼
    │   Submit
    │       │
    │       ▼
    │  Community
    │   Benefits
    │       │
    └───────┘
```

**Benefits:**

- Multiple installation paths
- Plugin discovery built-in
- Community contributions
- Ecosystem growth
- Specialized solutions
- Network effects

______________________________________________________________________

## Technical Architecture

### File Resolution Flow

```
User executes: /infra-check
                │
                ▼
┌───────────────────────────────────────┐
│ Claude Code Runtime                   │
│   - Looks in ~/.claude/plugins/       │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│ Plugin: mycelium-core                 │
│   Location: ~/.claude/plugins/        │
│           mycelium-core/              │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│ Read: .claude-plugin/plugin.json      │
│   "commands": "./commands/"           │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│ Load: commands/infra-check.md         │
│   Parse YAML frontmatter              │
│   Execute command logic               │
└───────────────────────────────────────┘
```

### Marketplace Sync Flow

```
User: /plugin marketplace add gsornsen/mycelium
                │
                ▼
┌───────────────────────────────────────┐
│ Claude Code fetches:                  │
│   .claude-plugin/marketplace.json     │
│   from GitHub repo                    │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│ Store locally:                        │
│   ~/.claude/plugins/marketplaces/     │
│        mycelium/marketplace.json      │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│ Parse marketplace.json                │
│   Extract plugin list                 │
│   Cache metadata                      │
└───────────────┬───────────────────────┘
                │
                ▼
User: /plugin
                │
                ▼
┌───────────────────────────────────────┐
│ Display available plugins:            │
│   - mycelium-core                     │
│   - [other plugins]                   │
└───────────────────────────────────────┘
```

______________________________________________________________________

## Summary Diagram: Complete System

```
┌──────────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                             │
│                    github.com/gsornsen/mycelium                        │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ .claude-plugin/marketplace.json                            │    │
│  │   - Marketplace metadata                                   │    │
│  │   - Plugin registry                                        │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ plugins/                                                    │    │
│  │   ├── mycelium-core/                                       │    │
│  │   │     ├── .claude-plugin/plugin.json                     │    │
│  │   │     ├── agents/ (130+ agents)                          │    │
│  │   │     ├── commands/ (/infra-check, /team-status)         │    │
│  │   │     ├── hooks/                                         │    │
│  │   │     └── lib/ (coordination.js, workflow.js)            │    │
│  │   │                                                         │    │
│  │   └── [community-plugins]/                                 │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ docs/marketplace/                                           │    │
│  │   - Submission guides                                       │    │
│  │   - Development guidelines                                  │    │
│  │   - Quality standards                                       │    │
│  └────────────────────────────────────────────────────────────┘    │
└──────────────────────┬───────────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          │                         │
    Installation            Installation
    Method 1                Method 2
          │                         │
          ▼                         ▼
┌─────────────────────┐   ┌─────────────────────┐
│  Via Marketplace    │   │  Direct Plugin      │
│  /plugin market-    │   │  claude plugin      │
│  place add          │   │  install git+...    │
└──────────┬──────────┘   └──────────┬──────────┘
           │                         │
           └────────────┬────────────┘
                        │
                        ▼
           ┌────────────────────────┐
           │ User's Claude Code     │
           │ ~/.claude/plugins/     │
           │   mycelium-core/       │
           └────────────────────────┘
                        │
                        ▼
           ┌────────────────────────┐
           │    Functionality       │
           │  - 130+ agents         │
           │  - Slash commands      │
           │  - Coordination        │
           │  - Workflows           │
           └────────────────────────┘
```

______________________________________________________________________

## Conclusion

This dual-purpose architecture provides:

1. **Flexibility** - Multiple installation methods for different user needs
1. **Scalability** - Easy to add community plugins
1. **Maintainability** - Clear separation of concerns
1. **Discoverability** - Built-in marketplace for plugin discovery
1. **Community** - Enables ecosystem growth through contributions

The structure follows established Claude Code patterns while extending them to support the Mycelium philosophy of
distributed intelligence.
