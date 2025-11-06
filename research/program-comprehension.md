# Program Comprehension and Cognitive Load

This document covers research on how programmers understand code, the cognitive processes involved, and how cognitive load affects program comprehension.

## Overview

Program comprehension—understanding what code does and how it works—is fundamental to software development. Research using cognitive science methods (fMRI, EEG, eye-tracking) has revealed how the brain processes code and what makes code difficult to understand. This research has important implications for educational tools like Code Tutor.

## Papers

---

### 1. Program Comprehension and Code Complexity Metrics: An fMRI Study

**Authors:** Norman Peitek, Sven Apel, Chris Parnin, André Brechmann, Janet Siegmund

**Published:** ICSE 2021 (International Conference on Software Engineering)

**Link:** https://conf.researchr.org/details/icse-2021/icse-2021-papers/10/Program-Comprehension-and-Code-Complexity-Metrics-An-fMRI-Study

**ACM:** https://dl.acm.org/doi/10.1109/ICSE43902.2021.00056

**Replication Package:** https://github.com/brains-on-code/fMRI-complexity-metrics-icse2021

#### Abstract

**Background**: Researchers and practitioners have been using code complexity metrics for decades to predict how developers comprehend a program. While it is plausible and tempting to use them for this purpose, their validity is debated, since they rely on code properties and rarely consider particularities of human cognition.

**Aims**: Investigate whether and how code complexity metrics reflect difficulty of program comprehension.

**Method**: Conducted a functional magnetic resonance imaging (fMRI) study with 19 participants observing program comprehension of short code snippets at varying complexity levels. Dissected four classes of code complexity metrics and their relationship to neuronal, behavioral, and subjective correlates of program comprehension, overall analyzing more than 41 metrics.

**Results**: While data corroborate that complexity metrics can—to a limited degree—explain programmers' cognition in program comprehension, fMRI allowed insights into why some code properties are difficult to process. In particular, a code's textual size drives programmers' attention, and vocabulary size burdens programmers' working memory.

**Conclusion**: Results provide neuro-scientific evidence supporting warnings of prior research questioning the validity of code complexity metrics and pin down factors relevant to program comprehension.

#### Key Findings

1. **Textual Size Matters**: The sheer amount of code (lines of code, text length) drives programmers' attention and cognitive load

2. **Vocabulary Size Burdens Working Memory**: The number of distinct identifiers (variable names, function names) particularly burdens programmers' working memory

3. **Complexity Metrics Have Limited Validity**: Traditional code complexity metrics (like cyclomatic complexity) have limited correlation with actual cognitive difficulty

4. **Working Memory is Key**: Program comprehension is fundamentally limited by working memory capacity

5. **Brain Regions Involved**: The study identified specific brain regions involved in code comprehension, showing overlap with language processing and mathematical reasoning

#### Methodology

- 19 participants
- fMRI brain scanning while comprehending code
- Short Java code snippets at varying complexity
- Measured brain activation patterns
- Correlated with 41+ complexity metrics
- Compared neuronal, behavioral, and subjective measures

#### Relevance to This Project

This neuroscience-based research has direct implications for Code Tutor:

**1. Reducing Cognitive Load**

Code Tutor should help reduce cognitive load by:
- Breaking down complex code into understandable pieces
- Explaining unfamiliar vocabulary (what does this variable represent?)
- Highlighting the most important parts (focus attention)
- Providing context that reduces working memory burden

**2. Vocabulary Explanation**

Since vocabulary size burdens working memory, Code Tutor could:
- Explicitly ask about and explain identifier naming choices
- Help users understand the "mental model" behind variable names
- Suggest clearer naming when vocabulary is confusing
- Build a "vocabulary map" for large codebases

**3. Managing Textual Size**

For large files or complex code:
- Provide summaries that reduce information to work with
- Help users focus on relevant sections
- Break reviews into manageable chunks
- Use abstraction to handle large code without overwhelming working memory

**4. Question Design**

Understanding that working memory is limited, Code Tutor should:
- Ask focused questions, not overwhelming lists
- Break complex questions into smaller parts
- Allow users to handle one concept at a time
- Provide written summaries users can refer back to (external memory)

**5. Feedback Structure**

Feedback should be structured to minimize cognitive load:
- Clear section headings for easy navigation
- Bullet points rather than dense paragraphs
- Code examples to illustrate points (reduces translation burden)
- Specific file locations so users don't have to search

**Key Insight:** Program comprehension is fundamentally a working memory challenge. Code Tutor should act as an "external working memory" that helps manage cognitive load by organizing, summarizing, and focusing attention.

---

### 2. Comprehension of Computer Code Relies Primarily on Domain-General Executive Brain Regions

**Authors:** Liu et al.

**Published:** eLife, 2020

**Link:** https://elifesciences.org/articles/58906

#### Key Finding

The study found that it is the MD (multiple demand) regions, not the language regions, that are primarily involved in program comprehension. The fact that the MD system responds to code problems over and above content-matched sentence problems underscores the role of domain-general executive processes in code comprehension.

#### Implications

- **Not Language Processing**: Code comprehension is more like problem-solving than language reading
- **Executive Function**: Uses the brain's executive control systems for planning, reasoning, and cognitive control
- **Domain-General Skills**: Programming draws on general cognitive skills, not language-specific processing

#### Relevance to This Project

This finding has important implications for how Code Tutor should approach code education:

**1. Problem-Solving Focus**

Since code comprehension uses executive function (problem-solving) regions:
- Frame code review as problem-solving, not just reading
- Ask "what problem does this solve?" not just "what does this do?"
- Emphasize planning, reasoning, and design decisions
- Connect code to computational thinking

**2. Not Just Syntax**

Code Tutor should focus on:
- Algorithmic reasoning (not just syntax rules)
- Design decisions (executive planning)
- Trade-offs and alternatives (evaluation)
- Problem decomposition (cognitive control)

**3. Transfer to Other Domains**

Since programming uses domain-general executive processes:
- Skills learned through Code Tutor transfer to other problem-solving domains
- Emphasize that learning to code improves general reasoning
- Frame programming as cognitive skill development

**4. Teaching Approach**

Code Tutor should:
- Engage executive function through open-ended questions
- Promote planning and strategic thinking
- Encourage evaluation and comparison of alternatives
- Focus on reasoning, not just memorization

**Key Insight:** Code comprehension is problem-solving, not language processing. Code Tutor should engage users' executive function through strategic questions about design, planning, and trade-offs.

---

### 3. Measuring the Cognitive Load of Software Developers: Extended Systematic Mapping Study

**Authors:** Multiple authors

**Published:** Information and Software Technology, 2021

**Link:** https://www.sciencedirect.com/science/article/abs/pii/S095058492100046X

#### Overview

A comprehensive systematic mapping study of cognitive load measurement in software engineering, analyzing 63 primary studies from an initial pool of 4,175 candidates.

#### Cognitive Load Theory

Cognitive Load Theory distinguishes three types of load:

1. **Intrinsic Load**: Inherent difficulty of the material (complexity of the algorithm)
2. **Extraneous Load**: Difficulty from poor presentation (confusing naming, bad structure)
3. **Germane Load**: Productive cognitive effort toward learning and understanding

#### Measurement Methods

Studies used various methods to measure cognitive load:
- Physiological: EEG, eye-tracking, heart rate, skin conductance
- Behavioral: Task performance, time on task
- Subjective: Self-report questionnaires

#### Key Findings

- Cognitive load significantly affects software development performance
- Poor code quality increases extraneous cognitive load
- Developers' cognitive load approaches the limits of their working memory, making them prone to errors
- Both too little and too much cognitive load are problematic

#### Relevance to This Project

This research provides a framework for thinking about how Code Tutor affects cognitive load:

**1. Reduce Extraneous Load**

Code Tutor should help identify and reduce extraneous cognitive load:
- Point out confusing naming that increases load unnecessarily
- Identify poor code structure that makes comprehension harder
- Suggest refactoring that reduces mental burden
- Explain complex code to reduce processing difficulty

**2. Optimize Germane Load**

Code Tutor should increase productive learning effort:
- Ask questions that promote deep understanding (germane load)
- Encourage thinking about design and architecture
- Promote schema building and pattern recognition
- Support construction of mental models

**3. Don't Add Load**

Code Tutor itself shouldn't add cognitive load:
- Clear, well-structured feedback (not walls of text)
- Focused questions (not overwhelming lists)
- Specific locations (not vague references)
- Progressive revelation (not everything at once)

**4. Load-Aware Interaction**

Different users have different cognitive capacity:
- Beginners: Lower intrinsic capacity, need more support
- Experts: Higher capacity, can handle more complex analysis
- Experience-level configuration helps match load to capacity

**5. Teach Load Management**

Code Tutor can teach strategies for managing cognitive load:
- Breaking problems into smaller pieces
- Using clear naming to reduce memory burden
- Structuring code to support comprehension
- Documentation as external memory

**Key Insight:** Code Tutor should reduce extraneous load, optimize germane load, and not add load itself. This means clear, focused, well-structured interactions that support understanding without overwhelming.

---

### 4. The Effect of Poor Source Code Lexicon and Readability on Developers' Cognitive Load

**Authors:** Multiple authors

**Published:** ACM Conference on Program Comprehension, 2018

**Link:** https://dl.acm.org/doi/10.1145/3196321.3196347

**ResearchGate:** https://www.researchgate.net/publication/323933178_The_Effect_of_Poor_Source_Code_Lexicon_and_Readability_on_Developers'_Cognitive_Load

#### Key Finding

Results suggest that poor quality lexicon impairs program comprehension and consequently increases the effort that developers must spend to maintain the software.

#### Lexicon Quality Issues

- Inconsistent naming conventions
- Unclear or misleading identifier names
- Abbreviations without clear meaning
- Inconsistent abstraction levels in naming

#### Impact

- Increased cognitive load
- More time required for comprehension
- Higher error rates
- Reduced maintainability

#### Relevance to This Project

This paper highlights the importance of naming, which is highly relevant to Code Tutor:

**1. Naming as Focus Area**

Code Tutor should pay special attention to identifier naming:
- Ask users to explain their naming choices
- Point out potentially confusing names
- Suggest clearer alternatives when appropriate
- Check for consistency in naming patterns

**2. Lexicon Questions**

Specific questions Code Tutor could ask:
- "What does [variable name] represent?"
- "Why did you choose this particular name?"
- "Is this naming convention consistent with the rest of the codebase?"
- "Would a more descriptive name help future readers?"

**3. Cognitive Load Reduction**

Good naming reduces cognitive load—Code Tutor can emphasize this:
- Explain how clear naming reduces working memory burden
- Show that time spent on good naming saves time in maintenance
- Frame naming as part of "being kind to future readers (including yourself)"

**4. "Teach Me!" Mode Application**

In "Teach Me!" mode, include exercises with poor naming:
- Present code with confusing variable names
- Ask users to identify what's unclear
- Explain how the poor naming increases cognitive load
- Have users practice improving naming

**Key Insight:** Identifier naming has a huge impact on cognitive load. Code Tutor should explicitly address naming quality as a readability and comprehension issue.

---

### 5. Estimating Developers' Cognitive Load at a Fine-Grained Level Using Eye-Tracking Measures

**Authors:** Multiple authors

**Published:** ACM Conference on Program Comprehension, 2022

**Link:** https://dl.acm.org/doi/10.1145/3524610.3527890

#### Methodology

Used eye-tracking to measure cognitive load in real-time as developers work with code. Eye movement patterns (fixation duration, saccade length, pupil dilation) correlate with cognitive load.

#### Findings

- Cognitive load varies significantly within a single code-reading session
- Different code sections impose different cognitive demands
- Developers' cognitive load frequently approaches working memory limits
- When load is high, comprehension accuracy decreases

#### Relevance to This Project

This research shows that cognitive load is dynamic and varies by code section:

**1. Selective Focus**

Code Tutor should help users focus on the most important/difficult parts:
- Identify which sections are most complex
- Prioritize review effort on high-complexity areas
- Allow users to specify sections to focus on
- Don't force comprehensive review of all code equally

**2. Load-Aware Pacing**

Break reviews into manageable chunks:
- Don't try to review everything at once
- Allow users to take breaks between sections
- Provide summaries for context without full detail
- Let users control the pace of review

**3. Difficulty Signaling**

Code Tutor could explicitly signal difficulty:
- "This section is particularly complex..."
- "This is straightforward, so we'll focus elsewhere..."
- Help users allocate their cognitive resources efficiently

**4. Support for High-Load Code**

When code is inherently complex:
- Provide more explanation and context
- Break down into smaller conceptual pieces
- Offer analogies or examples
- Be especially clear and well-structured in feedback

**Key Insight:** Not all code is equally demanding. Code Tutor should help users allocate their cognitive resources efficiently by identifying what's most important and providing appropriate support for complex sections.

---

### 6. On the Accuracy of Code Complexity Metrics: A Neuroscience-Based Guideline for Improvement

**Published:** PMC, 2023

**Link:** https://pmc.ncbi.nlm.nih.gov/articles/PMC9942489/

#### Key Finding

EEG can be used to accurately identify programmers' cognitive load associated with understanding code of varying complexity. This validates that complexity metrics should be evaluated against actual cognitive load, not just theoretical constructs.

#### Implications for Metrics

- Traditional metrics (cyclomatic complexity, etc.) are imperfect proxies for cognitive difficulty
- Neuroscience methods can validate or refute metric validity
- Some code properties have higher cognitive impact than metrics suggest

#### Relevance to This Project

This research suggests Code Tutor should:

**1. Look Beyond Metrics**

Don't rely solely on traditional complexity metrics:
- Consider readability, not just structure
- Evaluate naming and vocabulary
- Consider cognitive factors beyond code structure
- Use holistic assessment of comprehension difficulty

**2. Focus on Actual Difficulty**

Prioritize features that actually make code harder to understand:
- Confusing naming (high cognitive impact)
- Large vocabulary (working memory burden)
- Misleading structure (mental model mismatch)
- Poor documentation (lack of context)

**3. Human-Centered Assessment**

Code Tutor uses an LLM that can consider cognitive factors:
- "Would a programmer find this confusing?"
- "Does this require too much working memory?"
- "Is the cognitive flow clear?"
- These questions are hard for rule-based tools but natural for LLMs

**Key Insight:** Code Tutor should focus on cognitive difficulty for humans, not just structural complexity metrics.

---

## Summary of Key Themes

Across program comprehension research, consistent themes emerge:

1. **Working Memory is the Bottleneck**: Program comprehension is fundamentally limited by working memory capacity (typically 7±2 items)

2. **Vocabulary Matters More Than Structure**: Identifier naming and vocabulary size have outsized impact on cognitive load

3. **Executive Function, Not Language**: Code comprehension uses problem-solving brain regions, not language regions

4. **Cognitive Load Has Three Types**: Intrinsic (inherent difficulty), extraneous (poor presentation), and germane (productive learning)

5. **Poor Code Quality Increases Load**: Confusing naming, inconsistent style, and poor structure unnecessarily burden cognition

6. **Metrics Are Imperfect**: Traditional complexity metrics poorly predict actual cognitive difficulty

7. **Load is Dynamic**: Cognitive load varies throughout a code-reading session depending on the specific code section

## Implications for Code Tutor

### How Code Tutor Should Support Comprehension

Based on this research, Code Tutor should:

**1. Act as External Working Memory**
- Provide summaries and context (offload from working memory)
- Break complex code into manageable chunks
- Offer written reference that users can consult repeatedly
- Structure feedback to be easily navigable

**2. Focus on Naming and Vocabulary**
- Explicitly discuss identifier naming choices
- Point out confusing or inconsistent naming
- Explain domain-specific vocabulary
- Suggest clearer alternatives when appropriate

**3. Reduce Extraneous Cognitive Load**
- Identify code that's unnecessarily confusing
- Point out where presentation makes comprehension harder
- Suggest refactoring that improves understandability
- Explain complex sections to reduce processing burden

**4. Engage Executive Function**
- Ask questions about problem-solving and design
- Encourage strategic thinking and planning
- Explore trade-offs and alternatives
- Focus on reasoning, not just syntax

**5. Be Load-Aware**
- Provide clear, well-structured feedback (don't add load)
- Use focused questions (not overwhelming lists)
- Allow users to control pacing
- Adapt to experience level (beginners have less capacity)

**6. Prioritize Effectively**
- Help users focus on the most important/complex parts
- Don't force equal attention to all code
- Signal difficulty levels
- Support efficient allocation of cognitive resources

### Design Principles from Cognitive Science

**Working Memory Limits:**
- Limit questions to 2-4 at a time (not 10+)
- Break feedback into clear sections
- Use external representation (written feedback) as memory aid
- Allow users to process one concept before moving to the next

**Vocabulary Impact:**
- Always clarify unfamiliar terms
- Ask about naming choices explicitly
- Build glossaries for complex codebases
- Emphasize naming as cognitive load management

**Executive Function:**
- Frame as problem-solving, not just code reading
- Ask "why" and "how" questions (strategic thinking)
- Explore alternatives (planning and evaluation)
- Connect to broader design principles (abstraction)

**Load Management:**
- Reduce extraneous load (clear, well-structured feedback)
- Optimize germane load (promote productive thinking)
- Don't add unnecessary load (focus and clarity)
- Adapt to user capacity (experience-level configuration)

### Features to Enhance Comprehension Support

Based on this research, potential Code Tutor enhancements:

1. **Vocabulary Glossary**
   - Generate glossaries for unfamiliar identifiers
   - Explain domain-specific terms
   - Build shared understanding of codebase vocabulary

2. **Complexity Highlights**
   - Identify sections that are cognitively demanding
   - Explain why certain code is complex
   - Suggest simplification strategies

3. **Chunking Support**
   - Break large files into logical sections
   - Review one chunk at a time
   - Provide section summaries

4. **Naming Analysis**
   - Dedicated focus on identifier naming
   - Consistency checking
   - Clarity assessment
   - Suggestions for improvement

5. **Mental Model Building**
   - Help users build accurate mental models of code
   - Provide architectural overview
   - Explain relationships and dependencies
   - Use analogies and examples

6. **Load Indicators**
   - Signal cognitive difficulty of code sections
   - Warn when code approaches comprehension limits
   - Suggest when refactoring would reduce load

### What Not to Do

Based on cognitive load research, Code Tutor should avoid:

❌ **Overwhelming users with information** - Respects working memory limits
❌ **Dense, unstructured feedback** - Adds extraneous cognitive load
❌ **Asking too many questions at once** - Exceeds working memory capacity
❌ **Focusing only on structural metrics** - Misses actual cognitive difficulty
❌ **Ignoring naming and vocabulary** - Missing high-impact factors
❌ **Treating all code equally** - Ignores dynamic variation in difficulty

## Conclusion

Research on program comprehension reveals that understanding code is fundamentally a cognitive challenge limited by working memory. Vocabulary size, naming quality, and presentation all have major impacts on cognitive load—often more than structural complexity.

Code Tutor is well-positioned to support program comprehension by:
- Acting as external working memory through structured feedback
- Focusing on high-impact factors like naming and vocabulary
- Engaging executive function through strategic questions
- Managing cognitive load through clear, focused interaction
- Prioritizing based on actual cognitive difficulty

The key insight is that Code Tutor should be designed with cognitive science in mind, not just programming concepts. By understanding how programmers' brains process code, Code Tutor can provide support where it's most needed and avoid adding unnecessary cognitive burden.

Most importantly, this research validates that education and explanation (Code Tutor's focus) are more valuable than mere complexity metrics—because comprehension is about human cognition, not just code structure.
