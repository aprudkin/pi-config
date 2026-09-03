---
name: documentation-system
description: Apply the Diátaxis framework to write, audit, organize, and improve technical documentation. Use when creating or revising tutorials, how-to guides, reference, explanation, docs IA, README sections, or documentation that feels mixed, incomplete, or hard to use.
metadata:
  source: https://diataxis.fr/
  framework: Diátaxis
---

# Diátaxis Documentation

Use Diátaxis as a way to think about documentation, not as a rigid template or top-down reorganization plan.

Diátaxis identifies four user needs and corresponding forms of documentation:

| Form | User need | Domain | Orientation | Promise |
|---|---|---|---|---|
| Tutorial | acquire skill through action | study | learning | a safe, meaningful learning experience |
| How-to guide | apply skill through action | work | goal | guidance through a real-world problem |
| Reference | apply knowledge | work | information | accurate, orderly technical description |
| Explanation | acquire knowledge through reflection | study | understanding | context and connections that deepen understanding |

The boundaries matter because each need demands different content, form, and language. Apply them at whatever scale helps: sentence, section, page, or documentation set.

## Use the compass

When form is unclear, ask two questions:

1. Does the user need **action** or **cognition**?
2. Is the user **acquiring** skill or **applying** it?

| Content | User activity | Form |
|---|---|---|
| informs action | acquisition/study | tutorial |
| informs action | application/work | how-to guide |
| informs cognition | application/work | reference |
| informs cognition | acquisition/study | explanation |

Use these terms flexibly. Identify the actual user need, not the label that an existing file or heading claims.

## Work iteratively

Do not begin by imposing four directories, creating empty sections, or planning a complete rewrite.

1. Choose one small piece already in front of you.
2. Ask what user need it serves and how well it serves it.
3. Use the compass when its purpose is uncertain.
4. Choose one immediate improvement: add, remove, move, split, rename, verify, or rewrite.
5. Make that improvement complete and usable.
6. Repeat.

Let information architecture emerge from well-formed content. Structure documentation from the inside out. Documentation can always improve without ever being “finished,” while each published state should remain useful and coherent.

For new documentation, start with the user need and write the smallest useful form that serves it. Do not create speculative coverage merely to fill all four forms.

## Form guidance

### Tutorial

A tutorial is a lesson: a practical, learning-oriented experience in which the learner gains skill through doing something meaningful.

The author carries responsibility for the learner’s safety and success. Design the experience, not a transfer of facts.

Must:
- State what **we will make or accomplish**, giving the learner a clear destination.
- Lead through concrete, meaningful actions in a logical learning journey.
- Deliver visible, comprehensible results early and often.
- Maintain a narrative of expected results and likely failure signs.
- Point out what the learner should notice.
- Use small steps and support repetition where practical.
- Make the journey meaningful, successful, logical, and usefully complete.
- Minimize explanation and ignore options or alternatives that interrupt the lesson.
- Test the full journey with representative learners and supported environments.

Avoid:
- “You will learn…” promises; describe what the learner will do instead.
- Assuming the learner can make expert choices.
- Detours, broad option lists, edge-case catalogues, and conceptual lectures.
- Calling a task recipe a tutorial merely because it contains steps.

Useful language:

```md
# Build <small meaningful thing>

In this tutorial, we will <concrete accomplishment>.

## Before you begin
<minimal known-good starting point>

## <First concrete action>
<exact direction>

You should see:
<expected result>

Notice that <learning cue>.

## <Next action>
...

## What you made
<brief acknowledgement of the accomplishment>

## Where to go next
<link to a related tutorial, how-to guide, reference, or explanation>
```

### How-to guide

A how-to guide gives goal-oriented directions for a competent user facing a real-world problem or desired result.

Write from the user’s project, not from the machinery’s features. Tools are means to the user’s end.

Must:
- Address a specific, meaningful goal or problem.
- Assume suitable competence; do not turn the guide into a lesson.
- Provide an executable solution through actions, judgement, or both.
- Arrange guidance in a logical sequence that follows the user’s activity and thinking.
- Preserve flow and minimize context switching.
- Remain adaptable to realistic variants.
- Prefer practical usability over completeness.
- Start and end at reasonable points that the user can connect to their own work.
- Use an exact title, usually “How to <achieve result>”.

A how-to guide need not be a simple linear procedure. Real problems can require branches, overlapping actions, multiple entry or exit points, and user judgement.

Avoid:
- Teaching from first principles.
- Feature-led topics with no human purpose.
- Exhaustive option catalogues or long rationale.
- Open-ended goals such as “How to build a web application.”

Useful language:

```md
# How to <achieve specific result>

This guide shows you how to <solve problem or reach result>.

## Before you begin
<assumed knowledge and state>

## <Action or decision>
<directions, including conditions where needed>

If <situation>, <action>.

## Verify the result
<check tied to the user's goal>

## Related information
<link to reference or explanation>
```

### Reference

Reference is information-oriented technical description. Users consult it during work for truth and certainty.

Must:
- Describe the machinery neutrally, succinctly, and authoritatively.
- Be accurate, precise, complete, clear, and consistent.
- Mirror the product’s logical structure where that helps users navigate both together.
- Use standard, repeated patterns readers can scan.
- State behavior, syntax, types, defaults, constraints, side effects, errors, limitations, and compatibility where relevant.
- Include succinct examples when they illuminate usage without becoming instruction.
- Generate from authoritative sources when practical, then verify generated output.

Avoid:
- Task journeys, teaching narratives, rationale, speculation, and opinion.
- Restructuring reference around imagined user tasks when product structure is the better map.
- Clever prose where predictable formatting works better.

Useful shape:

```md
# <API, command, module, or configuration item>

<brief factual description>

## Syntax
`<exact form>`

## Parameters, options, or fields
| Name | Type | Required | Default | Description |
|---|---|---|---|---|

## Behavior
<facts, constraints, side effects, warnings>

## Output
<facts>

## Errors
<errors and conditions>

## Examples
<minimal illustrations>

## See also
<links to related how-to guides or explanation>
```

### Explanation

Explanation is understanding-oriented, discursive material that helps readers reflect on a bounded topic.

It provides a higher and wider perspective than task guidance or technical description. It should make sense away from immediate work in the product.

Must:
- Deepen and broaden understanding.
- Connect the topic to related ideas.
- Provide background, context, design reasons, history, and technical constraints where useful.
- Draw implications and use examples to illuminate them.
- Admit relevant opinion, perspective, alternatives, and counterexamples.
- Bound the topic around a meaningful question, often an implicit “why?” or “tell me about…”.

Avoid:
- Required action sequences.
- API or option catalogues.
- Unbounded essays that absorb every related topic.
- Presenting opinion as neutral fact.

Useful shape:

```md
# About <bounded topic>

<why this topic deserves reflection>

## Context
<background and problem space>

## Connections
<relationships and mental model>

## Why it works this way
<constraints, decisions, history>

## Alternatives and perspectives
<tradeoffs, counterexamples, opinions identified as such>

## Implications
<how this changes understanding>

## Related information
<links to tutorials, how-to guides, or reference>
```

## Auditing and review

Inspect content at the smallest useful scale. Do not force an entire page into one form when a problematic paragraph is the real unit to fix.

For each item reviewed, report:

```md
## Diátaxis review: <item>

User need: <action/cognition + acquisition/application>
Likely form: tutorial | how-to guide | reference | explanation
Current fit: <what works and what conflicts>

### Functional quality
- Accuracy: <evidence or verification needed>
- Completeness: <relevant gaps>
- Consistency and precision: <issues>
- Usefulness: <fit to actual need>

### Form and flow
- <language, ordering, interruptions, misplaced material>

### Next improvement
1. <single smallest change that improves it now>

### Later opportunities
- <only evidenced follow-up work; no speculative four-quadrant backlog>
```

Use the compass to diagnose mixed content:
- Action + acquisition belongs in a tutorial.
- Action + application belongs in a how-to guide.
- Cognition + application belongs in reference.
- Cognition + acquisition belongs in explanation.

Move or link off-purpose material when that improves flow. Do not split content mechanically; a small amount of another form can support the primary need when it does not interrupt it.

## Quality boundary

Diátaxis helps content fit human needs, develop flow, and expose hidden problems. It does **not** guarantee functional quality.

Always validate objective qualities separately:
- accuracy against product behavior and authoritative sources
- completeness against supported scope
- consistency across related documentation
- precision of terminology, commands, examples, and constraints
- usefulness with representative user goals

Functional quality is required before deeper qualities such as flow, anticipation, fit, and pleasure in use can hold.

## Output contract

When writing or revising documentation:

1. Name the user need and selected form in one short line when useful to the requester.
2. Produce the requested documentation, not a framework lecture.
3. Link to other forms only when they serve a real adjacent need.
4. Preserve existing information architecture unless a concrete problem justifies changing it.
5. Prefer one complete improvement now over a speculative redesign.

Source of truth: [Diátaxis](https://diataxis.fr/).
