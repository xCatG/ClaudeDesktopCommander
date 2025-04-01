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