# Code Style Guidelines

## Code Style Constraints

- Follow PEP 8 style guide for Python code
- Use snake_case for variable and function names
- Use PascalCase for class names
- Use UPPER_CASE for constants
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 120 characters
- Every function MUST have type hints for all parameters and return values
- Use proper docstrings with Args/Returns sections for functions and classes

## Framework Constraints

### FastAPI
- Use dependency injection pattern with `Depends()`
- Use Pydantic v2+ models for request/response validation
- Use `pydantic-settings.BaseSettings` for configuration management
- Use async/await pattern for route handlers
- Use proper HTTP status codes (e.g., 200, 201, 404, 500)
- Use `BackgroundTasks` for async background operations
- Use `APIRouter` for modular route organization

### Pydantic
- Use Pydantic v2+ features (e.g., `computed_field`, `model_serializer`)
- Use `Field()` with proper validation rules
- Use `ConfigDict` class for model configuration
- Use `pydantic_settings.BaseSettings` for environment-based config

### LangChain & LangGraph
- Use `langchain_openai` for OpenAI integration
- Use `langchain_anthropic` for Claude integration
- Use `langchain-google-genai` for Google AI integration
- Use `langgraph` for stateful, multi-agent workflows
- Use `chainlit` for chat UI when applicable
- Use proper prompt templates with variable binding

### Database
- Use `motor` (async MongoDB driver) for async DB operations
- Use `pymongo` for synchronous operations when needed
- Use `redis` for caching with proper connection pooling
- Use connection context managers for DB operations

### Async/Await
- Use `httpx` for async HTTP requests
- Use `aiofiles` for async file operations
- Always use `async def` for async functions
- Use `async with` for async context managers
- Use `async for` for async iteration

### Task Scheduling
- Use `APScheduler` for cron-like scheduling
- Use proper job error handling
- Use persistent job stores for critical tasks

### Data Processing
- Use `pandas` with proper data typing
- Use `plotly` for visualizations
- Use `pytz` for timezone-aware datetime handling

### Logging
- Use `concurrent-log-handler` for cross-platform log rotation
- Use proper log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Include contextual information in log messages



## Code Comments Constraints

- All code comments and docstrings MUST be in English only
- Use triple quotes for docstrings
- Every function MUST have: function description, Args section, and Returns section in docstring
- Include Args section for function parameters
- Include Returns section for return values
- Keep comments concise and meaningful

## Pylint Constraints

- Target score: >= 9.0
- Enable all common pylint checks
- Disable unused imports warnings with justification
- Follow naming conventions (C0103, C0111, C0115, C0116)
- Use `# pylint: disable=<error-code>` sparingly with comments explaining why

## Testing Virtual Environment Constraints

- Use the project's virtual environment located at `./venv`
- Activate with: `source ./venv/bin/activate` (macOS/Linux)
- Run pytest with: `pytest`
- Install test dependencies in the virtual environment
- Ensure tests are isolated and repeatable
