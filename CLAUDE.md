# Claude Desktop Commander Guidelines

## Commands

### TypeScript
- Build: `npm run build`
- Test: `npm test`
- Install: `npm install`
- Setup: `npm run setup`

### Python
- Install: `pip install -e .`
- Setup: `python -m desktop_commander.main setup` or `desktop-commander-py-setup`
- Test project tools: `python scripts/test_project_tools.py`

## Code Style Guidelines

### TypeScript
- Use strict TypeScript typing
- Follow ES2020 standards with Node16 module system
- Use async/await for asynchronous operations
- Handle errors with try/catch blocks
- Use camelCase for variables/functions and PascalCase for classes/interfaces

### Python
- Python 3.10+ required
- Use type hints consistently
- Use Pydantic for data validation and models
- Follow PEP 8 conventions
- Use snake_case for variables/functions and PascalCase for classes
- Error handling with try/except and proper logging

## File Editing Tools

The codebase provides several tools for editing files with different approaches:

### 1. edit_block Tool
- Token-intensive as it requires full search text and replacement text
- Useful for precise replacements when exact content is known
- Example: `edit_block(file="proj:src/file.js", search="function hello() {...}", replace="function hello() {...}")`

### 2. edit_range Tool
- More token-efficient, requires only line numbers and new content
- Doesn't require sending the original content to be replaced
- Good for replacing, adding, or removing whole sections of a file
- Examples:
  - Replace lines 5-10: `edit_range(file="proj:src/app.js", start_line=5, end_line=10, new_content="...")`
  - Insert between lines: `edit_range(file="proj:src/utils.py", start_line=15, end_line=15, new_content="...")`
  - Delete lines: `edit_range(file="proj:src/config.json", start_line=7, end_line=9, new_content="")`

### 3. edit_by_patch Tool
- Most token-efficient, uses unified diff format
- Only requires sending the differences between files
- Implementation uses a custom patch parser to handle unified diff format
- Example:
```
edit_by_patch(
    file="proj:src/utils.js",
    patch='''@@ -10,7 +10,7 @@
 function hello() {
-  console.log('hello');
+  console.log('hello world');
   return true;
 }
'''
)
```

### Findings on Patch Implementation

1. **Unified Diff Format**:
   - Most token-efficient format for making edits
   - Standard format supported by git and other tools
   - Format: `@@ -start,count +start,count @@` followed by context lines
   - Lines starting with `-` are deletions, `+` are additions, space for context

2. **Implementation Considerations**:
   - Custom parser is more reliable than external libraries in this context
   - Using Python's built-in `difflib` for creating diffs works well
   - Handling line endings and file encodings properly is critical
   - Apply hunks in reverse order to avoid line number changes affecting later edits

3. **Best Practices**:
   - Always include enough context (unchanged lines) for proper patch application
   - Show clear before/after diffs when reporting changes
   - Validate patch format before attempting to apply
   - Provide helpful error messages for common patch issues