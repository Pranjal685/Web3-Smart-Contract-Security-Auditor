# Loop Protection Constraints

This document defines the rules and patterns used by the Loop Protection Middleware to prevent infinite tool-execution loops during agentic workflows.

## The 3x Duplicate Call Rule
If any agent calls a tool with identical parameters three (3) times consecutively, the session must be immediately terminated to prevent resource consumption and infinite loops.

## Regex Pattern for Loop Detection
To detect loops, tool invocations are serialized into a sequence format. An example serialization pattern for a tool call is:
`tool:<tool_name>|params:<JSON_serialized_params>`

A log or stream of these serializations is matched against the following regex pattern (assuming newlines or unique delimiters separate consecutive calls):

```regex
^(?P<call>tool:[a-zA-Z0-9_-]+\|params:\{.*?\}),?\s*(?P=call),?\s*(?P=call)
```

### Pattern Breakdown:
1. `(?P<call>tool:[a-zA-Z0-9_-]+\|params:\{.*?\})` - Captures a serialized tool call name and its parameters into a named group `call`.
2. `,?\s*` - Matches optional separators (like commas or whitespaces) between tool calls.
3. `(?P=call)` - Matches the exact string matched by the first group (`call`) a second time.
4. `,?\s*` - Matches optional separator.
5. `(?P=call)` - Matches the exact string matched by the first group (`call`) a third time.

If a match is found on the command stream or execution history log, the middleware must immediately abort the execution.
