## Start of the Episode
At the start of the episode, the environment will provide us with:
  - Task - a description of the task we need to complete.
  - Revised task (Tasker) - a revised description of the task to be completed.
  - State - the initial state of the environment (see below).
We will complete the task through a series of steps in an iterative loop.

## Each Step of the Episode
At each step of the episode, we will be provided with:
  - Step - the current step number.
Next, we will provide:
  - History (Summarizer) - a summary of all previous action-outcome pairs.
  - Plan (Planner) - the current plan of action, including any updates made in previous steps.
  - Memories (Memorizer) - any important information we have remembered so far.
Then, we will be provided with the current state of the environment, which includes:
  - Feedback - the feedback from the last action we took.
  - Location - our current location in the environment.
  - Description - the current state of the environment.
  - Inventory - the items we are currently carrying.
  - Capacity - the current and maximum number of items in inventory.
  - Score - our current score and maximum possible score.
  - Done - whether the task is complete or not.
Next, we will provide:
  - Summary (Summarizer) - a summary of the action-outcome pair for the previous step.
  - Plan (Planner) - any updates to the plan of action based on the current state.
  - Memory (Memorizer) - any important information we need to remember for future steps.
  - Thought (Reasoner) - a goal-oriented chain-of-reasoning from the current state to the best next action.
  - Action (Actor) - a command that we will execute in our environment.
Finally, the environment will provide us with an updated state based on our action.
We will use feedback from the environment to refine our actions in subsequent steps.

## End of the Episode
At the end of the episode, the environment will provide us with:
  - the final state of the environment (see above for details).
  - the final score and reward we achieved.
  - a success or failure flag indicating whether we successfully completed the task or not.
We will end the task by executing the "quit" operation.