# Learning by Teaching and the Protégé Effect

This document covers research on the protégé effect, teachable agents, and learning-by-teaching pedagogical approaches in educational technology.

## The Protégé Effect

The protégé effect is a psychological phenomenon where teaching or preparing to teach information to others results in better learning and retention than studying the material for oneself. The term comes from the French word "protégé," meaning student or mentee.

## Papers

---

### 1. Teachable Agents and the Protégé Effect: Increasing the Effort Towards Learning

**Authors:** Chase, C. C., Chin, D. B., Oppezzo, M. A., & Schwartz, D. L.

**Published:** Journal of Science Education and Technology, 2009, Vol. 18, pp. 334-352

**Link:** https://link.springer.com/article/10.1007/s10956-009-9180-4

**PDF:** https://aaalab.stanford.edu/assets/papers/2009/Protege_Effect_Teachable_Agents.pdf

#### Abstract

The idea that teaching others is a powerful way to learn is intuitively compelling and supported in the research literature. We have developed computer-based, domain-independent Teachable Agents that students can teach using a visual representation. The students query their agent to monitor their learning and problem solving behavior. This motivates the students to learn more so they can teach their agent to perform better.

#### Key Findings

- Students make greater effort to learn for their teachable agents (TAs) than they do for themselves
- TA students spent more time on learning activities (e.g., reading) and also learned more
- These beneficial effects were most pronounced for lower achieving children
- The protégé effect is particularly powerful because it:
  - Increases student motivation
  - Encourages metacognition (thinking about thinking)
  - Promotes deeper engagement with material
  - Shifts students' mindset from performance to mastery

#### Relevance to This Project

This paper is **highly relevant** to Code Tutor's "Teach Me!" mode:

- **Core Mechanism**: The "Teach Me!" mode operates on the exact principle studied in this paper—having users explain code mistakes engages the protégé effect
- **Motivation**: When users must explain what's wrong with code, they take more care and think more deeply than if they were just reviewing code for themselves
- **Lower Achievement Benefits**: The finding that the protégé effect helps lower-achieving students most suggests "Teach Me!" mode could be especially valuable for beginner programmers
- **Metacognition**: By asking users to explain *why* code is wrong (not just *that* it's wrong), Code Tutor encourages metacognitive thinking about programming
- **Design Validation**: This research provides strong empirical support for the "Teach Me!" feature's pedagogical approach

**Potential Enhancement:** Code Tutor could make the protégé effect even more explicit by framing it as "teaching a friend" or "explaining to a junior developer" to strengthen the psychological effect.

---

### 2. Designing Learning by Teaching Agents: The Betty's Brain System

**Authors:** Leelawong, K., & Biswas, G.

**Published:** International Journal of Artificial Intelligence in Education, 2008, Vol. 18(3), pp. 181-208

**Link:** https://dl.acm.org/doi/10.5555/1454278.1454280

**ResearchGate:** https://www.researchgate.net/publication/220049808_Designing_Learning_by_Teaching_Agents_The_Betty's_Brain_System

#### Abstract

The idea that teaching others is a powerful way to learn is intuitively compelling and supported in the research literature. We have developed computer-based, domain-independent Teachable Agents that students can teach using a visual representation. The students query their agent to monitor their learning and problem solving behavior. This motivates the students to learn more so they can teach their agent to perform better. This paper presents a teachable agent called Betty's Brain that combines learning by teaching with self-regulated learning feedback to promote deep learning and understanding in science domains. A study conducted in a 5th grade science classroom compared three versions of the system: a version where the students were taught by an agent, a baseline learning by teaching version, and a learning by teaching version where students received feedback on self-regulated learning strategies and some domain content.

#### Key Findings

- Betty's Brain is a computer-based learning environment where students instruct a character called a Teachable Agent (TA) which can reason based on how it is taught
- The system capitalizes on the social aspects of learning by creating a sense of responsibility for the agent's performance
- Students who received self-regulated learning (SRL) feedback showed better learning outcomes
- The visual concept map representation helped students organize and structure knowledge
- Students exhibited increased effort and persistence when teaching their agent

#### System Design Features

1. **Visual Knowledge Representation**: Students teach Betty by creating concept maps with causal relationships
2. **Agent Querying**: Students can quiz Betty to see what she has learned
3. **Mentor Agent**: A mentor character provides hints and feedback on both content and learning strategies
4. **Self-Regulated Learning Support**: System provides feedback on learning strategies, not just content

#### Relevance to This Project

Betty's Brain provides a comprehensive model for learning-by-teaching systems that could inform Code Tutor:

- **Teach Me! Mode Design**: The current "Teach Me!" mode has students identify and explain code mistakes—Betty's Brain shows this could be extended with:
  - Visual representations of concepts students are teaching/learning
  - A persistent "tutee" that remembers previous lessons
  - Multiple rounds of teaching to build knowledge progressively

- **Self-Regulated Learning**: Betty's Brain's SRL feedback component suggests Code Tutor could provide meta-level feedback like:
  - "You're focusing on syntax errors—also consider design patterns"
  - "Good job identifying the error quickly—can you explain *why* it's a problem?"
  - "You might want to review [concept] before continuing"

- **Query Mechanism**: Betty's Brain lets students quiz their agent—Code Tutor could add:
  - "Test your understanding" mode where the AI asks users questions
  - Self-assessment checkpoints
  - Progressive difficulty based on demonstrated understanding

- **Social Motivation**: Betty's Brain creates social pressure (not wanting Betty to fail)—Code Tutor could frame "Teach Me!" mode more explicitly as teaching a junior developer to enhance this motivation

**Key Insight:** Betty's Brain research shows that combining learning-by-teaching with self-regulated learning feedback is more effective than either alone. Code Tutor's "Teach Me!" mode provides the learning-by-teaching component but could benefit from adding SRL support.

---

### 3. Learning By Teaching: A New Agent Paradigm For Educational Software

**Authors:** Biswas, G., Schwartz, D. L., Leelawong, K., & Vye, N.

**Published:** Applied Artificial Intelligence, 2005, Vol. 19(3-4), pp. 363-392

**Link:** https://www.tandfonline.com/doi/full/10.1080/08839510590910200

#### Abstract

This paper introduces the learning-by-teaching paradigm for educational software, where students learn by teaching a computational agent. The approach reverses the traditional intelligent tutoring system model where the computer teaches the student.

#### Key Findings

- Teaching is one of the most effective ways to learn because it requires:
  - Organization of knowledge
  - Identification of gaps in understanding
  - Active engagement with material
  - Explaining concepts in one's own words

- The learning-by-teaching paradigm creates a "preparation for future learning" (PFL) environment
- Students develop transferable learning skills, not just domain knowledge
- The approach works across different subject domains

#### Relevance to This Project

This foundational paper provides theoretical grounding for Code Tutor's "Teach Me!" feature:

- **Paradigm Shift**: Code Tutor's "Teach Me!" mode embodies this paradigm shift—instead of the AI teaching the user (traditional code review), the user teaches the AI by explaining mistakes
- **Knowledge Organization**: When users must explain what's wrong with code, they organize their programming knowledge, leading to deeper learning
- **Gap Identification**: The process of explaining forces users to confront gaps in their understanding
- **Transfer Skills**: By practicing explanation, users develop skills that transfer to:
  - Code reviews of colleagues' code
  - Technical documentation writing
  - Mentoring junior developers
  - Debugging their own code

**Design Implication:** Code Tutor could emphasize in its documentation that "Teach Me!" mode isn't just about learning programming—it's about developing the skill of explaining and teaching, which is valuable for senior developers and technical leaders.

---

### 4. University of Pennsylvania Cascading Mentoring Program

**Source:** NSF-funded program for computer science education

**Funding:** Three-year, $600,000 grant from the National Science Foundation

#### Program Structure

- Undergraduates teach high school students
- High school students teach middle school students
- Creates a cascade of teaching and learning

#### Relevance to This Project

While not a research paper, this program demonstrates real-world application of learning-by-teaching principles in computer science education:

- **Scalability**: Shows that learning-by-teaching approaches can scale in CS education
- **CS-Specific**: Validates that teaching is an effective learning method specifically for programming
- **Community Building**: Suggests Code Tutor could facilitate peer teaching features in the future
- **Real-World Impact**: NSF funding indicates the approach has demonstrated value in CS education

---

## Summary of Key Themes

1. **Teaching Forces Active Processing**: Preparing to teach or explain requires deeper cognitive engagement than passive learning
2. **Motivation Enhancement**: Responsibility for a "protégé" (whether real or virtual) increases effort and persistence
3. **Metacognitive Benefits**: Teaching makes learners think about their own thinking and identify knowledge gaps
4. **Especially Effective for Struggling Learners**: The protégé effect shows strongest benefits for lower-performing students
5. **Self-Regulated Learning**: Combining teaching with feedback on learning strategies is more effective than either alone
6. **Domain Independence**: The protégé effect works across different subject areas, including programming
7. **Transferable Skills**: Learning-by-teaching develops explanation and communication skills valuable beyond the specific domain

## Implications for Code Tutor Development

### Current Strengths

Code Tutor's "Teach Me!" mode already leverages key principles:
- Users must identify mistakes (not just be shown them)
- Users must explain *what* is wrong
- Users must explain *why* it's a problem
- The AI evaluates depth of understanding
- Multiple rounds allow progressive deepening

### Potential Enhancements

Based on this research, Code Tutor could be enhanced with:

1. **Explicit Protégé Framing**
   - Frame "Teach Me!" as teaching a junior developer or peer
   - Give the "student" a name and persona
   - Make the social relationship more explicit

2. **Self-Regulated Learning Feedback**
   - Provide meta-level feedback on learning strategies
   - Suggest when to review foundational concepts
   - Recognize and reinforce good explanation patterns

3. **Progressive Knowledge Building**
   - Track concepts the user has successfully taught
   - Build on previously taught concepts in subsequent sessions
   - Create a "knowledge map" of what the user has mastered

4. **Query/Assessment Mode**
   - Let users test their understanding by being quizzed
   - Reverse the roles occasionally—AI poses problems, user explains solutions
   - Self-assessment checkpoints

5. **Preparation for Future Learning**
   - Design exercises that prepare users for more advanced concepts
   - Focus on transferable debugging and explanation skills
   - Emphasize learning-to-learn, not just learning content

6. **Social Features** (longer-term)
   - Peer teaching mode where users can challenge each other
   - Community-contributed teaching scenarios
   - Leaderboards or recognition for effective teaching

### Research-Backed Design Principles

From these papers, Code Tutor should:
- ✅ Make users explain, not just identify (already implemented)
- ✅ Require "why" not just "what" (already implemented)
- ✅ Provide iterative refinement (already implemented)
- ⚠️ Frame as teaching someone else (could be more explicit)
- ⚠️ Provide meta-level learning strategy feedback (not yet implemented)
- ⚠️ Build progressive knowledge over sessions (not yet implemented)
- ⚠️ Create sense of responsibility for "protégé" (could be stronger)

## Conclusion

The research on learning-by-teaching provides strong empirical support for Code Tutor's "Teach Me!" mode. The protégé effect is a well-established psychological phenomenon that the system successfully leverages. The Betty's Brain research suggests several concrete ways the feature could be enhanced, particularly by adding self-regulated learning feedback and progressive knowledge building.

Most importantly, this research validates that having programmers *explain* code mistakes (rather than just reviewing correct code) is not only pedagogically sound but is one of the most effective learning strategies available.
