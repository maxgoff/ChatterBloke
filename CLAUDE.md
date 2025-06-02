# Development Guidelines for ChatterBloke

This document contains guidelines and best practices for maintaining and developing the ChatterBloke project.

## Important: No Mock Mode Policy

**We don't ever use mock mode. We fix.**

When encountering issues with dependencies or integrations:
- Do NOT fall back to mock implementations
- Do NOT create placeholder functionality
- Instead, diagnose and fix the actual issue
- Ensure all required dependencies are properly installed and configured
- If PyTorch, Chatterbox, or other dependencies appear missing, investigate why they're not being detected

## Core Development Principles

### 1. Script Management
- **Only create new scripts when absolutely necessary** - Always prefer updating existing scripts over creating new ones
- **Never create scripts that generate other scripts** - If a script needs to be created, create it directly
- **Follow DRY (Don't Repeat Yourself)** - Reuse existing code and modules whenever possible
- **Keep scripts focused** - Each script should have a single, clear purpose

### 2. Code Modification Best Practices
- **Read before writing** - Always understand existing code before making changes
- **Preserve existing functionality** - Ensure modifications don't break existing features
- **Follow existing patterns** - Maintain consistency with the current codebase style
- **Test changes** - Run relevant tests after modifications

### 3. Version Control
- **Update CHANGELOG.md** - Document all significant changes as they occur
- **Write clear commit messages** - Describe what changed and why
- **Keep commits atomic** - One logical change per commit
- **Review changes before committing** - Use `git diff` to verify modifications

### 4. Project Structure
- **Respect the established directory structure** - Place files in appropriate directories
- **Don't create redundant directories** - Use existing structure from TECHPLAN.md
- **Keep data separate from code** - Use the data/ directory for runtime files

### 5. Dependencies
- **Minimize new dependencies** - Only add packages that provide significant value
- **Use poetry for dependency management** - Keep pyproject.toml updated
- **Pin versions** - Avoid using wildcard version specifiers
- **Document why dependencies are needed** - Add comments for non-obvious packages

### 6. Testing
- **Write tests for new functionality** - Maintain test coverage
- **Run existing tests before changes** - Ensure nothing breaks
- **Use pytest conventions** - Follow established testing patterns
- **Test edge cases** - Don't just test the happy path

### 7. Documentation
- **Update documentation with code** - Keep README.md and docstrings current
- **Document complex logic** - Add comments for non-obvious code
- **Keep TECHPLAN.md aligned** - Update if architecture changes
- **Use type hints** - Make code self-documenting with proper typing

### 8. Performance
- **Profile before optimizing** - Don't guess at performance issues
- **Cache expensive operations** - Especially for audio processing
- **Use async where appropriate** - Don't block the GUI thread
- **Monitor memory usage** - Audio files can be large

### 9. Security
- **Never hardcode credentials** - Use environment variables
- **Validate all inputs** - Especially file paths and user data
- **Sanitize file operations** - Prevent directory traversal attacks
- **Keep local data secure** - Set appropriate file permissions

### 10. Error Handling
- **Handle errors gracefully** - Don't let the application crash
- **Log errors appropriately** - Use the logging framework
- **Provide user-friendly messages** - Technical errors should be translated
- **Clean up on failure** - Don't leave partial files or states

## File-Specific Guidelines

### Python Files (.py)
- Use Black for formatting
- Follow PEP 8 conventions
- Add type hints for function signatures
- Keep functions under 50 lines when possible

### Configuration Files
- Use .env for secrets (never commit this)
- Keep config.py for application settings
- Document all configuration options

### Audio Files
- Store in appropriate data/voices/ subdirectories
- Use consistent naming conventions
- Clean up temporary files after processing
- Implement size limits to prevent disk issues

## Development Workflow

1. **Before Starting Work**
   - Review existing code
   - Check CHANGELOG.md for recent changes
   - Pull latest changes from repository
   - Review open issues

2. **During Development**
   - Make incremental changes
   - Test frequently
   - Keep the application runnable
   - Update tests as needed

3. **Before Committing**
   - Run the test suite: `pytest`
   - Format code: `black src/`
   - Check types: `mypy src/`
   - Update CHANGELOG.md
   - Review all changes

4. **After Major Changes**
   - Update documentation
   - Consider performance impact
   - Test on all target platforms
   - Update TECHPLAN.md if architecture changed

## Common Tasks

### Adding a New Voice Feature
1. Update the voice_service.py module
2. Add database migrations if needed
3. Update the GUI in voice_manager.py
4. Add tests for the new feature
5. Update API endpoints if applicable

### Modifying the GUI
1. Work within existing tab structure
2. Use consistent widget naming
3. Maintain responsive design
4. Test with different window sizes

### Integrating New TTS Models
1. Create adapter in services/
2. Maintain consistent interface
3. Handle model-specific errors
4. Document model requirements

## Debugging Tips

- Use logging instead of print statements
- Check logs in data/logs/
- Use breakpoints in PyQt6 carefully
- Test audio operations in isolation
- Monitor system resources during testing

## Remember

- **Quality over quantity** - Better to have fewer, well-tested features
- **User experience first** - Performance optimizations should not hurt UX
- **Keep it simple** - Avoid over-engineering solutions
- **Ask when unsure** - Better to clarify than to assume