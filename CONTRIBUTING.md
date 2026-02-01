# Contributing to Descope Skills

Thank you for your interest in contributing to Descope Skills! This document provides guidelines for contributing new skills or improving existing ones.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/skills.git`
3. Create a feature branch: `git checkout -b add-new-skill`
4. Make your changes
5. Test with an AI agent
6. Submit a pull request

## Skill Format

All skills must follow the [Agent Skills specification](https://agentskills.io/). At minimum, a skill requires:

### Directory Structure

```
your-skill-name/
├── SKILL.md              # Required: Main skill instructions
└── references/           # Optional: Supporting documentation
    ├── guide1.md
    └── guide2.md
```

### SKILL.md Frontmatter

```yaml
---
name: your-skill-name
description: Brief description of what the skill does and when to use it
---
```

**Requirements:**
- `name`: lowercase with hyphens (e.g., `descope-auth`)
- `description`: Clear trigger phrases for when AI should use this skill
- **Do NOT include**: `author`, `version`, `tags`, or other metadata fields

### Content Guidelines

1. **Use imperative form**: "To install, run..." NOT "You should install..."
2. **Be specific**: Include exact commands, imports, and code examples
3. **Prevent hallucination**: Provide exhaustive lists (e.g., all valid API methods)
4. **Add guardrails**: Include "DO NOT" section for security/correctness
5. **Keep concise**: Under 5,000 words total per skill
6. **Test thoroughly**: Verify all code examples work with latest SDK versions

### Example Structure

```markdown
---
name: my-skill
description: Use when implementing X or Y. Supports frameworks A, B, C.
---

# My Skill

Brief introduction to the skill.

## When to Use

- Task A
- Task B
- Task C

## Quick Start

1. Install: `npm install package`
2. Configure: Set environment variable
3. Use: Import and call function

## Framework Detection

| If project has... | Use reference |
|-------------------|---------------|
| framework A | `references/framework-a.md` |
| framework B | `references/framework-b.md` |

## Code Examples

\`\`\`typescript
import { Function } from 'package';

// Exact, working example
const result = Function({ option: 'value' });
\`\`\`

## DO NOT

- DO NOT do insecure thing X
- DO NOT skip validation step Y
- DO NOT use deprecated pattern Z
```

## Testing Your Skill

Before submitting:

1. **Format validation**:
   ```bash
   # Verify frontmatter
   grep -q "^name:" your-skill/SKILL.md
   grep -q "^description:" your-skill/SKILL.md
   
   # Check word count
   wc -w your-skill/**/*.md
   ```

2. **Install locally**:
   ```bash
   npx skills add ./your-skill
   ```

3. **Test with AI agent**:
   - Install skill in your preferred agent
   - Ask agent to perform tasks covered by the skill
   - Verify agent uses correct patterns and code examples

## Pull Request Guidelines

### PR Title

Use conventional commits format:
- `feat: add new-skill-name`
- `fix: correct SDK import in skill-name`
- `docs: update README with new skill`

### PR Description

Use this template:

```markdown
## Related Issues

Fixes #123 (if applicable)

## Description

Brief description of the skill and what it helps agents do.

## Testing

- [ ] Verified frontmatter format
- [ ] Tested code examples work
- [ ] Installed locally with `npx skills add`
- [ ] Tested with AI agent (specify which: Claude Code, Cursor, etc.)

## Checklist

- [ ] Follows Agent Skills specification
- [ ] Uses imperative form throughout
- [ ] Includes "DO NOT" security section
- [ ] Word count under 5,000
- [ ] All code examples tested
- [ ] Updated main README.md
```

## Code of Conduct

- Be respectful and constructive
- Focus on the skill quality, not the person
- Assume good intent
- Help others learn

## Questions?

- Join [Descope Community Slack](https://www.descope.com/community)
- Open a [GitHub Discussion](https://github.com/descope/skills/discussions)
- Email: support@descope.com

Thank you for contributing! 🙏
