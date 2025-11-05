# Documentation Creation Policy

## Rule: Only create documentation when explicitly requested

**IMPORTANT:** Do NOT proactively create documentation files unless the user explicitly asks for them.

### What NOT to create automatically:
- ❌ README.md files
- ❌ SUMMARY.md files
- ❌ Documentation in Markdown format
- ❌ Project overview documents
- ❌ Architecture diagrams in files
- ❌ CHANGELOG.md
- ❌ Any other .md files

### When TO create documentation:
- ✅ User explicitly says: "create a README"
- ✅ User explicitly says: "write documentation"
- ✅ User explicitly says: "document this"
- ✅ User asks: "can you create a summary?"

### What you CAN do without asking:
- ✅ Write code
- ✅ Fix bugs
- ✅ Refactor
- ✅ Add comments in code (when appropriate)
- ✅ Explain things verbally in chat
- ✅ Answer questions

### Examples:

**❌ BAD (don't do this):**
```
User: "I fixed the authentication bug"
Assistant: "Great! Let me create a SUMMARY.md to document this change..."
```

**✅ GOOD (do this instead):**
```
User: "I fixed the authentication bug"
Assistant: "Great! The fix looks good. Is there anything else you'd like me to help with?"
```

**✅ GOOD (user explicitly asks):**
```
User: "Can you create a README for this project?"
Assistant: "Sure! I'll create a README.md with project overview..."
```

## Rationale

- Users prefer to control when documentation is created
- Unsolicited documentation files clutter the project
- Users will ask for documentation when they need it
- Focus on code and functionality first

## Exception

The ONLY exception is when writing production code that REQUIRES documentation by industry standards (e.g., public APIs, libraries meant for distribution). Even then, ask first: "Should I add documentation for this API?"
