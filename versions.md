Reasoner
 - reasoner-v2 (58%, 185k)
 - reasoner-v2.1
   - added instructions about failed steps and unproductive loops
   - updated examples to better represent goal-based reasoning

Planner
 - planner-v2
 - planner-v2.1
 - planner-v2.2
  - fixed insert ids out of range issue
 - planner-v3.0
 - planner-v3.1
   - reverted back to writing full plan each step
   - reverted back to subgoals but still had action-level examples
 - planner-v3.2
   - added previous agent action to user prompt
   - reverted back to subgoals in both instructions and examples
   - added "NO_CHANGE" feature
 - planner-v3.3
   - inverted back to action-level examples
 - planner-v3.4
   - added 2-level hierarchy of subgoals and actions
   - added mandatory full expansion of all subgoals
 - planner-v3.5
   - Added mandatory expand of the active subgoal and collapse of all other subgoals
 - planner-v3.6
   - added optional expand/collapse of subgoals (I let the agent decide when to expand/collapse)

Summarizer
 - summarizer-v2 (64%, 242k)
   - narrative summary; action in past tense, outcomes in past tense
   - outcomes kept growing longer each step
   - helped plus-summarizer - it recorded recipes which helped cooking tasks
   - hurt top-line performance - became very noisy when combined with other sub-agents
   - Note: there was an bug with k=2-n instead of k=1-n summaries
 - summarizer-v2.1 
   - symbolic; action in present tense, outcome as object=change 
   - (e.g., go north -> location=north)
 - summarizer-v2.2 (52%, 218k)
   - symbolic; tighter constraints on outcomes
 - summarizer-v2.3 (48%, 201k)
   - symbolic; limit of 10 previous summaries 
   - [Improved GPT-5-mini but worse for GPT-5.2]
- summarizer-v2.4 (59%, 233k) 
  - narrative but same constraints as symbolic
 - [NOTE: Use either v2.2 (for symbolic) or v2.4 (for narrative) going forward]

Memorizer
 - memorizer-v2 (56%, 263k)
   - narrative memories; past tense, passive voice 
   - (e.g., "At step 2, there was a carrot on the counter in the kitchen.)
   - added update operation
 - memorizer-v2.1 (57%, 240k)
   - narrative memories, present tense, active voice
   - added more section headers, improved instructions, removed "At step [n], ..."
   - (e.g., "The carrot is on the counter in the kitchen.")
 - memorizer-v2.2 (56%, 286k)
   - symbolic memories 
   - (i.e., "[entity-key]: [property]=[value], ...")
   - (e.g., "carrot: location = {room = kitchen, on = counter}, state = diced)
 - memorizer-v3.0 (56%)
 - memorizer-v3.1 (54%)
   - switched from int IDs to string IDs
