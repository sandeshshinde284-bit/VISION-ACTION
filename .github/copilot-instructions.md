# GitHub Copilot Project Instructions

## Main objective

Provide accurate, project-specific answers based on the existing codebase.

Before answering or changing code:

- Inspect the relevant files and folders.
- Search the project for similar implementations and existing patterns.
- Check related interfaces, models, services, components, configuration, and tests.
- Check callers and usages before changing methods, classes, interfaces, or public APIs.
- Follow the existing architecture, naming conventions, formatting, and error-handling patterns.
- Reuse existing utilities, services, components, and dependencies where possible.
- Do not provide a generic solution when the project already contains a relevant pattern.
- Do not guess about project code, files, methods, APIs, configuration, or test results.
- If the required information cannot be found, clearly state what is missing.

## Code change policy

- Make the smallest change required for the requested behavior.
- Modify only the necessary files and code sections.
- Do not rewrite or return the complete file for a small change.
- Do not modify unrelated files or code.
- Do not reformat unrelated code.
- Do not repeat unchanged code.
- Do not add dependencies unless explicitly requested or clearly necessary.
- Do not change public APIs, database schemas, external contracts, or architecture unless explicitly requested or required.
- Preserve existing behavior outside the requested change.
- Preserve backward compatibility where possible.
- Follow the project's existing patterns instead of introducing a new approach.
- Do not remove existing functionality unless explicitly requested.

## Response requirements

Keep the response proportional to the size and complexity of the requested change.

For every code change, provide enough information for the user to apply the change correctly:

1. What needs to change
2. The exact file path
3. The exact class, method, function, component, or configuration location
4. The code to add, replace, delete, or move
5. A short explanation of why the change is correct
6. Required or recommended refactoring, if relevant
7. Relevant validation or tests

## Small changes

For one-line or small changes:

- Do not provide a long plan.
- Do not provide the complete file.
- Do not explain unchanged code.
- Show the exact file path.
- Identify the exact code location.
- Show only the required code.
- Clearly label whether the code should be added, replaced, deleted, or moved.
- Include required imports only when necessary.
- Mention relevant validation briefly.
- Do not provide a general summary unless it is needed to understand the change.

Use this format:

What:
Brief description of the required change.

File:
exact/path/to/file.ext

Location:
ClassName.methodName()
or another precise code location.

Action:
Add / Replace / Delete / Move

Change:
[Show only the necessary code]

Why:
Brief explanation of why this change is correct and how it fits the existing project.

Refactoring:
Required: [None, or explain what must be refactored]
Recommended: [None, or explain optional improvement]

Validation:
Relevant test, build, lint, or validation command.

When replacing code, use this format:

File:
exact/path/to/file.ext

Location:
ClassName.methodName()

Replace:

[existing code]

With:

[new code]

Why:
Brief explanation.

Refactoring:
Required: None
Recommended: None

Validation:
Relevant validation or test.

## Larger changes

For larger changes:

- Inspect the project before proposing an implementation.
- Identify all affected files.
- Identify the relevant classes, methods, functions, components, tests, and configuration.
- Explain the implementation approach briefly.
- Provide focused changes for each affected location.
- Do not repeat unchanged code.
- Do not return complete files unless explicitly requested.
- Separate required implementation changes from optional refactoring.
- Identify assumptions and risks.
- Identify relevant tests and validation steps.

## Project inspection

Before proposing a solution, inspect the following when relevant:

- Existing implementations of similar functionality
- Callers and consumers of the code being changed
- Interfaces and abstract classes
- Related models, DTOs, entities, and schemas
- Services, controllers, repositories, components, and utilities
- Configuration files and environment variables
- Dependency and build files
- Existing tests and test utilities
- Error-handling and logging patterns
- Security and validation patterns

Do not ask the user for information that can be found by inspecting the project.

## Refactoring review

For every non-trivial change, check whether refactoring is relevant.

Separate refactoring into two categories.

### Required refactoring

Required refactoring is necessary for the requested change to work correctly, safely, or maintainably.

If required refactoring exists, explain:

- What must be refactored
- Why it is required
- Which files or code sections are affected
- The risk of not doing it

### Recommended refactoring

Recommended refactoring is useful but not necessary for the current request.

Check for:

- Duplicated logic
- Overly large methods or classes
- Incorrect responsibility between layers
- Unclear naming
- Dead or unreachable code
- Unused imports or dependencies
- Repeated constants or hard-coded values
- Missing error handling
- Inconsistent validation
- Weak separation of concerns
- Performance problems
- Security risks
- Difficult-to-test code
- Missing or outdated tests

For each recommended refactoring, explain:

- What should be refactored
- Why it is recommended
- The expected benefit
- The estimated scope or risk

Do not perform recommended refactoring automatically.

Do not expand a small change into a large refactor without explicit approval.

Do not recommend refactoring only because of personal preference. Recommendations must be based on:

- Existing project conventions
- A clear maintainability problem
- A correctness or security issue
- A measurable performance or reliability concern
- A meaningful reduction in duplication or complexity

If no refactoring is needed, state:

No refactoring is required for this change.

## Questions and clarification

- Search the project before asking questions.
- Do not ask for information that already exists in the repository.
- If the requirement is clear, answer it directly.
- If the requirement is ambiguous, ask only the specific question that blocks a correct answer.
- If there are multiple valid approaches, recommend one and briefly explain the trade-offs.
- Clearly identify assumptions.
- Do not repeat a question that has already been answered in the current conversation.
- Do not ask for confirmation before explaining a clear solution.
- Ask for approval before applying optional, non-essential refactoring.

## Accuracy and safety rules

- Never invent files, classes, methods, APIs, configuration values, dependencies, or test results.
- Clearly distinguish between:
  - Facts found in the project
  - Assumptions
  - Required changes
  - Recommendations
- Check callers and usages before changing public behavior.
- Check tests before changing existing behavior.
- Consider null values, empty values, invalid input, error handling, security, and backward compatibility.
- Do not claim that tests, builds, linting, compilation, or validation passed unless they were actually run.
- If a required file cannot be inspected, say so instead of assuming its contents.
- If the requested change may introduce a breaking change, clearly warn the user.

## Dependency and architecture rules

- Reuse existing project dependencies where possible.
- Do not introduce a new library for functionality already available in the project.
- Do not change the project's architecture for a local problem.
- Do not move code between layers unless there is a clear reason.
- Do not change database schemas or external contracts without explicit approval.
- If a dependency or architectural change is necessary, explain the reason before applying it.
- Identify migration, compatibility, or deployment effects when relevant.

## Testing and validation

- Identify tests that should be added or updated for behavior changes.
- Use the project's existing testing patterns and utilities.
- Suggest the smallest relevant test command.
- Consider important edge cases.
- Run validation only when appropriate and supported by the current workflow.
- Report actual results only.
- If validation was not run, state that it was not run.
- Do not provide a long test report for a small change.

## Output and token usage

- Be complete but concise.
- Provide enough explanation to prevent repeated questions.
- Do not provide unnecessary background information.
- Do not return complete files for localized changes.
- Do not repeat the same code in multiple sections.
- Do not explain unchanged code.
- Show exact locations and focused code snippets.
- Use a focused diff when appropriate.
- For a one-line change, provide the file path, location, replacement or addition, reason, refactoring status, and relevant validation only.
- For a larger change, provide more detail and identify all affected files.